# /home/ubuntu/suiboard_project_v3/lib/sui_service.py
import subprocess
import json
import logging
import re # For extracting object ID
import os
import platform

# Configure logging
logger = logging.getLogger(__name__)

def get_default_sui_bin_path():
    """OS에 따라 기본 SUI CLI 경로를 반환합니다."""
    system = platform.system().lower()
    
    if system == "windows":
        # Windows 환경에서 일반적인 SUI CLI 경로들
        username = os.environ.get('USERNAME', 'User')
        possible_paths = [
            "C:\\ProgramData\\chocolatey\\bin\\sui.exe",
            f"C:\\Users\\{username}\\AppData\\Local\\Programs\\sui\\sui.exe",
            "sui.exe"  # PATH에 등록된 경우
        ]
    elif system == "linux":
        # Linux 환경에서 일반적인 SUI CLI 경로들
        possible_paths = [
            "/home/linuxbrew/.linuxbrew/bin/sui",
            "/usr/local/bin/sui",
            "/usr/bin/sui",
            "sui"  # PATH에 등록된 경우
        ]
    elif system == "darwin":  # macOS
        # macOS 환경에서 일반적인 SUI CLI 경로들
        possible_paths = [
            "/opt/homebrew/bin/sui",
            "/usr/local/bin/sui",
            "sui"  # PATH에 등록된 경우
        ]
    else:
        # 기타 OS의 경우 PATH에서 찾기
        possible_paths = ["sui"]
    
    # 실제로 존재하는 경로 찾기
    for path in possible_paths:
        try:
            # PATH에 등록된 경우 (sui, sui.exe)
            if path in ["sui", "sui.exe"]:
                result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    logger.info(f"SUI CLI found in PATH: {path}")
                    return path
            # 절대 경로인 경우
            elif os.path.exists(path):
                logger.info(f"SUI CLI found at: {path}")
                return path
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    # 찾지 못한 경우 기본값 반환
    default_path = "sui.exe" if system == "windows" else "sui"
    logger.warning(f"SUI CLI not found in common locations. Using default: {default_path}")
    return default_path

def get_default_mint_address():
    """기본 민트 주소를 동적으로 가져옵니다."""
    try:
        sui_bin_path = get_default_sui_bin_path()
        return _get_active_sui_address(sui_bin_path)
    except Exception as e:
        logger.warning(f"Failed to get active address, using fallback: {e}")
        return "0xcfd7707740d1e2a7ea3a3d70128d38ced43d59625354b78cb6f3c8794d952264"

DEFAULT_SUI_BIN_PATH = get_default_sui_bin_path()
DEFAULT_GAS_BUDGET = 100000000 

# Default SUI configuration
DEFAULT_SUI_CONFIG = {
    "network": "testnet", # or "mainnet", "devnet"
    "package_id": "0x7ded54267def06202efa3e9ffb8df024d03b43f9741a9348332eee2ed63ef165", # 패키지 ID
    "treasury_cap_id": "0x3fe97fd206b14a8fc560aeb926eebc36afd68687fbece8df50f8de1012b28e59", # Treasury Cap ID
    "gas_budget": DEFAULT_GAS_BUDGET,
    "sui_bin_path": DEFAULT_SUI_BIN_PATH
}

class SuiInteractionError(Exception):
    """Custom exception for SUI interaction failures."""
    pass

def _get_active_sui_address(sui_bin_path: str) -> str:
    """Helper function to get the active SUI address from the CLI."""
    try:
        result = subprocess.run([sui_bin_path, "client", "active-address"], capture_output=True, text=True, check=True)
        active_address = result.stdout.strip()
        if not active_address.startswith("0x") or len(active_address) < 5:
            raise SuiInteractionError(f"Invalid active address format: {active_address}")
        logger.info(f"Retrieved active SUI address: {active_address}")
        return active_address
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get active SUI address. Return code: {e.returncode}, Stderr: {e.stderr}")
        raise SuiInteractionError(f"Failed to get active SUI address: {e.stderr if e.stderr else e.stdout}")
    except Exception as e:
        logger.error(f"Unexpected error getting active SUI address: {e}")
        raise SuiInteractionError(f"Unexpected error getting active SUI address: {e}")

def extract_transaction_hash(sui_output: str) -> str:
    """SUI CLI 출력에서 트랜잭션 해시를 추출합니다"""
    if not sui_output:
        logger.warning("Empty SUI output provided for hash extraction")
        return None
        
    try:
        # JSON 파싱 시도
        output_json = json.loads(sui_output)
        
        # 다양한 JSON 구조에서 해시 찾기
        hash_locations = [
            output_json.get("digest"),
            output_json.get("effects", {}).get("transactionDigest"),
            output_json.get("transactionDigest"),
            output_json.get("result", {}).get("digest")
        ]
        
        for hash_value in hash_locations:
            if hash_value and isinstance(hash_value, str) and hash_value.startswith("0x") and len(hash_value) == 66:
                logger.debug(f"Transaction hash extracted from JSON: {hash_value}")
                return hash_value
                
    except json.JSONDecodeError:
        logger.debug("JSON parsing failed, attempting regex extraction")
    except Exception as e:
        logger.warning(f"Unexpected error during JSON parsing: {e}")
    
    # JSON 파싱 실패 시 정규식으로 해시 추출
    hash_patterns = [
        r'Transaction Digest:\s*(0x[a-fA-F0-9]{64})',
        r'digest["\']?\s*:\s*["\']?(0x[a-fA-F0-9]{64})',
        r'(0x[a-fA-F0-9]{64})'  # 일반적인 해시 패턴
    ]
    
    for pattern in hash_patterns:
        hash_match = re.search(pattern, sui_output, re.IGNORECASE)
        if hash_match:
            hash_value = hash_match.group(1) if hash_match.lastindex else hash_match.group(0)
            if hash_value.startswith("0x") and len(hash_value) == 66:
                logger.debug(f"Transaction hash extracted with regex: {hash_value}")
                return hash_value
    
    logger.warning(f"Could not extract transaction hash from output: {sui_output[:200]}...")
    return None

def award_suiboard_token(recipient_address: str, amount: int, sui_config: dict) -> str:
    """SUIBOARD 토큰을 지급하고 발행량을 추적합니다."""
    from core.database import DBConnect
    from core.models import TokenSupply
    from datetime import datetime
    
    # 입력 검증
    if not recipient_address or not recipient_address.startswith("0x"):
        raise ValueError(f"Invalid recipient address format: {recipient_address}")
    
    if amount <= 0:
        raise ValueError(f"Amount must be positive: {amount}")
    
    required_keys = ["package_id", "treasury_cap_id"]
    for key in required_keys:
        if key not in sui_config:
            raise ValueError(f"Missing required SUI configuration key: {key}")
    
    # 발행량 제한 체크
    db_connect = DBConnect()
    db = db_connect.sessionLocal()
    try:
        supply_record = db.query(TokenSupply).first()
        
        if not supply_record:
            # 최초 실행 시 토큰 공급량 기록 생성
            supply_record = TokenSupply(
                total_minted=0,
                total_burned=0,
                max_supply=100000000,  # 1억개 제한
                last_updated=datetime.now(),
                notes="Initial token supply record created"
            )
            db.add(supply_record)
            db.commit()
            logger.info("토큰 공급량 추적 테이블 초기화 완료")
        
        # 발행 가능 여부 확인
        if not supply_record.can_mint(amount):
            remaining = supply_record.remaining_supply
            error_msg = f"토큰 발행 한도 초과: 요청량 {amount}, 남은 발행가능량 {remaining}, 최대공급량 {supply_record.max_supply}"
            logger.error(error_msg)
            raise SuiInteractionError(error_msg)
        
        # 실제 토큰 민팅 실행
        logger.info(f"Attempting to award {amount} SUIBOARD tokens to {recipient_address}")
        
        # SUI CLI 명령 실행
        command = [
            sui_config.get("sui_bin_path", DEFAULT_SUI_BIN_PATH),
            "client", "call",
            "--package", sui_config["package_id"],
            "--module", "suiboard_token",
            "--function", "mint",
            "--args",
            sui_config["treasury_cap_id"],
            str(amount),
            recipient_address,
            "--gas-budget", str(sui_config.get("gas_budget", DEFAULT_GAS_BUDGET)),
            "--json"
        ]
        
        command_str = " ".join(command)
        logger.info(f"SUI CLI 명령 실행: {command_str}")
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"SUI CLI 명령 결과 - stdout: {result.stdout}")
        if result.stderr:
            logger.warning(f"SUI CLI 명령 stderr: {result.stderr}")
        
        # JSON 응답 파싱
        try:
            response_json = json.loads(result.stdout)
            if "error" in response_json:
                error_message = response_json.get("error", "Unknown SUI error")
                logger.error(f"SUI CLI call failed with error: {error_message}")
                raise SuiInteractionError(f"SUI CLI call failed: {error_message}")
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response, attempting text parsing")
        
        # 트랜잭션 해시 추출
        tx_hash = extract_transaction_hash(result.stdout)
        
        if tx_hash:
            # 발행량 업데이트
            supply_record.total_minted += amount
            supply_record.last_updated = datetime.now()
            supply_record.notes = f"Minted {amount} tokens to {recipient_address}, TX: {tx_hash}"
            db.commit()
            
            logger.info(f"SUIBOARD 토큰 {amount}개 발행 완료: {recipient_address}, TX: {tx_hash}")
            logger.info(f"총 발행량: {supply_record.total_minted}/{supply_record.max_supply}, 남은 발행가능량: {supply_record.remaining_supply}")
            return tx_hash
        else:
            error_msg = f"트랜잭션 해시를 찾을 수 없음: {result.stdout}"
            logger.error(error_msg)
            raise SuiInteractionError(error_msg)
            
    except subprocess.CalledProcessError as e:
        error_msg = f"SUI CLI 명령 실패 (RC: {e.returncode}): {e.stderr if e.stderr else e.stdout}"
        logger.error(error_msg)
        raise SuiInteractionError(error_msg)
    except SuiInteractionError:
        raise
    except Exception as e:
        logger.error(f"토큰 지급 중 예상치 못한 오류: {str(e)}")
        raise SuiInteractionError(f"토큰 지급 실패: {str(e)}")
    finally:
        db.close()

def reclaim_suiboard_token(amount_to_reclaim: int, sui_config: dict) -> str:
    """토큰을 회수합니다 (민트 후 즉시 소각)."""
    logger.info(f"Attempting to reclaim (mint and burn) {amount_to_reclaim} Suiboard tokens.")
    
    # 입력 검증
    if amount_to_reclaim <= 0:
        raise ValueError(f"Amount to reclaim must be positive: {amount_to_reclaim}")
    
    required_keys = ["package_id", "treasury_cap_id"]
    for key in required_keys:
        if key not in sui_config:
            raise ValueError(f"Missing required SUI configuration key for reclaim: {key}")

    sui_bin_path = sui_config.get("sui_bin_path", DEFAULT_SUI_BIN_PATH)
    package_id = sui_config["package_id"]
    treasury_cap_id = sui_config["treasury_cap_id"]
    gas_budget_mint = sui_config.get("gas_budget_mint", sui_config.get("gas_budget", DEFAULT_GAS_BUDGET))
    gas_budget_burn = sui_config.get("gas_budget_burn", sui_config.get("gas_budget", DEFAULT_GAS_BUDGET))
    
    # Determine the address to mint the temporary coin to (for burning)
    # This should ideally be an address controlled by the system/TreasuryCap holder.
    # For simplicity, using the CLI's active address.
    try:
        mint_to_address = _get_active_sui_address(sui_bin_path)
        logger.info(f"Temporary coin for burning will be minted to active CLI address: {mint_to_address}")
    except SuiInteractionError as e:
        logger.error(f"Cannot proceed with reclaim: Failed to get active SUI address for minting temporary coin. Error: {e}")
        raise

    # Step 1: Mint a new coin object with the amount_to_reclaim to the mint_to_address
    mint_command = [
        sui_bin_path, "client", "call",
        "--package", package_id,
        "--module", "suiboard_token",
        "--function", "mint",
        "--args", treasury_cap_id, str(amount_to_reclaim), mint_to_address,
        "--gas-budget", str(gas_budget_mint),
        "--json"
    ]
    mint_command_str = " ".join(mint_command)
    logger.info(f"Executing SUI CLI mint command for reclaim: {mint_command_str}")
    newly_minted_coin_id = None
    try:
        mint_result = subprocess.run(mint_command, capture_output=True, text=True, check=True)
        logger.info(f"SUI CLI mint (for reclaim) command output: {mint_result.stdout}")
        mint_response_json = json.loads(mint_result.stdout)

        if "error" in mint_response_json:
            error_message = mint_response_json.get("error", "Unknown SUI error from mint (for reclaim) JSON response")
            logger.error(f"SUI CLI mint (for reclaim) call failed with error: {error_message}")
            raise SuiInteractionError(f"SUI CLI mint (for reclaim) call failed: {error_message}")

        # Extract the newly created Coin object ID
        # This part is critical and depends heavily on the SUI CLI version and output format.
        # Looking for created objects of type Coin<SUIBOARD_TOKEN>
        created_objects = mint_response_json.get("effects", {}).get("created", [])
        if not created_objects:
             # Fallback for older SUI CLI versions or different output structures
            object_changes = mint_response_json.get("objectChanges", [])
            for change in object_changes:
                if change.get("type") == "created" and "Coin<" in change.get("objectType", ""):
                    created_objects.append(change)
        
        for obj in created_objects:
            object_type = obj.get("objectType", "")
            # We need to be more specific if possible, e.g., by checking the full type string
            # Example: f"{package_id}::suiboard_token::SUIBOARD_TOKEN"
            # For now, a simpler check for Coin and ensuring it's not the gas coin.
            if "Coin<" in object_type and package_id in object_type: # Check if it's our token
                newly_minted_coin_id = obj.get("objectId")
                if newly_minted_coin_id:
                    logger.info(f"Successfully minted temporary coin for burning. Object ID: {newly_minted_coin_id}")
                    break
        
        if not newly_minted_coin_id:
            logger.error(f"Could not find newly minted Coin<SUIBOARD_TOKEN> object ID in mint (for reclaim) response: {mint_response_json}")
            raise SuiInteractionError("Failed to extract newly minted coin ID for burning.")

    except subprocess.CalledProcessError as e:
        logger.error(f"SUI CLI mint (for reclaim) command failed. RC: {e.returncode}, Stdout: {e.stdout}, Stderr: {e.stderr}")
        raise SuiInteractionError(f"SUI CLI mint (for reclaim) execution failed: {e.stderr if e.stderr else e.stdout}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from SUI CLI mint (for reclaim): {e}, Raw: {mint_result.stdout}")
        raise SuiInteractionError(f"Failed to decode SUI CLI mint (for reclaim) JSON: {mint_result.stdout}")
    except Exception as e:
        logger.error(f"Unexpected error during mint (for reclaim): {e}")
        raise SuiInteractionError(f"Unexpected error during mint (for reclaim): {e}")

    # Step 2: Burn the newly minted coin
    burn_command = [
        sui_bin_path, "client", "call",
        "--package", package_id,
        "--module", "suiboard_token",
        "--function", "burn",
        "--args", treasury_cap_id, newly_minted_coin_id,
        "--gas-budget", str(gas_budget_burn),
        "--json"
    ]
    burn_command_str = " ".join(burn_command)
    logger.info(f"Executing SUI CLI burn command: {burn_command_str}")
    try:
        burn_result = subprocess.run(burn_command, capture_output=True, text=True, check=True)
        logger.info(f"SUI CLI burn command output: {burn_result.stdout}")
        burn_response_json = json.loads(burn_result.stdout)

        if "error" in burn_response_json:
            error_message = burn_response_json.get("error", "Unknown SUI error from burn JSON response")
            logger.error(f"SUI CLI burn call failed with error: {error_message}")
            raise SuiInteractionError(f"SUI CLI burn call failed: {error_message}")

        tx_digest_burn = None
        if "digest" in burn_response_json:
            tx_digest_burn = burn_response_json["digest"]
        elif burn_response_json.get("effects", {}).get("status", {}).get("status") == "success":
            tx_digest_burn = burn_response_json.get("effects", {}).get("transactionDigest")
        
        if not tx_digest_burn:
            logger.error(f"Could not extract transaction digest from SUI CLI burn response: {burn_response_json}")
            raise SuiInteractionError(f"Could not extract transaction digest from SUI CLI burn response. Response: {burn_result.stdout}")

        logger.info(f"Suiboard token reclaim (burn) successful. Transaction Digest: {tx_digest_burn}")
        return tx_digest_burn

    except subprocess.CalledProcessError as e:
        logger.error(f"SUI CLI burn command failed. RC: {e.returncode}, Stdout: {e.stdout}, Stderr: {e.stderr}")
        raise SuiInteractionError(f"SUI CLI burn command execution failed: {e.stderr if e.stderr else e.stdout}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from SUI CLI burn: {e}, Raw: {burn_result.stdout}")
        raise SuiInteractionError(f"Failed to decode SUI CLI burn JSON response: {burn_result.stdout}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during SUI token burn: {e}")
        raise SuiInteractionError(f"An unexpected error occurred during token burn: {e}")

if __name__ == '__main__':
    print("SUI Service Module - Direct Testing")
    print(f"Default SUI binary path: {DEFAULT_SUI_BIN_PATH}")
    
    # Test SUI CLI availability
    try:
        active_address = _get_active_sui_address(DEFAULT_SUI_BIN_PATH)
        print(f"Active SUI address: {active_address}")
        print("SUI CLI is available and working!")
    except Exception as e:
        print(f"SUI CLI test failed: {e}")
    
    # Example configuration for testing
    print("\nExample configuration:")
    print(f"DEFAULT_SUI_CONFIG = {DEFAULT_SUI_CONFIG}")
    
    # Example for testing award_suiboard_token (requires setup):
    # try:
    #     test_config = DEFAULT_SUI_CONFIG.copy()
    #     test_recipient = "0x1234567890abcdef1234567890abcdef12345678"  # Replace with valid address
    #     test_amount = 100
    #     tx_hash = award_suiboard_token(test_recipient, test_amount, test_config)
    #     print(f"Test award transaction hash: {tx_hash}")
    # except Exception as e:
    #     print(f"Test award failed: {e}")
    
    # Example for testing reclaim_suiboard_token (requires setup):
    # try:
    #     test_config = DEFAULT_SUI_CONFIG.copy()
    #     test_config["gas_budget"] = 30000000  # Higher budget for two transactions
    #     amount_to_reclaim_test = 50
    #     reclaim_digest = reclaim_suiboard_token(amount_to_reclaim_test, test_config)
    #     print(f"Test reclaim transaction digest: {reclaim_digest}")
    # except Exception as e:
    #     print(f"Test reclaim failed: {e}")

