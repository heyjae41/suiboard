# /home/ubuntu/suiboard_project_v3/service/sui_transaction_log_service.py
import datetime
import logging
from sqlalchemy.orm import Session
from core.models import SuiTransactionlog, Member # Assuming Member might be needed for context, though mb_id is passed

logger = logging.getLogger(__name__)

def log_sui_transaction(
    db: Session,
    mb_id: str,
    stl_amount: int,
    stl_status: str, # "success" or "failed"
    wr_id: int = None, # Optional: ID of the related write/post
    bo_table: str = None, # Optional: Board table of the related write/post
    stl_tx_hash: str = None, # SUI Transaction Hash, None if failed before submission
    stl_reason: str = None, # Reason for the transaction
    stl_error_message: str = None # Error message if status is "failed"
):
    """
    Logs a SUI token transaction to the SuiTransactionlog table.

    Args:
        db: SQLAlchemy Session.
        mb_id: Member ID of the user involved.
        stl_amount: Amount of tokens transacted (in smallest unit).
        stl_status: Status of the transaction ("success" or "failed").
        wr_id: (Optional) ID of the related write/post.
        bo_table: (Optional) Board table of the related write/post.
        stl_tx_hash: (Optional) SUI Transaction Hash.
        stl_reason: (Optional) Reason for the transaction.
        stl_error_message: (Optional) Error message if the transaction failed.
    """
    try:
        # 중복 트랜잭션 해시 체크 (해시가 있는 경우만)
        if stl_tx_hash:
            from sqlalchemy import select
            existing_log = db.scalar(
                select(SuiTransactionlog).where(SuiTransactionlog.stl_tx_hash == stl_tx_hash)
            )
            if existing_log:
                logger.warning(f"Duplicate transaction hash found, skipping log: {stl_tx_hash}")
                return
        
        log_entry = SuiTransactionlog(
            mb_id=mb_id,
            wr_id=wr_id,
            bo_table=bo_table,
            stl_amount=stl_amount,
            stl_tx_hash=stl_tx_hash,
            stl_status=stl_status,
            stl_reason=stl_reason,
            stl_datetime=datetime.datetime.now(),
            stl_error_message=stl_error_message
        )
        db.add(log_entry)
        db.commit()
        logger.info(f"SUI transaction logged for mb_id {mb_id}, wr_id {wr_id}, status {stl_status}, tx_hash {stl_tx_hash}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to log SUI transaction for mb_id {mb_id}, wr_id {wr_id}. Error: {e}")
        # Depending on policy, this might raise the exception further or just log it.
        # For now, just logging to prevent cascading failures if logging itself fails.

