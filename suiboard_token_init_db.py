"""
SUIBOARD 데이터베이스 초기화 스크립트
- TokenSupply 테이블 생성
- 초기 설정값 입력
"""

from core.database import get_db, DBConnect
from core.models import Base, TokenSupply
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """데이터베이스 테이블 생성 및 초기 데이터 설정"""
    
    try:
        # 데이터베이스 연결 및 engine 가져오기
        db_connect = DBConnect()
        engine = db_connect.engine
        
        # 모든 테이블 생성
        logger.info("데이터베이스 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
        
        # 데이터베이스 세션 시작
        db = db_connect.sessionLocal()
        
        # TokenSupply 초기 데이터 확인/생성
        existing_supply = db.query(TokenSupply).first()
        
        if not existing_supply:
            logger.info("TokenSupply 초기 데이터 생성 중...")
            initial_supply = TokenSupply(
                total_minted=0,
                total_burned=0,
                max_supply=100000000,  # 1억개 제한
                last_updated=datetime.now(),
                notes="Database initialized - no tokens minted yet"
            )
            db.add(initial_supply)
            db.commit()
            logger.info("TokenSupply 초기 데이터 생성 완료")
            logger.info(f"설정된 최대 발행량: {initial_supply.max_supply:,} SUIBOARD 토큰")
        else:
            logger.info("TokenSupply 데이터가 이미 존재합니다")
            logger.info(f"현재 발행량: {existing_supply.total_minted:,}/{existing_supply.max_supply:,}")
            logger.info(f"남은 발행 가능량: {existing_supply.remaining_supply:,}")
        
        db.close()
        logger.info("데이터베이스 초기화 완료!")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {str(e)}")
        raise

if __name__ == "__main__":
    init_database() 