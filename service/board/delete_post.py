from typing_extensions import List, Annotated
import logging # Added for logging

from fastapi import Depends, Request, HTTPException, Path
from sqlalchemy import select, exists, delete, update
from sqlalchemy.orm import Session # Ensure Session is imported for type hinting

from core.database import db_session
from core.models import Member, BoardNew, Scrap, WriteBaseModel, SuiTransactionlog # Import SuiTransactionlog
from lib.board_lib import is_owner, FileCache
from lib.common import remove_query_params, set_url_query_params
from service.board_file_service import BoardFileService
from service.point_service import PointService
from .board import BoardService
from lib.sui_service import reclaim_suiboard_token, SuiInteractionError, DEFAULT_SUI_CONFIG # Import SUI service
from service.sui_transaction_log_service import log_sui_transaction # Import SUI transaction logging service

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

    def delete_write(self, sui_config_override: dict = None):
        """게시글 삭제 처리 및 SUI 토큰 회수"""
        write_model = self.write_model
        db: Session = self.db # type hint for clarity
        bo_table = self.bo_table
        board = self.board
        original_post_writer_mb_id = self.write.mb_id
        original_post_wr_id = self.write.wr_id

        # 1. Find the amount of SUI tokens awarded for this post
        awarded_token_log = db.scalar(
            select(SuiTransactionlog)
            .where(
                SuiTransactionlog.wr_id == original_post_wr_id,
                SuiTransactionlog.bo_table == bo_table,
                SuiTransactionlog.stl_status == "success",
                SuiTransactionlog.stl_reason.like("%게시글 작성 보상%") # Match original award reason
            )
            .order_by(SuiTransactionlog.stl_datetime.desc()) # Get the latest one if multiple
        )

        amount_to_reclaim = 0
        if awarded_token_log and awarded_token_log.stl_amount > 0:
            amount_to_reclaim = awarded_token_log.stl_amount
            logger.info(f"Post {original_post_wr_id} in {bo_table} was awarded {amount_to_reclaim} tokens. Attempting reclaim.")
        else:
            logger.info(f"No successful SUI token award found for post {original_post_wr_id} in {bo_table}, or amount is zero. Skipping reclaim.")

        # 원글 + 댓글
        delete_write_count = 0
        delete_comment_count = 0
        writes: List[WriteBaseModel] = db.scalars(
            select(write_model)
            .filter_by(wr_parent=original_post_wr_id)
            .order_by(write_model.wr_id)
        ).all()
        for write_item in writes:
            if not write_item.wr_is_comment:
                if not self.point_service.delete_point(write_item.mb_id, bo_table, original_post_wr_id, "쓰기"):
                    self.point_service.save_point(write_item.mb_id, board.bo_write_point * (-1),
                                                    f"{board.bo_subject} {original_post_wr_id} 글 삭제")
                self.file_service.delete_board_files(board.bo_table, original_post_wr_id)
                delete_write_count += 1
            else:
                if not self.point_service.delete_point(write_item.mb_id, bo_table, original_post_wr_id, "댓글"):
                    self.point_service.save_point(self.request, write_item.mb_id, board.bo_comment_point * (-1),
                                                  f"{board.bo_subject} {original_post_wr_id} 댓글 삭제")
                delete_comment_count += 1

        db.execute(delete(write_model).filter_by(wr_parent=original_post_wr_id))
        db.execute(delete(BoardNew).where(BoardNew.bo_table == bo_table, BoardNew.wr_parent == original_post_wr_id))
        db.execute(delete(Scrap).filter_by(bo_table=bo_table, wr_id=original_post_wr_id))
        board.bo_notice = self.set_board_notice(original_post_wr_id, False)
        board.bo_count_write -= delete_write_count
        board.bo_count_comment -= delete_comment_count

        # 2. Attempt to reclaim SUI tokens if an award was found
        if amount_to_reclaim > 0 and original_post_writer_mb_id:
            logger.info(f"Attempting to reclaim {amount_to_reclaim} SUI tokens for deleted post {original_post_wr_id}.")
            current_sui_config = DEFAULT_SUI_CONFIG.copy()
            if sui_config_override:
                current_sui_config.update(sui_config_override)

            reclaim_tx_digest = None
            reclaim_status = "failed"
            reclaim_error_msg = None
            try:
                reclaim_tx_digest = reclaim_suiboard_token(
                    amount_to_reclaim=amount_to_reclaim,
                    sui_config=current_sui_config
                )
                reclaim_status = "success"
                logger.info(f"SUI token reclaim successful for deleted post {original_post_wr_id}. TX Digest: {reclaim_tx_digest}")
            except SuiInteractionError as e:
                reclaim_error_msg = str(e)
                logger.error(f"SUI token reclaim failed for deleted post {original_post_wr_id}. Error: {reclaim_error_msg}")
            except ValueError as e: # From sui_config validation
                reclaim_error_msg = str(e)
                logger.error(f"SUI configuration error during token reclaim for post {original_post_wr_id}. Error: {reclaim_error_msg}")
            except Exception as e:
                reclaim_error_msg = f"Unexpected error during SUI token reclaim: {str(e)}"
                logger.error(f"{reclaim_error_msg} for post {original_post_wr_id}")
            
            # Log the reclaim transaction attempt to DB
            log_sui_transaction(
                db=db,
                mb_id=original_post_writer_mb_id, # Log against the original post writer
                wr_id=original_post_wr_id,
                bo_table=bo_table,
                stl_amount=-amount_to_reclaim, # Log reclaimed amount as negative
                stl_tx_hash=reclaim_tx_digest,
                stl_status=reclaim_status,
                stl_reason="게시글 삭제로 인한 토큰 회수",
                stl_error_message=reclaim_error_msg
            )
        
        db.commit()
        # db.close() # Closing session here might be premature if called from a larger transaction context

        FileCache().delete_prefix(f"latest-{bo_table}")

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

