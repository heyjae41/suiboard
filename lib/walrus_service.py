import subprocess
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_SUI_BIN_PATH = "/home/linuxbrew/.linuxbrew/bin/sui"
DEFAULT_WALRUS_CONFIG = {
    "publisher_url": "https://publisher.walrus-testnet.walrus.space",
    "aggregator_url": "https://aggregator.walrus-testnet.walrus.space",
    "sui_bin_path": DEFAULT_SUI_BIN_PATH,
    "storage_package_id": "0x1fad2576bf6359f0fafc8c089723c80fed4784f5e3ee508b037c5280f91e543f",  # Walrus 스토리지 패키지 ID
    "gas_budget": 100000000
}

# SUI 체인 스토리지용 설정 (현재 미사용)
# BOARD_STORAGE_ID = "0xb07d7417fed89e22255fada05fa0e63b07465f9a05a0cb25ca66ffb71bc95902"

class WalrusError(Exception):
    """Walrus 관련 오류"""
    pass

def store_post_on_walrus(title: str, content: str, author: str, board_table: str, walrus_config: dict = None) -> Optional[str]:
    """
    게시글을 Walrus 스토리지에 저장 (Publisher API 사용)
    
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
        
    try:
        # 1. 게시글 데이터를 JSON으로 구성
        post_data = {
            "title": title,
            "content": content,
            "author": author,
            "board_table": board_table,
            "timestamp": str(int(__import__('time').time() * 1000))
        }
        
        # 2. 임시 파일에 데이터 저장
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            json.dump(post_data, tmp_file, ensure_ascii=False, indent=2)
            tmp_filename = tmp_file.name
        
        # 3. Walrus Publisher를 통해 저장
        publisher_url = walrus_config.get("publisher_url")
        command = [
            "curl", "-X", "PUT",
            f"{publisher_url}/v1/store",
            "--data-binary", f"@{tmp_filename}",
            "-H", "Content-Type: application/json"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        response_data = json.loads(result.stdout)
        
        # 4. 임시 파일 삭제
        import os
        os.unlink(tmp_filename)
        
        # 5. blob_id 반환
        if "newlyCreated" in response_data:
            blob_id = response_data["newlyCreated"]["blobObject"]["blobId"]
            logger.info(f"게시글을 Walrus에 저장 완료: blob_id={blob_id}")
            return blob_id
        elif "alreadyCertified" in response_data:
            blob_id = response_data["alreadyCertified"]["blobId"]
            logger.info(f"게시글이 이미 Walrus에 존재함: blob_id={blob_id}")
            return blob_id
        else:
            logger.error(f"Walrus 저장 응답을 파싱할 수 없음: {response_data}")
            return None
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Walrus 저장 명령 실행 실패: {e.stderr}")
        raise WalrusError(f"Walrus 저장 실패: {e.stderr}")
    except json.JSONDecodeError as e:
        logger.error(f"Walrus 응답 JSON 파싱 실패: {e}")
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
        command = [
            "curl", "-X", "GET",
            f"{aggregator_url}/v1/{blob_id}"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        post_data = json.loads(result.stdout)
        
        logger.info(f"Walrus에서 게시글 조회 완료: blob_id={blob_id}")
        return post_data
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Walrus 조회 명령 실행 실패: {e.stderr}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Walrus 응답 JSON 파싱 실패: {e}")
        return None
    except Exception as e:
        logger.error(f"Walrus 조회 중 예상치 못한 오류: {e}")
        return None 