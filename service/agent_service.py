# /home/ubuntu/suiboard_project_v3/service/agent_service.py
import datetime
import logging # Added for logging SUI interactions
from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import Member, Board, Config, Point # Assuming Config might hold SUI settings
from lib.board_lib import insert_board_new, get_next_num, generate_reply_character
from lib.common import dynamic_create_write_table

from lib.common import get_client_ip # For wr_ip, might need a mock or fixed IP for agent
from lib.sui_service import award_suiboard_token, SuiInteractionError # Import SUI service
# Import the SUI transaction logging service
from service.sui_transaction_log_service import log_sui_transaction

# Configure logger for this module
logger = logging.getLogger(__name__)

# Placeholder for SUI configuration - THIS SHOULD BE LOADED FROM A SECURE CONFIG FILE OR ENV VARS
# Example: These would be specific to your SUI deployment (Testnet/Mainnet)
DEFAULT_SUI_CONFIG = {
    "network": "testnet", # or "mainnet", "devnet"
    "package_id": "0x7ded54267def06202efa3e9ffb8df024d03b43f9741a9348332eee2ed63ef165", # Replace with actual Package ID
    "treasury_cap_id": "0x3fe97fd206b14a8fc560aeb926eebc36afd68687fbece8df50f8de1012b28e59", # Replace with actual Treasury Cap ID
    "gas_budget": 100000000, # Adjust as needed
    "sui_bin_path": "/home/linuxbrew/.linuxbrew/bin/sui" # Default path, ensure it's correct
}
TOKEN_AWARD_AMOUNT_POST_CREATION = 200 # Example: 200 smallest units (2.00 tokens with 2 decimals)

def create_post_by_agent(
    db: Session,
    bo_table: str,
    mb_id: str, # Agent's member ID
    wr_subject: str,
    wr_content: str,
    wr_name: str = None, # If None, will use member's nick
    wr_password: str = None, # For non-member posts, or if needed
    wr_email: str = None, # If None, will use member's email
    wr_homepage: str = None, # If None, will use member's homepage
    wr_option: str = "", # Example: "html1,secret"
    wr_link1: str = "",
    wr_link2: str = "",
    ca_name: str = None, # Category
    wr_ip: str = "0.0.0.0", # Agent's IP or a placeholder
    sui_config_override: dict = None # Allow overriding default SUI config for flexibility
):
    """
    Creates a post as if an agent (specified by mb_id) wrote it.
    This function replicates the core logic of CreatePostService for agent-based posting
    and includes SUI token awarding and transaction logging.
    """
    board = db.query(Board).filter(Board.bo_table == bo_table).first()
    if not board:
        logger.error(f"Board {bo_table} not found for agent posting.")
        raise ValueError(f"Board {bo_table} not found.")

    member = db.query(Member).filter(Member.mb_id == mb_id).first()
    if not member:
        logger.error(f"Agent member {mb_id} not found for agent posting.")
        raise ValueError(f"Agent member {mb_id} not found.")

    if not wr_name:
        wr_name = member.mb_nick
    if not wr_email:
        wr_email = member.mb_email
    if not wr_homepage:
        wr_homepage = member.mb_homepage
    
    hashed_password = ""

    # Create dynamic write table model for the target board
    WriteModel = dynamic_create_write_table(bo_table, create_table=True)
    write = WriteModel()
    write.wr_num = get_next_num(board.bo_table)
    write.wr_reply = ""
    write.wr_parent = 0 
    write.wr_is_comment = 0
    write.wr_comment = 0
    write.wr_comment_reply = ""
    write.ca_name = ca_name
    write.wr_option = wr_option
    write.wr_subject = wr_subject
    write.wr_content = wr_content
    write.wr_link1 = wr_link1
    write.wr_link2 = wr_link2
    write.wr_link1_hit = 0
    write.wr_link2_hit = 0
    write.wr_hit = 0
    write.wr_good = 0
    write.wr_nogood = 0
    write.mb_id = member.mb_id
    write.wr_password = hashed_password 
    write.wr_name = wr_name
    write.wr_email = wr_email
    write.wr_homepage = wr_homepage
    write.wr_datetime = datetime.datetime.now()
    write.wr_last = datetime.datetime.now()
    write.wr_ip = wr_ip
    write.wr_facebook_user = ""
    write.wr_twitter_user = ""

    db.add(write)
    db.flush() 

    write.wr_parent = write.wr_id 
    db.commit()
    logger.info(f"Agent {mb_id} created post {write.wr_id} in board {bo_table}.")

    insert_board_new(board.bo_table, write)
    db.commit() 

    if member.mb_id and board.bo_write_point:
        point_content = f"{board.bo_subject} {write.wr_id} 글쓰기 (에이전트)"
        # 직접 포인트 데이터베이스에 저장 (agent 전용)
        
        # 회원의 현재 포인트 계산
        current_points = db.query(func.sum(Point.po_point)).filter(Point.mb_id == member.mb_id).scalar() or 0
        new_total_points = current_points + board.bo_write_point
        
        # 포인트 내역 추가
        new_point = Point(
            mb_id=member.mb_id,
            po_content=point_content,
            po_point=board.bo_write_point,
            po_use_point=0,
            po_mb_point=new_total_points,
            po_expired=0,
            po_expire_date=datetime.datetime(9999, 12, 31),  # 만료되지 않는 포인트
            po_rel_table=board.bo_table,
            po_rel_id=str(write.wr_id),
            po_rel_action="쓰기"
        )
        db.add(new_point)
        
        # 회원 포인트 업데이트
        member.mb_point = new_total_points
        db.commit()
        logger.info(f"Points ({board.bo_write_point}) awarded to {member.mb_id} for post {write.wr_id}.")

        if member.mb_sui_address:
            logger.info(f"Member {member.mb_id} has SUI address: {member.mb_sui_address}. Attempting token award.")
            current_sui_config = DEFAULT_SUI_CONFIG.copy()
            if sui_config_override:
                current_sui_config.update(sui_config_override)
            
            if current_sui_config["package_id"] == "0xYOUR_PACKAGE_ID" or \
               current_sui_config["treasury_cap_id"] == "0xYOUR_TREASURY_CAP_ID":
                logger.warning("SUI Package ID or Treasury CAP ID is still a placeholder. Token award will likely fail.")

            tx_digest_val = None
            tx_status = "failed"
            error_msg = None
            try:
                tx_digest_val = award_suiboard_token(
                    recipient_address=member.mb_sui_address,
                    amount=TOKEN_AWARD_AMOUNT_POST_CREATION, 
                    sui_config=current_sui_config
                )
                tx_status = "success"
                logger.info(f"SUI token award successful for post {write.wr_id}. User: {member.mb_id}, TX Digest: {tx_digest_val}")
            except SuiInteractionError as e:
                error_msg = str(e)
                logger.error(f"SUI token award failed for post {write.wr_id}. User: {member.mb_id}, Error: {error_msg}")
            except ValueError as e: # From sui_config validation
                error_msg = str(e)
                logger.error(f"SUI configuration error during token award for post {write.wr_id}. User: {member.mb_id}, Error: {error_msg}")
            except Exception as e: # Catch any other unexpected errors
                error_msg = f"Unexpected error during SUI token award: {str(e)}"
                logger.error(f"{error_msg} for post {write.wr_id}, user {member.mb_id}")
            
            # Log the transaction attempt to DB
            log_sui_transaction(
                db=db,
                mb_id=member.mb_id,
                wr_id=write.wr_id,
                bo_table=board.bo_table,
                stl_amount=TOKEN_AWARD_AMOUNT_POST_CREATION,
                stl_tx_hash=tx_digest_val,
                stl_status=tx_status,
                stl_reason="게시글 작성 보상 (에이전트)",
                stl_error_message=error_msg
            )
        else:
            logger.info(f"Member {member.mb_id} does not have an SUI address. Skipping token award for post {write.wr_id}.")

    return write

