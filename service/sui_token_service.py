# /home/ubuntu/suiboard_project_v3/service/sui_token_service.py
import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import Request

from core.database import db_session
from core.models import Member, SuiTransactionlog # Using SuiTransactionlog model
# from lib.sui_integration import transfer_suiboard_tokens # Placeholder for actual SUI transfer function

class SuiTokenService:
    def __init__(self, request: Request, db: db_session):
        self.request = request
        self.db = db

    @classmethod
    async def async_init(cls, request: Request, db: db_session):
        return cls(request, db)

    async def award_login_tokens(self, member: Member, amount: int = 2) -> bool:
        """
        Awards SUIBOARD tokens to a member upon login, once per day.
        Logs the transaction.
        """
        if not member or not member.mb_id:
            print("SuiTokenService: Invalid member object.")
            return False

        if not member.mb_sui_address:
            print(f"SuiTokenService: Member {member.mb_id} has no SUI address. Cannot award tokens.")
            # Optionally, log this attempt or notify the user to set their SUI address.
            return False

        # Check if tokens were already awarded today for login
        today = datetime.date.today()
        existing_log = self.db.scalar(
            select(SuiTransactionlog).where(
                SuiTransactionlog.mb_id == member.mb_id,
                SuiTransactionlog.stl_reason == "login_bonus",
                func.date(SuiTransactionlog.stl_datetime) == today
            ).limit(1)
        )

        if existing_log:
            print(f"SuiTokenService: Login tokens already awarded to {member.mb_id} today ({today}).")
            return True # Or False if we want to indicate no new tokens were awarded

        # Placeholder for actual SUI token transfer logic
        # In a real implementation, this would call a function that interacts with the SUI blockchain.
        # tx_hash = await transfer_suiboard_tokens(member.mb_sui_address, amount)
        # For now, we simulate a successful transfer and generate a dummy tx_hash.
        print(f"SuiTokenService: Attempting to transfer {amount} SUIBOARD tokens to {member.mb_sui_address} for member {member.mb_id}.")
        simulated_tx_hash = f"simulated_tx_{datetime.datetime.now().isoformat().replace(':', '-')}_{member.mb_id}"
        sui_transfer_successful = True # Assume success for now
        
        if sui_transfer_successful:
            print(f"SuiTokenService: Simulated SUI token transfer successful. TxHash: {simulated_tx_hash}")
            try:
                new_token_log = SuiTransactionlog(
                    mb_id=member.mb_id,
                    wr_id=None,  # No post associated with login bonus
                    bo_table=None,  # No board associated with login bonus
                    stl_amount=amount,
                    stl_reason="login_bonus",
                    stl_tx_hash=simulated_tx_hash,
                    stl_status="success",
                    stl_datetime=datetime.datetime.now(),
                    stl_error_message=None
                )
                self.db.add(new_token_log)
                self.db.commit()
                print(f"SuiTokenService: Logged token award for {member.mb_id}.")
                return True
            except Exception as e:
                self.db.rollback()
                print(f"SuiTokenService: Error logging token award for {member.mb_id}: {e}")
                # Potentially handle SUI transaction rollback/compensation if logging fails critically
                return False
        else:
            print(f"SuiTokenService: SUI token transfer failed for {member.mb_id}.")
            # Log the failure if necessary
            return False

# Note: The SuiTokenLog model needs to be defined in core/models.py
# Example definition for SuiTokenLog:
# class SuiTokenLog(Base):
#     __tablename__ = "g6_sui_token_log"
# 
#     stl_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     mb_id = Column(String(20), ForeignKey(Member.mb_id), nullable=False, index=True)
#     stl_datetime = Column(DateTime, nullable=False, default=datetime.now)
#     stl_reason = Column(String(255), nullable=False, default="") # e.g., "login_bonus", "post_reward", "delete_penalty"
#     stl_amount = Column(Integer, nullable=False, default=0) # Positive for award, negative for deduction
#     stl_tx_hash = Column(String(255), nullable=True) # SUI Transaction Hash
#     stl_ip = Column(String(255), nullable=False, default="")
# 
#     member = relationship("Member")

# Also, sui_integration.transfer_suiboard_tokens function needs to be implemented elsewhere,
# handling the actual blockchain interaction.

