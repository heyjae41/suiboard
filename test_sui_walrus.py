#!/usr/bin/env python3
"""
SUIBOARD 토큰 지급과 Walrus 스토리지 기능 테스트 스크립트
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lib.sui_service import award_suiboard_token, DEFAULT_SUI_CONFIG
from lib.walrus_service import store_post_on_walrus, retrieve_post_from_walrus, DEFAULT_WALRUS_CONFIG
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_suiboard_token():
    """SUIBOARD 토큰 지급 테스트"""
    print("=== SUIBOARD 토큰 지급 테스트 ===")
    
    # 테스트용 주소 (실제 SUI 주소로 교체 필요)
    test_address = "0x75afdd8da74b9e64cdc62cfcbd7eaaa4ec0538cee13d468094912b5078b1e636"
    test_login_amount = 2  # 로그인 보상
    test_post_amount = 1   # 게시글 작성 보상
    
    try:
        print(f"테스트 주소: {test_address}")
        print(f"로그인 보상 토큰량: {test_login_amount} SUIBOARD")
        print(f"게시글 작성 보상 토큰량: {test_post_amount} SUIBOARD")
        print(f"사용할 설정: {DEFAULT_SUI_CONFIG}")
        
        # 실제로는 실행하지 않고 설정만 확인
        print("주의: 실제 토큰 지급은 실행하지 않습니다. 설정만 확인합니다.")
        print("실제 실행을 원하면 아래 주석을 해제하세요:")
        print("# tx_hash = award_suiboard_token(test_address, test_login_amount, DEFAULT_SUI_CONFIG)")
        print("# print(f'로그인 보상 트랜잭션 해시: {tx_hash}')")
        print("# tx_hash = award_suiboard_token(test_address, test_post_amount, DEFAULT_SUI_CONFIG)")
        print("# print(f'게시글 작성 보상 트랜잭션 해시: {tx_hash}')")
        
    except Exception as e:
        print(f"SUIBOARD 토큰 테스트 중 오류: {e}")

def test_walrus_storage():
    """Walrus 스토리지 테스트"""
    print("\n=== Walrus 스토리지 테스트 ===")
    
    # 테스트 게시글 데이터
    test_title = "테스트 게시글"
    test_content = "이것은 Walrus 스토리지 테스트를 위한 게시글입니다."
    test_author = "테스트 사용자"
    test_board = "test_board"
    
    try:
        print(f"제목: {test_title}")
        print(f"내용: {test_content}")
        print(f"작성자: {test_author}")
        print(f"게시판: {test_board}")
        print(f"사용할 설정: {DEFAULT_WALRUS_CONFIG}")
        
        # 실제로는 실행하지 않고 설정만 확인
        print("주의: 실제 Walrus 저장은 실행하지 않습니다. 설정만 확인합니다.")
        print("실제 실행을 원하면 아래 주석을 해제하세요:")
        print("# blob_id = store_post_on_walrus(test_title, test_content, test_author, test_board)")
        print("# print(f'Blob ID: {blob_id}')")
        print("# if blob_id:")
        print("#     retrieved_data = retrieve_post_from_walrus(blob_id)")
        print("#     print(f'조회된 데이터: {retrieved_data}')")
        
    except Exception as e:
        print(f"Walrus 스토리지 테스트 중 오류: {e}")

def check_configuration():
    """설정 확인"""
    print("\n=== 설정 확인 ===")
    
    print("SUIBOARD 토큰 (SUI 블록체인) 설정:")
    for key, value in DEFAULT_SUI_CONFIG.items():
        print(f"  {key}: {value}")
    
    print("\nWalrus 스토리지 설정:")
    for key, value in DEFAULT_WALRUS_CONFIG.items():
        print(f"  {key}: {value}")
    
    print("\n토큰 지급량:")
    print("  로그인 보상: 2 SUIBOARD 토큰")
    print("  게시글 작성 보상: 1 SUIBOARD 토큰")
    
    print("\n패키지 ID:")
    print("  SUIBOARD 토큰 패키지: 0x7ded54267def06202efa3e9ffb8df024d03b43f9741a9348332eee2ed63ef165")
    print("  Walrus 스토리지 패키지: 0x1fad2576bf6359f0fafc8c089723c80fed4784f5e3ee508b037c5280f91e543f")
    
    print("\n스토리지 방식:")
    print("  현재 사용: Walrus Publisher API (HTTP)")
    print("  미사용: SUI 체인 스토리지 컨트랙트 (board_storage_id 불필요)")
    
    print("\n주의사항:")
    print("1. treasury_cap_id가 실제 값으로 설정되어 있는지 확인하세요.")
    print("2. SUI CLI가 올바르게 설치되어 있는지 확인하세요.")
    print("3. 활성 SUI 주소가 설정되어 있는지 확인하세요.")
    print("4. Walrus 테스트넷이 접근 가능한지 확인하세요.")

if __name__ == "__main__":
    print("SUIBOARD 토큰 및 Walrus 스토리지 기능 테스트")
    print("=" * 60)
    
    check_configuration()
    test_suiboard_token()
    test_walrus_storage()
    
    print("\n테스트 완료!")
    print("실제 기능을 테스트하려면 스크립트의 주석을 해제하고 실행하세요.") 