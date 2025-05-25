#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import subprocess
import tempfile
import os

def test_walrus_connection():
    """Walrus 테스트넷 연결 테스트 (최신 CLI 방식)"""
    
    # 최신 Walrus 테스트넷 설정 (2025년 5월 기준)
    package_id = "0xdf9033cac39b7a9b9f76fb6896c9fc5283ba730d6976a2b1d85ad1e6036c3272"
    sui_rpc_url = "https://fullnode.testnet.sui.io:443"
    walrus_binary = "walrus"
    
    print("=== 최신 Walrus 테스트넷 연결 테스트 ===")
    print(f"패키지 ID: {package_id}")
    print(f"Sui RPC URL: {sui_rpc_url}")
    
    # 1. Sui RPC 연결 테스트
    print(f"\n1. Sui RPC 연결 테스트")
    try:
        response = requests.post(
            sui_rpc_url,
            json={"jsonrpc": "2.0", "id": 1, "method": "sui_getChainIdentifier", "params": []},
            timeout=10
        )
        print(f"   상태 코드: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 체인 ID: {data.get('result', 'N/A')}")
        else:
            print(f"   ❌ 응답 내용: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    # 2. Walrus CLI 설치 확인
    print(f"\n2. Walrus CLI 설치 확인")
    try:
        result = subprocess.run([walrus_binary, "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"   ✅ Walrus CLI 버전: {result.stdout.strip()}")
        else:
            print(f"   ❌ Walrus CLI 오류: {result.stderr}")
    except FileNotFoundError:
        print(f"   ❌ Walrus CLI가 설치되지 않음: {walrus_binary}")
        print(f"   💡 설치 방법: https://docs.walrus.site/walrus-sites/tutorial.html")
        return
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return
    
    # 3. Walrus CLI를 사용한 데이터 저장 테스트
    print(f"\n3. Walrus CLI 데이터 저장 테스트")
    try:
        test_data = {
            "title": "테스트 게시글",
            "content": "Walrus CLI 테스트 내용입니다.",
            "author": "test_user",
            "board_table": "test_board",
            "timestamp": str(int(time.time() * 1000))
        }
        
        # 임시 파일에 데이터 저장
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
            json.dump(test_data, tmp_file, ensure_ascii=False, indent=2)
            tmp_filename = tmp_file.name
        
        print(f"   임시 파일: {tmp_filename}")
        print(f"   데이터: {test_data}")
        
        try:
            # Walrus CLI로 저장
            command = [
                walrus_binary, "store",
                tmp_filename,
                "--rpc-url", sui_rpc_url,
                "--json"
            ]
            
            print(f"   명령어: {' '.join(command)}")
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=60)
            
            print(f"   반환 코드: {result.returncode}")
            if result.stdout:
                print(f"   표준 출력: {result.stdout[:500]}...")
            if result.stderr:
                print(f"   표준 오류: {result.stderr[:500]}...")
            
            blob_id = None
            if result.returncode == 0 and result.stdout.strip():
                try:
                    response_data = json.loads(result.stdout)
                    if "newlyCreated" in response_data:
                        blob_id = response_data["newlyCreated"]["blobObject"]["blobId"]
                        print(f"   ✅ 저장 성공! blob_id: {blob_id}")
                    elif "alreadyCertified" in response_data:
                        blob_id = response_data["alreadyCertified"]["blobId"]
                        print(f"   ✅ 이미 존재함! blob_id: {blob_id}")
                    elif "blobId" in response_data:
                        blob_id = response_data["blobId"]
                        print(f"   ✅ 저장 성공! blob_id: {blob_id}")
                    else:
                        print(f"   ⚠️ 응답에서 blob_id를 찾을 수 없음: {response_data}")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON 파싱 실패: {e}")
                    print(f"   원본 출력: {result.stdout}")
            else:
                print(f"   ❌ 저장 실패")
                
            # 저장된 데이터 조회 테스트
            if blob_id:
                print(f"\n4. Walrus CLI 데이터 조회 테스트")
                
                command = [
                    walrus_binary, "read",
                    blob_id,
                    "--rpc-url", sui_rpc_url,
                    "--json"
                ]
                
                print(f"   조회 명령어: {' '.join(command)}")
                
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                
                print(f"   반환 코드: {result.returncode}")
                if result.stdout:
                    print(f"   표준 출력: {result.stdout[:500]}...")
                if result.stderr:
                    print(f"   표준 오류: {result.stderr[:500]}...")
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        retrieved_data = json.loads(result.stdout)
                        print(f"   ✅ 조회 성공!")
                        print(f"   제목: {retrieved_data.get('title', 'N/A')}")
                        print(f"   작성자: {retrieved_data.get('author', 'N/A')}")
                        print(f"   내용: {retrieved_data.get('content', 'N/A')[:50]}...")
                    except json.JSONDecodeError:
                        print(f"   ✅ 텍스트 조회 성공!")
                        print(f"   내용: {result.stdout[:100]}...")
                else:
                    print(f"   ❌ 조회 실패")
                    
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
                print(f"   🗑️ 임시 파일 삭제: {tmp_filename}")
            
    except Exception as e:
        print(f"   ❌ 저장 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

def test_walrus_service():
    """SUIBOARD Walrus 서비스 테스트"""
    print(f"\n=== SUIBOARD Walrus 서비스 테스트 ===")
    
    try:
        from lib.walrus_service import store_post_on_walrus, retrieve_post_from_walrus
        
        # 테스트 데이터
        title = "SUIBOARD 테스트 게시글"
        content = "이것은 SUIBOARD에서 Walrus로 저장하는 테스트입니다."
        author = "test_user"
        board_table = "g6_write_stockai"
        
        print(f"제목: {title}")
        print(f"내용: {content}")
        print(f"작성자: {author}")
        print(f"게시판: {board_table}")
        
        # 저장 테스트
        print(f"\n1. Walrus 저장 테스트")
        blob_id = store_post_on_walrus(title, content, author, board_table)
        
        if blob_id:
            print(f"   ✅ 저장 성공! blob_id: {blob_id}")
            
            # 조회 테스트
            print(f"\n2. Walrus 조회 테스트")
            retrieved_data = retrieve_post_from_walrus(blob_id)
            
            if retrieved_data:
                print(f"   ✅ 조회 성공!")
                print(f"   제목: {retrieved_data.get('title', 'N/A')}")
                print(f"   작성자: {retrieved_data.get('author', 'N/A')}")
                print(f"   내용: {retrieved_data.get('content', 'N/A')[:50]}...")
            else:
                print(f"   ❌ 조회 실패")
        else:
            print(f"   ❌ 저장 실패")
            
    except ImportError as e:
        print(f"   ❌ 모듈 import 실패: {e}")
        print(f"   💡 SUIBOARD 프로젝트 루트에서 실행해주세요.")
    except Exception as e:
        print(f"   ❌ 서비스 테스트 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_walrus_connection()
    test_walrus_service() 