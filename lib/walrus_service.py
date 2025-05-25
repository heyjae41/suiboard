import subprocess
import json
import logging
import requests
import tempfile
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_SUI_BIN_PATH = "/home/linuxbrew/.linuxbrew/bin/sui"
DEFAULT_WALRUS_CONFIG = {
    # 최신 Walrus 테스트넷 설정 (2025년 5월 기준)
    "package_id": "0xdf9033cac39b7a9b9f76fb6896c9fc5283ba730d6976a2b1d85ad1e6036c3272",  # 최신 Walrus 테스트넷 패키지 ID
    "sui_rpc_url": "https://fullnode.testnet.sui.io:443",  # Sui 테스트넷 RPC URL
    "sui_bin_path": DEFAULT_SUI_BIN_PATH,
    "walrus_binary": "walrus.exe" if os.name == 'nt' else "walrus",  # Walrus CLI 바이너리 경로 (Windows/Linux)
    "gas_budget": 500000000,  # 공식 권장 가스 예산
    "enabled": False,  # Walrus CLI 설치 후 True로 변경. 현재 서버가 Ubuntu 20이어서 비활성화. 최소 22 이상이어야 함. 현재 서버가 Ubuntu 20이어서 비활성화. 최소 22 이상이어야 함
    
    # 레거시 설정 (하위 호환성을 위해 유지)
    "storage_package_id": "0xdf9033cac39b7a9b9f76fb6896c9fc5283ba730d6976a2b1d85ad1e6036c3272",
    "publisher_url": None,  # 더 이상 사용하지 않음
    "aggregator_url": None,  # 더 이상 사용하지 않음
}

# SUI 체인 스토리지용 설정 (현재 미사용)
# BOARD_STORAGE_ID = "0xb07d7417fed89e22255fada05fa0e63b07465f9a05a0cb25ca66ffb71bc95902"

class WalrusError(Exception):
    """Walrus 관련 오류"""
    pass

def store_post_on_walrus(title: str, content: str, author: str, board_table: str, walrus_config: dict = None) -> Optional[str]:
    """
    게시글을 Walrus 스토리지에 저장 (최신 CLI 방식 사용)
    
    Args:
        title: 게시글 제목
        content: 게시글 내용  
        author: 작성자
        board_table: 게시판 테이블명
        walrus_config: Walrus 설정
        
    Returns:
        저장된 Post의 blob_id 또는 None
    """
    if walrus_config is None:
        walrus_config = DEFAULT_WALRUS_CONFIG
    
    # Walrus 기능이 비활성화된 경우 건너뛰기
    if not walrus_config.get("enabled", True):
        logger.info("Walrus 저장 기능이 비활성화되어 있습니다.")
        return None
    
    # 레거시 REST API 방식 체크 (하위 호환성)
    if walrus_config.get("publisher_url"):
        return _store_post_legacy_api(title, content, author, board_table, walrus_config)
    
    # 최신 CLI 방식 사용
    return _store_post_cli(title, content, author, board_table, walrus_config)

def _store_post_cli(title: str, content: str, author: str, board_table: str, walrus_config: dict) -> Optional[str]:
    """
    Walrus CLI를 사용하여 게시글 저장 (최신 방식)
    """
    try:
        # 1. 게시글 데이터를 JSON으로 구성
        post_data = {
            "title": title,
            "content": content,
            "author": author,
            "board_table": board_table,
            "timestamp": str(int(time.time() * 1000))
        }
        
        logger.info(f"Walrus CLI로 저장할 데이터: {post_data}")
        
        # 2. 임시 파일에 데이터 저장
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as tmp_file:
            json.dump(post_data, tmp_file, ensure_ascii=False, indent=2)
            tmp_filename = tmp_file.name
        
        try:
            # 3. Walrus CLI를 사용하여 저장
            walrus_binary = walrus_config.get("walrus_binary", "walrus")
            sui_rpc_url = walrus_config.get("sui_rpc_url")
            
            command = [
                walrus_binary, "store",
                tmp_filename,
                "--rpc-url", sui_rpc_url,
                "--json"
            ]
            
            logger.info(f"Walrus CLI 명령어: {' '.join(command)}")
            
            result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=60)
            
            # 4. 응답 파싱
            if result.stdout.strip():
                try:
                    response_data = json.loads(result.stdout)
                    
                    # blob_id 추출
                    blob_id = None
                    if "newlyCreated" in response_data:
                        blob_id = response_data["newlyCreated"]["blobObject"]["blobId"]
                        logger.info(f"게시글을 Walrus에 저장 완료: blob_id={blob_id}")
                    elif "alreadyCertified" in response_data:
                        blob_id = response_data["alreadyCertified"]["blobId"]
                        logger.info(f"게시글이 이미 Walrus에 존재함: blob_id={blob_id}")
                    elif "blobId" in response_data:
                        blob_id = response_data["blobId"]
                        logger.info(f"게시글을 Walrus에 저장 완료: blob_id={blob_id}")
                    
                    return blob_id
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Walrus CLI 응답 JSON 파싱 실패: {e}")
                    logger.error(f"응답 내용: {result.stdout}")
                    return None
            else:
                logger.error("Walrus CLI 응답이 비어있음")
                return None
                
        finally:
            # 5. 임시 파일 삭제
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
                
    except subprocess.CalledProcessError as e:
        logger.error(f"Walrus CLI 명령 실행 실패: {e.stderr}")
        raise WalrusError(f"Walrus CLI 실행 실패: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("Walrus CLI 명령 실행 시간 초과")
        raise WalrusError("Walrus CLI 실행 시간 초과")
    except Exception as e:
        logger.error(f"Walrus CLI 저장 중 예상치 못한 오류: {e}")
        raise WalrusError(f"Walrus CLI 저장 중 오류: {e}")

def _store_post_legacy_api(title: str, content: str, author: str, board_table: str, walrus_config: dict) -> Optional[str]:
    """
    레거시 REST API를 사용하여 게시글 저장 (하위 호환성)
    """
    try:
        # 1. 게시글 데이터를 JSON으로 구성
        post_data = {
            "title": title,
            "content": content,
            "author": author,
            "board_table": board_table,
            "timestamp": str(int(time.time() * 1000))
        }
        
        logger.info(f"Walrus 레거시 API로 저장할 데이터: {post_data}")
        
        # 2. JSON 데이터를 바이트로 변환
        json_data = json.dumps(post_data, ensure_ascii=False, indent=2)
        
        # 3. Walrus Publisher API 호출 (requests 사용)
        publisher_url = walrus_config.get("publisher_url")
        # publisher_url이 이미 /v1/api를 포함하고 있으므로 store만 추가
        if publisher_url.endswith("/v1/api"):
            store_url = f"{publisher_url}/store"
        else:
            store_url = f"{publisher_url}/v1/store"
        
        logger.info(f"Walrus Publisher URL: {store_url}")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # 요청 전송
        response = requests.put(
            store_url,
            data=json_data.encode('utf-8'),
            headers=headers,
            timeout=30  # 30초 타임아웃
        )
        
        logger.info(f"Walrus 응답 상태 코드: {response.status_code}")
        logger.info(f"Walrus 응답 내용: {response.text[:500]}...")  # 처음 500자만 로깅
        
        # 응답 상태 확인
        response.raise_for_status()
        
        # JSON 응답 파싱
        if not response.text.strip():
            logger.error("Walrus 응답이 비어있음")
            raise WalrusError("Walrus 응답이 비어있음")
            
        response_data = response.json()
        
        # 5. blob_id 반환
        if "newlyCreated" in response_data:
            blob_object = response_data["newlyCreated"]["blobObject"]
            blob_id = blob_object["blobId"]
            logger.info(f"게시글을 Walrus에 저장 완료: blob_id={blob_id}")
            return blob_id
        elif "alreadyCertified" in response_data:
            blob_id = response_data["alreadyCertified"]["blobId"]
            logger.info(f"게시글이 이미 Walrus에 존재함: blob_id={blob_id}")
            return blob_id
        else:
            logger.error(f"Walrus 저장 응답을 파싱할 수 없음: {response_data}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Walrus API 요청 실패: {e}")
        raise WalrusError(f"Walrus API 요청 실패: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Walrus 응답 JSON 파싱 실패: {e}")
        logger.error(f"응답 내용: {response.text if 'response' in locals() else 'N/A'}")
        raise WalrusError(f"Walrus 응답 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"Walrus 저장 중 예상치 못한 오류: {e}")
        raise WalrusError(f"Walrus 저장 중 오류: {e}")

def store_post_on_sui_chain(title: str, content: str, board_storage_id: str, walrus_config: dict = None) -> Optional[str]:
    """
    게시글을 SUI 체인의 스토리지 컨트랙트에 저장 (현재 미사용)
    
    Args:
        title: 게시글 제목
        content: 게시글 내용
        board_storage_id: 게시판 스토리지 객체 ID
        walrus_config: SUI/Walrus 설정
        
    Returns:
        트랜잭션 digest 또는 None
    """
    if walrus_config is None:
        walrus_config = DEFAULT_WALRUS_CONFIG
        
    try:
        sui_bin_path = walrus_config.get("sui_bin_path", DEFAULT_SUI_BIN_PATH)
        package_id = walrus_config.get("storage_package_id")
        gas_budget = walrus_config.get("gas_budget", 100000000)
        
        if not package_id:
            raise WalrusError("storage_package_id가 설정되지 않음")
        if not board_storage_id:
            raise WalrusError("board_storage_id가 필요함")
        
        # SUI 체인에 게시글 저장
        command = [
            sui_bin_path, "client", "call",
            "--package", package_id,
            "--module", "suiboard_storage", 
            "--function", "add_post",
            "--args", board_storage_id, title.encode().hex(), content.encode().hex(), "0x6",  # 0x6은 Clock object
            "--gas-budget", str(gas_budget),
            "--json"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        response_json = json.loads(result.stdout)
        
        if "error" in response_json:
            error_message = response_json.get("error", "Unknown SUI error")
            logger.error(f"SUI 체인 저장 실패: {error_message}")
            raise WalrusError(f"SUI 체인 저장 실패: {error_message}")
            
        # 트랜잭션 digest 추출
        tx_digest = None
        if "digest" in response_json:
            tx_digest = response_json["digest"]
        elif response_json.get("effects", {}).get("status", {}).get("status") == "success":
            tx_digest = response_json.get("effects", {}).get("transactionDigest")
            
        if tx_digest:
            logger.info(f"게시글을 SUI 체인에 저장 완료: {tx_digest}")
            return tx_digest
        else:
            logger.error(f"SUI 체인 저장 응답에서 트랜잭션 digest를 찾을 수 없음: {response_json}")
            return None
            
    except subprocess.CalledProcessError as e:
        logger.error(f"SUI 체인 저장 명령 실행 실패: {e.stderr}")
        raise WalrusError(f"SUI 체인 저장 실패: {e.stderr}")
    except json.JSONDecodeError as e:
        logger.error(f"SUI 응답 JSON 파싱 실패: {e}")
        raise WalrusError(f"SUI 응답 파싱 실패: {e}")
    except Exception as e:
        logger.error(f"SUI 체인 저장 중 예상치 못한 오류: {e}")
        raise WalrusError(f"SUI 체인 저장 중 오류: {e}")

def retrieve_post_from_walrus(blob_id: str, walrus_config: dict = None) -> Optional[dict]:
    """
    Walrus에서 게시글 데이터 조회
    
    Args:
        blob_id: Walrus blob ID
        walrus_config: Walrus 설정
        
    Returns:
        게시글 데이터 딕셔너리 또는 None
    """
    if walrus_config is None:
        walrus_config = DEFAULT_WALRUS_CONFIG
        
    try:
        aggregator_url = walrus_config.get("aggregator_url")
        # aggregator_url이 이미 /v1/api를 포함하고 있으므로 blob_id만 추가
        if aggregator_url.endswith("/v1/api"):
            retrieve_url = f"{aggregator_url}/{blob_id}"
        else:
            retrieve_url = f"{aggregator_url}/v1/{blob_id}"
        
        logger.info(f"Walrus에서 데이터 조회: {retrieve_url}")
        
        response = requests.get(retrieve_url, timeout=30)
        
        logger.info(f"Walrus 조회 응답 상태 코드: {response.status_code}")
        
        response.raise_for_status()
        
        if not response.text.strip():
            logger.error("Walrus 조회 응답이 비어있음")
            return None
            
        post_data = response.json()
        
        logger.info(f"Walrus에서 게시글 조회 완료: blob_id={blob_id}")
        return post_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Walrus 조회 API 요청 실패: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Walrus 조회 응답 JSON 파싱 실패: {e}")
        logger.error(f"응답 내용: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Walrus 조회 중 예상치 못한 오류: {e}")
        return None 