from typing_extensions import List, Annotated
import logging # Added for logging

from fastapi import Depends, Request, HTTPException, Path
from sqlalchemy import select, exists, delete, update, and_
from sqlalchemy.orm import Session # Ensure Session is imported for type hinting

from core.database import db_session
from core.models import Member, BoardNew, Scrap, WriteBaseModel, SuiTransactionlog, TokenSupply # Import SuiTransactionlog and TokenSupply
from lib.board_lib import is_owner, FileCache
from lib.common import remove_query_params, set_url_query_params
from service.board_file_service import BoardFileService
from service.point_service import PointService
from .board import BoardService
from lib.sui_service import reclaim_suiboard_token, SuiInteractionError, DEFAULT_SUI_CONFIG # Import SUI service
from service.sui_transaction_log_service import log_sui_transaction # Import SUI transaction logging service
from lib.walrus_service import retrieve_post_from_walrus, WalrusError, DEFAULT_WALRUS_CONFIG # Import Walrus service

logger = logging.getLogger(__name__) # Setup logger

class DeletePostService(BoardService):
    """
    게시글 삭제 처리 클래스
    """

    def __init__(
        self,
        request: Request,
        db: db_session,
        file_service: Annotated[BoardFileService, Depends()],
        point_service: Annotated[PointService, Depends()],
        bo_table: Annotated[str, Path(...)],
        wr_id: Annotated[int, Path(...)],
    ):
        super().__init__(request, db, bo_table)
        self.wr_id = wr_id
        self.write = self.get_write(wr_id)
        self.write_member_mb_no = self.db.scalar(select(Member.mb_no).where(Member.mb_id == self.write.mb_id))
        self.write_member = self.db.get(Member, self.write_member_mb_no)
        self.write_member_level = getattr(self.write_member, "mb_level", 1)
        self.file_service = file_service
        self.point_service = point_service

    @classmethod
    async def async_init(
        cls,
        request: Request,
        db: db_session,
        file_service: Annotated[BoardFileService, Depends()],
        point_service: Annotated[PointService, Depends()],
        bo_table: Annotated[str, Path(...)],
        wr_id: Annotated[int, Path(...)],
    ):
        instance = cls(request, db, file_service, point_service, bo_table, wr_id)
        return instance

    def validate_level(self, with_session: bool = True):
        """권한 검증"""
        if self.member.admin_type == "super":
            return

        if self.member.admin_type and self.write_member_level > self.member.level:
            self.raise_exception(status_code=403, detail="자신보다 높은 권한의 게시글은 삭제할 수 없습니다.")
        elif self.write.mb_id and not is_owner(self.write, self.member.mb_id):
            self.raise_exception(status_code=403, detail="자신의 게시글만 삭제할 수 있습니다.", )

        if not self.write.mb_id:
            if with_session and not self.request.session.get(f"ss_delete_{self.bo_table}_{self.wr_id}"):
                url = f"/bbs/password/delete/{self.bo_table}/{self.wr_id}"
                query_params = remove_query_params(self.request, "token")
                self.raise_exception(status_code=403, detail="비회원 글을 삭제할 권한이 없습니다.", url=set_url_query_params(url, query_params))
            elif not with_session:
                self.raise_exception(status_code=403, detail="비회원 글을 삭제할 권한이 없습니다.")
        
    def validate_exists_reply(self):
        """답변글이 있을 때 삭제 불가"""
        exists_reply = self.db.scalar(
            exists(self.write_model)
            .where(
                self.write_model.wr_reply.like(f"{self.write.wr_reply}%"),
                self.write_model.wr_num == self.write.wr_num,
                self.write_model.wr_is_comment == 0,
                self.write_model.wr_id != self.wr_id
            )
            .select()
        )
        if exists_reply:
            self.raise_exception(detail="답변이 있는 글은 삭제할 수 없습니다. 우선 답변글부터 삭제하여 주십시오.", status_code=403)

    def validate_exists_comment(self):
         """게시판 설정에서 정해놓은 댓글 개수 이상일 때 삭제 불가"""
         if not self.is_delete_by_comment(self.wr_id):
            self.raise_exception(detail=f"이 글과 관련된 댓글이 {self.board.bo_count_delete}건 이상 존재하므로 삭제 할 수 없습니다.", status_code=403)

    def delete_post(self, write_id: int):
        """게시글 삭제 및 SUIBOARD 토큰 회수"""
        write = self.get_write(write_id)
        
        # SUIBOARD 토큰 회수 (에이전트가 아닌 경우만)
        if not write.mb_id.startswith('gg_'):
            try:
                # 게시글 작성 보상으로 지급된 토큰 회수
                token_amount = 1  # 게시글 작성 시 지급된 토큰 양
                
                # 실제 SUIBOARD 토큰 회수 (소각)
                tx_hash = reclaim_suiboard_token(
                    amount_to_reclaim=token_amount,
                    sui_config=DEFAULT_SUI_CONFIG
                )
                
                # 소각량 추적 업데이트
                from core.database import get_db
                from datetime import datetime
                
                db = next(get_db())
                try:
                    supply_record = db.query(TokenSupply).first()
                    if supply_record:
                        supply_record.total_burned += token_amount
                        supply_record.last_updated = datetime.now()
                        supply_record.notes = f"Burned {token_amount} tokens from deleted post {write_id}"
                        db.commit()
                        logger.info(f"토큰 소각량 추적 업데이트: +{token_amount}, 총 소각량: {supply_record.total_burned}")
                    else:
                        logger.warning("TokenSupply 레코드가 없어 소각량 추적 불가")
                finally:
                    db.close()
                
                # 트랜잭션 로그 저장
                from core.models import SuiTransactionlog
                sui_log = SuiTransactionlog(
                    mb_id=write.mb_id,
                    wr_id=write.wr_id,
                    bo_table=self.bo_table,
                    stl_amount=-token_amount,  # 음수로 회수 표시
                    stl_reason="post_deletion", 
                    stl_tx_hash=tx_hash,
                    stl_status="success",
                    stl_datetime=datetime.now(),
                    stl_error_message=None
                )
                self.db.add(sui_log)
                logger.info(f"SUIBOARD 토큰 {token_amount} 회수 완료: {write.mb_id}, 게시글 {write.wr_id}, TX: {tx_hash}")
                
            except Exception as e:
                logger.error(f"SUIBOARD 토큰 회수 실패: {write.mb_id}, 게시글 {write.wr_id}, 오류: {str(e)}")
                # 실패 로그 저장
                from core.models import SuiTransactionlog
                sui_log = SuiTransactionlog(
                    mb_id=write.mb_id,
                    wr_id=write.wr_id,
                    bo_table=self.bo_table,
                    stl_amount=-1,
                    stl_reason="post_deletion",
                    stl_tx_hash=None,
                    stl_status="failed",
                    stl_datetime=datetime.now(),
                    stl_error_message=str(e)
                )
                self.db.add(sui_log)

        # Walrus에서 게시글 처리 (삭제는 불가능하므로 로그만 기록)
        self._handle_walrus_deletion(write)
        
        # 댓글이 있는 경우 댓글들도 모두 삭제
        comments = self.db.scalars(
            select(self.write_model).where(
                and_(
                    self.write_model.wr_parent == write.wr_parent,
                    self.write_model.wr_is_comment == 1
                )
            )
        ).all()
        
        for comment in comments:
            self.delete_comment(comment)
        
        # 게시글 삭제
        self.db.delete(write)
        self.board.bo_count_write = self.board.bo_count_write - 1
        self.db.commit()

    def _handle_walrus_deletion(self, write_item):
        """Walrus에서 게시글 처리 (삭제 기록)"""
        try:
            if write_item.wr_link2 and write_item.wr_link2.startswith('walrus:'):
                blob_id = write_item.wr_link2.replace('walrus:', '')
                
                # Walrus에서 게시글 정보 조회하여 삭제 상태 확인
                # 참고: Walrus는 불변 스토리지이므로 실제 삭제는 불가능
                # 여기서는 삭제 상태만 로그로 기록
                post_data = retrieve_post_from_walrus(blob_id, DEFAULT_WALRUS_CONFIG)
                
                if post_data:
                    logger.info(f"게시글 {write_item.wr_id}가 Walrus에서 확인됨 (blob_id: {blob_id}). "
                              f"Walrus는 불변 스토리지이므로 데이터는 그대로 유지됨.")
                else:
                    logger.warning(f"게시글 {write_item.wr_id}의 Walrus 데이터를 찾을 수 없음 (blob_id: {blob_id})")
                    
        except WalrusError as e:
            logger.error(f"게시글 {write_item.wr_id}의 Walrus 처리 중 오류: {str(e)}")
        except Exception as e:
            logger.error(f"게시글 {write_item.wr_id}의 Walrus 처리 중 예상치 못한 오류: {str(e)}")

# ... (rest of the file: DeleteCommentService, ListDeleteService remains the same) ...

class DeleteCommentService(DeletePostService):
    """댓글 삭제 처리 클래스"""

    def __init__(
        self,
        request: Request,
        db: db_session,
        file_service: Annotated[BoardFileService, Depends()],
        point_service: Annotated[PointService, Depends()],
        bo_table: Annotated[str, Path(...)],
        comment_id: Annotated[str, Path(...)],
    ):
        # Note: We are calling the parent constructor with comment_id as wr_id
        super().__init__(request, db, file_service, point_service, bo_table, int(comment_id) if comment_id.isdigit() else 0 )
        self.wr_id = int(comment_id) if comment_id.isdigit() else 0 # Ensure wr_id is int for comment
        self.comment = self.get_comment()

    @classmethod
    async def async_init(
        cls,
        request: Request,
        db: db_session,
        file_service: Annotated[BoardFileService, Depends()],
        point_service: Annotated[PointService, Depends()],
        bo_table: Annotated[str, Path(...)],
        comment_id: Annotated[str, Path(...)],
    ):
        instance = cls(request, db, file_service, point_service, bo_table, comment_id)
        return instance

    def get_comment(self) -> WriteBaseModel:
        comment: WriteBaseModel = self.db.get(self.write_model, self.wr_id)
        if not comment:
            raise HTTPException(status_code=404, detail=f"{self.wr_id} : 존재하지 않는 댓글입니다.")

        if not comment.wr_is_comment:
            raise HTTPException(status_code=400, detail=f"{self.wr_id} : 댓글이 아닌 게시글입니다.")

        return comment

    def check_authority(self, with_session: bool = True):
        """
        게시글 삭제 권한 검증
        - Template 용으로 사용하는 경우 with_session 인자는 True 값으로 하며
          익명 댓글일 경우 session을 통해 권한을 검증합니다.
        - API 용으로 사용하는 경우 with_session 인자는 False 값으로 사용합니다.
        """
        if self.member.admin_type:
            return

        if not self.comment.mb_id:
            if not with_session:
                self.raise_exception(detail="삭제할 권한이 없습니다.", status_code=403)
            session_name = f"ss_delete_comment_{self.bo_table}_{self.wr_id}"
            if self.request.session.get(session_name):
                return
            url = f"/bbs/password/comment-delete/{self.bo_table}/{self.wr_id}"
            query_params = remove_query_params(self.request, "token")
            self.raise_exception(detail="삭제할 권한이 없습니다.", status_code=403, url=set_url_query_params(url, query_params))

        if not is_owner(self.comment, self.member.mb_id):
            self.raise_exception(detail="자신의 댓글만 삭제할 수 있습니다.", status_code=403)

    def delete_comment(self):
        """댓글 삭제 처리"""
        write_model= self.write_model
        db = self.db

        # 댓글 포인트 회수 (SUI 토큰 회수는 댓글에 대해선 현재 미구현)
        if self.comment.mb_id and self.board.bo_comment_point:
            if not self.point_service.delete_point(self.comment.mb_id, self.bo_table, self.comment.wr_id, "댓글"):
                self.point_service.save_point(self.request, self.comment.mb_id, self.board.bo_comment_point * (-1),
                                                f"{self.board.bo_subject} {self.comment.wr_id} 댓글 삭제")

        db.delete(self.comment)
        db.execute(
            update(write_model).values(wr_comment=write_model.wr_comment - 1)
            .where(write_model.wr_id == self.comment.wr_parent)
        )
        db.commit()

class ListDeleteService(BoardService):
    """
    여러 게시글을 한번에 삭제하기 위한 클래스
    """
    def __init__(
        self,
        request: Request,
        db: db_session,
        file_service: Annotated[BoardFileService, Depends()],
        point_service: Annotated[PointService, Depends()],
        bo_table: Annotated[str, Path(...)],
    ):
        super().__init__(request, db, bo_table)
        self.file_service = file_service
        self.point_service = point_service

    @classmethod
    async def async_init(
        cls,
        request: Request,
        db: db_session,
        file_service: Annotated[BoardFileService, Depends()],
        point_service: Annotated[PointService, Depends()],
        bo_table: Annotated[str, Path(...)],
    ):
        instance = cls(request, db, file_service, point_service, bo_table)
        return instance

    def delete_writes(self, wr_ids: list, sui_config_override: dict = None):
        """게시글 목록 삭제 및 SUI 토큰 회수"""
        write_model = self.write_model
        db: Session = self.db

        for wr_id_to_delete in wr_ids:
            write_to_delete = db.get(write_model, wr_id_to_delete)
            if not write_to_delete:
                logger.warning(f"Attempted to delete non-existent write ID: {wr_id_to_delete} in bo_table: {self.bo_table}")
                continue
            
            original_writer_mb_id = write_to_delete.mb_id

            # 1. Find awarded tokens for this specific post
            awarded_token_log_list_delete = db.scalar(
                select(SuiTransactionlog)
                .where(
                    SuiTransactionlog.wr_id == wr_id_to_delete,
                    SuiTransactionlog.bo_table == self.bo_table,
                    SuiTransactionlog.stl_status == "success",
                    SuiTransactionlog.stl_reason.like("%게시글 작성 보상%")
                )
                .order_by(SuiTransactionlog.stl_datetime.desc())
            )
            amount_to_reclaim_list_delete = 0
            if awarded_token_log_list_delete and awarded_token_log_list_delete.stl_amount > 0:
                amount_to_reclaim_list_delete = awarded_token_log_list_delete.stl_amount
            
            # Delete comments associated with this post first (simplified, actual comment deletion might be more complex)
            # This part might need more robust handling if comments also award points/tokens that need reclaiming
            db.execute(delete(write_model).where(write_model.wr_parent == wr_id_to_delete, write_model.wr_is_comment == 1))

            # Delete the post itself
            db.delete(write_to_delete)
            if not self.point_service.delete_point(original_writer_mb_id, self.bo_table, wr_id_to_delete, "쓰기"):
                self.point_service.save_point(original_writer_mb_id, self.board.bo_write_point * (-1),
                                              f"{self.board.bo_subject} {wr_id_to_delete} 글 삭제")
            self.file_service.delete_board_files(self.board.bo_table, wr_id_to_delete)
            
            # Update board counts (simplified for list delete)
            self.board.bo_count_write -= 1 # Decrement for each main post deleted
            # Comment count update would be more complex here, assuming comments are deleted above

            # Reclaim SUI tokens
            if amount_to_reclaim_list_delete > 0 and original_writer_mb_id:
                logger.info(f"Attempting to reclaim {amount_to_reclaim_list_delete} SUI tokens for list-deleted post {wr_id_to_delete}.")
                current_sui_config_list = DEFAULT_SUI_CONFIG.copy()
                if sui_config_override:
                    current_sui_config_list.update(sui_config_override)
                
                reclaim_tx_digest_list = None
                reclaim_status_list = "failed"
                reclaim_error_msg_list = None
                try:
                    reclaim_tx_digest_list = reclaim_suiboard_token(
                        amount_to_reclaim=amount_to_reclaim_list_delete,
                        sui_config=current_sui_config_list
                    )
                    reclaim_status_list = "success"
                except SuiInteractionError as e:
                    reclaim_error_msg_list = str(e)
                except Exception as e:
                    reclaim_error_msg_list = f"Unexpected SUI error: {str(e)}"
                
                log_sui_transaction(
                    db=db,
                    mb_id=original_writer_mb_id,
                    wr_id=wr_id_to_delete,
                    bo_table=self.bo_table,
                    stl_amount=-amount_to_reclaim_list_delete,
                    stl_tx_hash=reclaim_tx_digest_list,
                    stl_status=reclaim_status_list,
                    stl_reason="목록 삭제로 인한 토큰 회수",
                    stl_error_message=reclaim_error_msg_list
                )

            # Remove from BoardNew and Scrap
            db.execute(delete(BoardNew).where(BoardNew.bo_table == self.bo_table, BoardNew.wr_id == wr_id_to_delete))
            db.execute(delete(Scrap).where(Scrap.bo_table == self.bo_table, Scrap.wr_id == wr_id_to_delete))

        db.commit()
        FileCache().delete_prefix(f"latest-{self.bo_table}")

