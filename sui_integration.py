"""
SUI 블록체인 연동 모듈
- SUI 블록체인에 토큰 발행과 데이터 저장을 위한 Python 인터페이스
- 주요 기능: 토큰 발행(mint_tokens), 게시물 저장(store_post_on_sui)

SUI client 설치 방법 : Chocolatey 사용 (권장, 간편)
    Chocolatey 설치: 아직 Chocolatey가 설치되어 있지 않다면, Chocolatey 공식 웹사이트 의 안내에 따라 설치합니다. 관리자 권한으로 PowerShell을 열고 다음 명령어를 실행하면 됩니다:

    powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1') )

    Sui 설치: Chocolatey 설치 후, 새 관리자 권한 PowerShell 창에서 다음 명령어를 사용하여 Sui를 설치합니다:
    powershell
    choco install sui

    설치가 완료되면 sui --version 명령어로 설치를 확인할 수 있습니다.
"""
import subprocess
import json
import os
import platform

# 배포된 패키지 및 객체 ID 상수 (실제 ID로 대체해야 함)
# SUI 바이너리 실행 파일 경로 (OS별로 설정)
if platform.system() == 'Windows':
    SUI_BIN_PATH = "sui"  # Windows에서는 PATH에서 찾도록 설정
else:
    SUI_BIN_PATH = "/home/linuxbrew/.linuxbrew/bin/sui"  # Linux용 경로
TOKEN_PACKAGE_ID = "0x7ded54267def06202efa3e9ffb8df024d03b43f9741a9348332eee2ed63ef165"  # 토큰 컨트랙트 패키지 ID (2023-05-10 업데이트)
TOKEN_TREASURY_CAP_ID = "0x3fe97fd206b14a8fc560aeb926eebc36afd68687fbece8df50f8de1012b28e59"  # 토큰 관리 권한 객체 ID (2023-05-10 업데이트)
STORAGE_PACKAGE_ID = "0x1fad2576bf6359f0fafc8c089723c80fed4784f5e3ee508b037c5280f91e543f"  # 스토리지 컨트랙트 패키지 ID (2023-05-10 업데이트)
BOARD_STORAGE_ID = "0xb07d7417fed89e22255fada05fa0e63b07465f9a05a0cb25ca66ffb71bc95902"  # 게시판 스토리지 객체 ID (2023-05-10 업데이트)
CLOCK_ID = "0x6"  # SUI의 시간 관련 시스템 객체 ID
GAS_BUDGET = 100000000  # 트랜잭션 실행에 필요한 가스 예산 (필요에 따라 조정)

def _run_sui_command(command_args):
    """
    SUI CLI 명령어를 subprocess를 통해 실행하는 내부 헬퍼 함수
    
    Args:
        command_args (list): SUI CLI에 전달할 명령어 인자 리스트
        
    Returns:
        subprocess.CompletedProcess: 명령어 실행 결과
        
    Raises:
        Exception: 명령어 실행 중 오류 발생 시
    """
    env = os.environ.copy()
    # Windows에서는 PATH 설정을 다르게 처리
    if platform.system() == 'Windows':
        # Windows에서는 sui.exe가 PATH에 있어야 함
        pass  # 환경 변수 수정 불필요
    else:
        env["PATH"] = f"{SUI_BIN_PATH}:{env.get('PATH', '')}"  # Linux에서 PATH에 SUI 바이너리 경로 추가
    
    try:
        print(f"Running SUI command: sui {' '.join(command_args)}")
        
        # Windows 환경에서 명령어를 문자열로 실행
        if platform.system() == 'Windows':
            command_str = "sui " + " ".join(command_args)
            result = subprocess.run(command_str, capture_output=True, text=True, check=True, env=env, encoding='utf-8', shell=True)
        else:
            result = subprocess.run(["sui"] + command_args, capture_output=True, text=True, check=True, env=env)
            
        print(f"SUI command output: {result.stdout}")
        print(f"SUI command error: {result.stderr}")
        # 기본적인 트랜잭션 성공 여부 검사 (세부 조정 필요할 수 있음)
        if "error" in result.stderr.lower() and "status: \"success\"" not in result.stderr.lower():
             raise Exception(f"SUI command failed: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running SUI command: {e}")
        print(f"Stderr: {e.stderr}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def mint_tokens(recipient_address: str, amount: int):
    """
    지정된 수량의 Suiboard 토큰을 수신자 주소로 발행(민팅)합니다.
    
    Args:
        recipient_address (str): 토큰을 받을 SUI 지갑 주소
        amount (int): 발행할 토큰 수량
        
    Returns:
        bool: 토큰 발행 성공 시 True, 실패 시 False
    """
    print(f"Attempting to mint {amount} tokens for {recipient_address}")
    command = [
        "client", "call",  # SUI 클라이언트 호출 명령어
        "--package", TOKEN_PACKAGE_ID,  # 토큰 컨트랙트 패키지 ID
        "--module", "suiboard_token",  # 호출할 모듈 이름
        "--function", "mint",  # 호출할 함수 이름
        "--args",  # 함수 인자 시작
        TOKEN_TREASURY_CAP_ID,  # 토큰 발행 권한 객체 ID
        str(amount),  # 발행할 토큰 수량
        recipient_address,  # 수신자 주소
        "--gas-budget", str(GAS_BUDGET)  # 트랜잭션 가스 예산
    ]
    try:
        _run_sui_command(command)
        print(f"Successfully minted {amount} tokens for {recipient_address}")
        return True
    except Exception as e:
        print(f"Failed to mint tokens: {e}")
        return False

def store_post_on_sui(title: str, content: str):
    """
    게시물을 SUI 블록체인에 저장합니다(suiboard_storage 모듈 사용).
    
    Args:
        title (str): 게시물 제목
        content (str): 게시물 내용
        
    Returns:
        bool: 게시물 저장 성공 시 True, 실패 시 False
    """
    print(f"Attempting to store post: Title='{title}'")
    # SUI CLI는 문자열 인자를 vector<u8> 형태로 예상하므로 16진수로 인코딩
    title_hex = title.encode('utf-8').hex()
    content_hex = content.encode('utf-8').hex()

    command = [
        "client", "call",  # SUI 클라이언트 호출 명령어
        "--package", STORAGE_PACKAGE_ID,  # 스토리지 컨트랙트 패키지 ID
        "--module", "suiboard_storage",  # 호출할 모듈 이름
        "--function", "add_post",  # 호출할 함수 이름
        "--args",  # 함수 인자 시작
        BOARD_STORAGE_ID,  # 게시판 스토리지 객체 ID
        f"vector[{title_hex}]",  # 16진수 벡터로 변환된 제목
        f"vector[{content_hex}]",  # 16진수 벡터로 변환된 내용
        CLOCK_ID,  # 시간 객체 ID (타임스탬프용)
        "--gas-budget", str(GAS_BUDGET)  # 트랜잭션 가스 예산
    ]
    try:
        _run_sui_command(command)
        print(f"Successfully stored post '{title}' on SUI")
        return True
    except Exception as e:
        print(f"Failed to store post on SUI: {e}")
        return False

def get_post_from_sui(post_id: int):
    """
    SUI 블록체인에서 저장된 게시물을 조회합니다.
    
    Args:
        post_id (int): 조회할 게시물 ID
        
    Returns:
        dict: 조회된 게시물 정보 (실패 시 None)
    """
    print(f"Attempting to get post with ID: {post_id}")
    
    # 1. 먼저 BoardStorage 객체의 dynamic field 목록을 조회
    command = [
        "client", "dynamic-field",  # SUI 클라이언트 dynamic-field 명령어
        BOARD_STORAGE_ID,  # 게시판 스토리지 객체 ID
        "--json"  # JSON 형식으로 출력
    ]
    try:
        result = _run_sui_command(command)
        
        # 결과를 JSON으로 파싱
        import json
        try:
            data = json.loads(result.stdout)
            print(f"Retrieved dynamic fields: {json.dumps(data, indent=2)}")
            
            # post_id에 해당하는 필드 찾기
            for field in data.get("data", []):
                field_name = field.get("name", {}).get("value")
                if str(field_name) == str(post_id):
                    field_id = field.get("objectId")
                    print(f"Found post with ID {post_id}, object ID: {field_id}")
                    
                    # 2. 해당 dynamic field 객체의 세부 정보 조회
                    detail_command = [
                        "client", "object",
                        field_id,
                        "--json"
                    ]
                    detail_result = _run_sui_command(detail_command)
                    post_data = json.loads(detail_result.stdout)
                    print(f"Successfully retrieved post {post_id} from SUI")
                    
                    # 3. 데이터 변환 - hexadecimal 형식의 title과 content를 문자열로 변환
                    post_fields = post_data.get("content", {}).get("fields", {}).get("value", {}).get("fields", {})
                    
                    # title 변환 (vector[hexstring] 형식에서 문자열로)
                    title_hex = post_fields.get("title", "")
                    title_text = ""
                    if title_hex.startswith("vector[") and title_hex.endswith("]"):
                        hex_str = title_hex[7:-1]  # "vector[" 와 "]" 제거
                        try:
                            title_text = bytes.fromhex(hex_str).decode('utf-8')
                        except Exception as e:
                            print(f"Error decoding title: {e}")
                            title_text = title_hex
                    
                    # content 변환 (vector[hexstring] 형식에서 문자열로)
                    content_hex = post_fields.get("content", "")
                    content_text = ""
                    if content_hex.startswith("vector[") and content_hex.endswith("]"):
                        hex_str = content_hex[7:-1]  # "vector[" 와 "]" 제거
                        try:
                            content_text = bytes.fromhex(hex_str).decode('utf-8')
                        except Exception as e:
                            print(f"Error decoding content: {e}")
                            content_text = content_hex
                    
                    # 변환된 데이터를 추가하여 반환
                    human_readable_post = {
                        "id": post_id,
                        "title": title_text,
                        "content": content_text,
                        "author": post_fields.get("author", ""),
                        "timestamp": post_fields.get("timestamp", ""),
                        "raw_data": post_data
                    }
                    return human_readable_post
            
            print(f"Post with ID {post_id} not found")
            return None
        except json.JSONDecodeError:
            print(f"Failed to parse JSON from output: {result.stdout}")
            return None
    except Exception as e:
        print(f"Failed to get post from SUI: {e}")
        return None

# 예제 사용법 (테스트용)
if __name__ == "__main__":
    # 테스트넷에 생성된 주소 (festive-diamond)
    test_address = "0xcfd7707740d1e2a7ea3a3d70128d38ced43d59625354b78cb6f3c8794d952264"

    print("Testing mint_tokens...")
    mint_success = mint_tokens(test_address, 10)  # 10개 토큰 테스트 발행
    print(f"Minting test result: {mint_success}\n")

    print("Testing store_post_on_sui...")
    store_success = store_post_on_sui("My First SUI Post", "This post is stored on the SUI blockchain!")  # 테스트 게시물 저장
    print(f"Storing post test result: {store_success}\n")
    
    print("Testing get_post_from_sui...")
    post_data = get_post_from_sui(0)  # 첫 번째 게시물(ID: 0) 조회
    print(f"Retrieved post data: {post_data}")

