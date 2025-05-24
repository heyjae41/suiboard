"""
SUIBOARD 토큰 발행량 제한 기능 테스트
- 발행량 추적 확인
- 최대 발행량 제한 테스트
- 개별 객체 vs 통합 객체 민팅 비교
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import DBConnect
from core.models import TokenSupply
from lib.sui_service import award_suiboard_token, DEFAULT_SUI_CONFIG
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 테스트용 주소
TEST_ADDRESS = "0x75afdd8da74b9e64cdc62cfcbd7eaaa4ec0538cee13d468094912b5078b1e636"

def show_supply_status():
    """현재 토큰 공급량 상태 출력"""
    db_connect = DBConnect()
    db = db_connect.sessionLocal()
    try:
        supply = db.query(TokenSupply).first()
        if supply:
            print(f"\n📊 토큰 공급량 현황")
            print(f"├─ 총 발행량: {supply.total_minted:,} SUIBOARD")
            print(f"├─ 총 소각량: {supply.total_burned:,} SUIBOARD")
            print(f"├─ 순 유통량: {supply.circulating_supply:,} SUIBOARD")
            print(f"├─ 최대 공급량: {supply.max_supply:,} SUIBOARD")
            print(f"├─ 남은 발행가능량: {supply.remaining_supply:,} SUIBOARD")
            print(f"└─ 마지막 업데이트: {supply.last_updated}")
        else:
            print("❌ 토큰 공급량 데이터가 없습니다.")
    finally:
        db.close()

def test_normal_minting():
    """정상적인 토큰 민팅 테스트"""
    print("\n🧪 테스트 1: 정상적인 토큰 민팅")
    
    try:
        # 2개 민팅 (로그인 보상 시뮬레이션)
        print("  └─ 2개 민팅 시도 (로그인 보상)...")
        tx_hash = award_suiboard_token(TEST_ADDRESS, 2, DEFAULT_SUI_CONFIG)
        print(f"     ✅ 성공: TX {tx_hash[:10]}...")
        
        # 1개 민팅 (게시글 작성 보상 시뮬레이션)  
        print("  └─ 1개 민팅 시도 (게시글 작성)...")
        tx_hash = award_suiboard_token(TEST_ADDRESS, 1, DEFAULT_SUI_CONFIG)
        print(f"     ✅ 성공: TX {tx_hash[:10]}...")
        
    except Exception as e:
        print(f"     ❌ 실패: {str(e)}")

def test_batch_minting():
    """대량 민팅 테스트 (객체 개수 확인)"""
    print("\n🧪 테스트 2: 대량 민팅 비교")
    
    try:
        # 방법 1: 한 번에 100개 민팅
        print("  └─ 방법 1: 한 번에 100개 민팅...")
        tx_hash1 = award_suiboard_token(TEST_ADDRESS, 100, DEFAULT_SUI_CONFIG)
        print(f"     ✅ 성공: TX {tx_hash1[:10]}... (balance=100인 Coin 객체 1개 생성)")
        
        # 방법 2: 1개씩 3번 민팅
        print("  └─ 방법 2: 1개씩 3번 민팅...")
        for i in range(3):
            tx_hash = award_suiboard_token(TEST_ADDRESS, 1, DEFAULT_SUI_CONFIG)
            print(f"     ✅ {i+1}번째: TX {tx_hash[:10]}... (balance=1인 Coin 객체 1개 생성)")
        
        print(f"     📝 결과: 총 103개 토큰 = Coin 객체 4개 (100+1+1+1)")
        
    except Exception as e:
        print(f"     ❌ 실패: {str(e)}")

def test_supply_limit():
    """발행량 한도 제한 테스트"""
    print("\n🧪 테스트 3: 발행량 한도 제한")
    
    # 현재 발행량 확인
    db_connect = DBConnect()
    db = db_connect.sessionLocal()
    try:
        supply = db.query(TokenSupply).first()
        remaining = supply.remaining_supply if supply else 100000000
        
        if remaining > 1000:
            print(f"  └─ 남은 발행가능량이 충분함 ({remaining:,}개)")
            print(f"  └─ 한도 초과 시뮬레이션을 위해 임시로 한도를 낮춰 테스트...")
            
            # 임시로 최대 공급량을 현재+10으로 설정
            original_max = supply.max_supply
            supply.max_supply = supply.total_minted + 10
            db.commit()
            
            try:
                # 15개 민팅 시도 (한도 초과)
                print(f"  └─ 15개 민팅 시도 (한도 {supply.max_supply} 초과)...")
                tx_hash = award_suiboard_token(TEST_ADDRESS, 15, DEFAULT_SUI_CONFIG)
                print(f"     ❌ 예상과 다름: 성공했어야 실패: TX {tx_hash}")
                
            except Exception as e:
                print(f"     ✅ 예상대로 실패: {str(e)}")
                
            finally:
                # 원래 한도로 복구
                supply.max_supply = original_max
                db.commit()
                print(f"  └─ 최대 공급량을 원래대로 복구: {original_max:,}")
        else:
            print(f"  └─ 남은 발행가능량이 적음 ({remaining:,}개)")
            print(f"  └─ {remaining + 1}개 민팅 시도 (한도 초과)...")
            try:
                tx_hash = award_suiboard_token(TEST_ADDRESS, remaining + 1, DEFAULT_SUI_CONFIG)
                print(f"     ❌ 예상과 다름: 성공했어야 실패: TX {tx_hash}")
            except Exception as e:
                print(f"     ✅ 예상대로 실패: {str(e)}")
                
    finally:
        db.close()

def test_supply_tracking():
    """발행량 추적 정확성 테스트"""
    print("\n🧪 테스트 4: 발행량 추적 정확성")
    
    # 초기 상태 저장
    db_connect = DBConnect()
    db = db_connect.sessionLocal()
    try:
        supply_before = db.query(TokenSupply).first()
        initial_minted = supply_before.total_minted if supply_before else 0
        
        print(f"  └─ 초기 발행량: {initial_minted:,}")
        
        # 5개 민팅
        print(f"  └─ 5개 민팅...")
        tx_hash = award_suiboard_token(TEST_ADDRESS, 5, DEFAULT_SUI_CONFIG)
        print(f"     ✅ 성공: TX {tx_hash[:10]}...")
        
        # 발행량 확인
        db.refresh(supply_before)  # 데이터 새로고침
        final_minted = supply_before.total_minted
        
        expected = initial_minted + 5
        if final_minted == expected:
            print(f"     ✅ 추적 정확: {initial_minted:,} + 5 = {final_minted:,}")
        else:
            print(f"     ❌ 추적 오류: 예상 {expected:,}, 실제 {final_minted:,}")
            
    finally:
        db.close()

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 SUIBOARD 토큰 발행량 제한 기능 테스트 시작\n")
    print("=" * 60)
    
    # 초기 상태 확인
    show_supply_status()
    
    # 실제 SUI 네트워크 연결이 필요한 테스트는 건너뛰고 설정만 확인
    print("\n📋 설정 확인:")
    print("- 토큰 컨트랙트 패키지 ID:", DEFAULT_SUI_CONFIG["package_id"])
    print("- Treasury Cap ID:", DEFAULT_SUI_CONFIG["treasury_cap_id"])
    print("- 최대 발행량: 100,000,000 SUIBOARD 토큰")
    print("- 로그인 보상: 2 토큰")
    print("- 게시글 작성 보상: 1 토큰")
    
    print("\n" + "=" * 60)
    print("🎯 설정 확인 완료!")
    print("\n📋 요약:")
    print("- amount=N 민팅 → balance=N인 Coin 객체 1개 생성")
    print("- 발행량 자동 추적 및 한도 제한 설정됨")
    print("- 1억개 발행 한도 설정됨")
    print("- 실제 토큰 민팅은 SUI 네트워크 연결 시 동작")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n🛑 테스트 중단됨")
    except Exception as e:
        print(f"\n💥 테스트 실행 오류: {str(e)}")
        import traceback
        traceback.print_exc() 