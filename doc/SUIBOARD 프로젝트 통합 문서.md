# SUIBOARD 프로젝트 통합 문서

## 목차
1. [프로젝트 개요](#1-프로젝트-개요)
2. [프로젝트 구조](#2-프로젝트-구조)
3. [주요 실행 흐름](#3-주요-실행-흐름)
4. [환경 설정](#4-환경-설정)
   - [4.1. 설치 방법](#41-설치-방법)
   - [4.2. 데이터베이스 설정](#42-데이터베이스-설정)
   - [4.3. 로컬 환경 설정](#43-로컬-환경-설정)
5. [SUI 블록체인 연동](#5-sui-블록체인-연동)
   - [5.1. Windows PC에 Sui 클라이언트 설치](#51-windows-pc에-sui-클라이언트-설치)
   - [5.2. Sui 클라이언트 Testnet 환경 설정](#52-sui-클라이언트-testnet-환경-설정)
   - [5.3. Ubuntu 서버에 SUI CLI 설치](#53-ubuntu-서버에-sui-cli-설치)
   - [5.4. Sui 토큰 작업](#54-sui-토큰-작업)
6. [주요 기능 구현](#6-주요-기능-구현)
   - [6.1. SUI 지갑 주소 연동](#61-sui-지갑-주소-연동)
   - [6.2. zkLogin Google 연동](#62-zklogin-google-연동)
   - [6.3. 게시글 작성 시 토큰 지급](#63-게시글-작성-시-토큰-지급)
   - [6.4. 글 삭제 시 토큰 회수](#64-글-삭제-시-토큰-회수)
   - [6.5. 로그인 시 토큰 제공](#65-로그인-시-토큰-제공)
7. [에이전트 기능](#7-에이전트-기능)
   - [7.1. Naver 주식 뉴스 에이전트](#71-naver-주식-뉴스-에이전트)
   - [7.2. Coindesk RSS 에이전트](#72-coindesk-rss-에이전트)
8. [참고 사항](#8-참고-사항)

## 1. 프로젝트 개요

SUIBOARD는 SUI 블록체인과 연동되는 기능을 갖춘 온라인 커뮤니티 게시판 플랫폼입니다. 이 프로젝트는 GNUBOARD6를 기반으로 하며, SUI 블록체인의 기능을 통합하여 사용자 참여에 대한 토큰 보상 시스템을 구현했습니다.

**애플리케이션 목적**: 
- SUI 블록체인과 연동되는 기능을 갖춘 온라인 커뮤니티 게시판 플랫폼
- 사용자들은 게시글 및 댓글을 작성하고, SUI 토큰 기반의 보상 시스템과 상호작용

**주요 기능**:
- 회원 가입, 로그인(일반 및 zkLogin), 정보 수정
- 게시글 작성, 조회, 수정, 삭제
- 댓글 작성, 조회, 수정, 삭제
- SUI 지갑 주소 등록 및 이를 활용한 기능 (토큰 지급/회수)
- 자동 게시글 생성 에이전트

**기술 스택**:
- 백엔드: Python, FastAPI
- 데이터베이스: PostgreSQL
- ORM: SQLAlchemy
- 템플릿 엔진: Jinja2
- 프론트엔드: HTML, CSS (Bootstrap 기반), JavaScript (jQuery)
- 블록체인: SUI (Testnet)

## 2. 프로젝트 구조

프로젝트는 `/root/suiboard/` 디렉토리에 위치하며, 주요 폴더 및 파일은 다음과 같습니다.

**루트 디렉토리**
- `main.py`: FastAPI 애플리케이션의 주 진입점
- `.env`: 데이터베이스 연결 정보, 테이블 접두사 등 주요 환경 변수 정의
- `sui_integration.log`: SUI 관련 기능 및 기타 주요 이벤트에 대한 로그 파일
- `requirements.txt`: Python 패키지 의존성 목록

**core/**
- `database.py`: SQLAlchemy 엔진 생성, 세션 관리 등 데이터베이스 연결 및 설정
- `models.py`: SQLAlchemy를 사용한 데이터베이스 테이블 매핑 모델 클래스
- `template.py`: Jinja2 템플릿 엔진 설정, 사용자 정의 필터 및 전역 함수 등록
- `routers.py`: 애플리케이션의 주요 라우터 등록
- `formclass.py`: FastAPI의 Form 데이터 처리를 위한 Pydantic 모델
- `exception.py`: 사용자 정의 예외 클래스 및 예외 처리 핸들러
- `middleware.py`: FastAPI 미들웨어 정의 및 등록

**bbs/**
- `index.py`: 웹사이트의 메인 페이지 라우트
- `member_profile.py`: 회원 정보 수정 관련 라우트
- `board.py`: 게시판 핵심 기능 담당 라우트 및 로직
- `login.py`: 로그인/로그아웃 관련 라우트
- `register.py`: 회원 가입 관련 라우트
- `zklogin.py`: Google zkLogin 인증 관련 라우트

**templates/**
- `bootstrap/`: 현재 사용 중인 기본 테마 폴더
  - `base.html`: 모든 페이지의 기본 레이아웃
  - `index.html`: 메인 페이지 구성
  - `member/`: 회원 관련 템플릿
  - `board/`: 게시판 관련 템플릿
  - `social/`: 소셜 로그인 관련 템플릿
  - `static/js/zklogin_handler.js`: zkLogin 처리 JavaScript

**lib/**
- `common.py`: 전역적으로 사용되는 유틸리티 함수
- `sui_service.py`: SUI 블록체인 연동 관련 함수
- `dependency/`: FastAPI 의존성 주입 관련 함수
- `template_filters.py`, `template_functions.py`: Jinja2 템플릿 사용자 정의 필터/함수

**service/**
- `agent_service.py`: 자동 게시글 생성 에이전트 서비스
- `board/`: 게시판 관련 서비스 (게시글 생성, 삭제 등)
- `sui_transaction_log_service.py`: SUI 트랜잭션 로그 서비스

**agent/**
- `naver_stock_agent.py`: 네이버 주식 뉴스 수집 에이전트
- `rss_coindesk_agent.py`: Coindesk RSS 피드 수집 에이전트

**suiboard_token/**
- `sources/suiboard_token.move`: SUIBOARD 토큰 Move 컨트랙트

**data/**
- 이미지 및 파일 저장 디렉토리 (설치 시 자동 생성)

## 3. 주요 실행 흐름

1. **요청 수신**: 사용자의 HTTP 요청이 FastAPI 애플리케이션으로 들어옵니다.
2. **미들웨어 처리**: `main.py`에 등록된 미들웨어들이 순차적으로 실행됩니다.
3. **라우팅**: 요청된 URL 경로에 따라 라우트 함수가 매칭됩니다.
4. **의존성 주입**: 라우트 함수에 정의된 의존성들이 실행되어 필요한 객체나 데이터가 함수로 전달됩니다.
5. **비즈니스 로직 처리**: 라우트 함수 내에서 핵심 비즈니스 로직이 수행됩니다.
6. **템플릿 렌더링**: 필요한 경우, Jinja2 템플릿 엔진을 사용하여 HTML 응답을 생성합니다.
7. **응답 반환**: 생성된 HTML, JSON 또는 리디렉션 응답이 사용자에게 반환됩니다.

**사용자 인증**:
- 세션 기반으로 처리되며, 로그인 시 세션에 사용자 ID가 저장됩니다.
- `get_login_member` 의존성을 통해 현재 로그인한 사용자 정보를 가져옵니다.
- zkLogin을 통한 Google 인증도 지원합니다.

**게시글 작성 처리 과정**:
1. 게시글 작성 요청 처리 (`/api/v1/boards/{bo_table}/writes` POST)
2. 유효성 검사 (비밀글, 내용, 작성 권한 등)
3. 데이터 정리
4. 게시글 저장 (`g6_write_{bo_table}` 테이블)
5. 최신글 테이블에 추가 (`g6_board_new`)
6. 포인트 추가 (`g6_point`)
7. SUI 토큰 지급 (설정된 경우)
8. 메일 발송 (설정된 경우)
9. 공지글 설정 (설정된 경우)
10. 캐시 삭제 및 트랜잭션 커밋

## 4. 환경 설정

### 4.1. 설치 방법

**Git을 사용한 설치**:
```bash
# Github에서 suiboard 복사 및 설치
git clone https://github.com/gnuboard/g6.git

# cd 명령어를 이용하여 suiboard 디렉토리로 이동
cd suiboard

# 가상환경 생성 (선택사항)
python -m venv venv

# Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
# 또는
source venv\Scripts\activate

# 필요한 패키지 설치
python -m pip install -r requirements.txt

# 서버 실행
# Linux
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
# 또는 백그라운드 실행
nohup uvicorn main:app --reload --host 0.0.0.0 > ~/suiboard/uvicorn.log 2>&1 &

# Windows
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

**윈도우 피시 개발환경 설치**:
```bash
cd C:\suiboard
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2. 데이터베이스 설정

`.env` 파일은 프로젝트 루트에 위치하며, 주요 설정은 다음과 같습니다:

```
# 테이블 이름 접두사 설정
DB_TABLE_PREFIX='****************'
'****************'
DB_ENGINE='****************'
DB_USER='****************'
DB_PASSWORD='****************'
DB_HOST='****************'
DB_PORT='****************'
DB_NAME='****************'
DB_CHARSET='****************'

# 이메일 발송 설정
SMTP_SERVER="localhost"
SMTP_PORT=25
SMTP_USERNAME="account@your-domain.com"
SMTP_PASSWORD=""

# 관리자 테마 설정
ADMIN_THEME = "basic"

# 이미지 설정
UPLOAD_IMAGE_RESIZE = "False"
UPLOAD_IMAGE_SIZE_LIMIT = 20
UPLOAD_IMAGE_QUALITY = 80
UPLOAD_IMAGE_RESIZE_WIDTH = 1200
UPLOAD_IMAGE_RESIZE_HEIGHT = 2800

# 디버그 모드 설정
APP_IS_DEBUG = "False"

# 웹사이트 표시 방법 (반응형/적응형)
IS_RESPONSIVE = "True"

# 쿠키 도메인 설정
COOKIE_DOMAIN = "marketmaker.store"
```

### 4.3. 로컬 환경 설정

로컬 환경(http://localhost)에서 suiboard 프로젝트를 테스트하기 위해 수정하거나 확인해야 할 주요 설정 지점들은 다음과 같습니다:

**1. Google Cloud Console OAuth 2.0 클라이언트 ID 설정**
- 승인된 JavaScript 원본: 기존 서버 도메인 외에 로컬 테스트용으로 `http://localhost`와 `http://localhost:포트번호` 추가
- 승인된 리디렉션 URI: 기존 서버용 리디렉션 URI 외에 로컬 테스트용으로 `http://localhost:포트번호/auth/zklogin/callback` 추가

**2. 프론트엔드 JavaScript 파일 수정 (`templates/bootstrap/static/js/zklogin_handler.js`)**
- `GOOGLE_CLIENT_ID`: Google Cloud Console에서 설정한 OAuth 2.0 클라이언트 ID와 일치해야 함
- `REDIRECT_URI`: 현재 `window.location.origin + "/auth/zklogin/callback"`으로 설정되어 있어 자동으로 적용됨

**3. 백엔드 Python 파일 수정 (`bbs/zklogin.py`)**
- `GOOGLE_CLIENT_ID`: 환경 변수(`GOOGLE_CLIENT_ID_ZKLOGIN`) 설정 또는 코드 내 플레이스홀더 수정

**4. 데이터베이스 연결 설정 (`.env` 파일)**
- 로컬 DB 사용 시 `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` 등을 로컬 환경에 맞게 수정

**5. FastAPI 애플리케이션 실행**
- 로컬에서 FastAPI 실행 시 사용하는 포트 번호를 URI 설정과 일치시켜야 함

## 5. SUI 블록체인 연동

### 5.1. Windows PC에 Sui 클라이언트 설치

**방법 1: Chocolatey 사용 (권장, 간편)**
1. Chocolatey 설치 (관리자 권한 PowerShell):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force;
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. Sui 설치:
   ```powershell
   choco install sui
   ```

3. 설치 확인:
   ```powershell
   sui --version
   ```

**방법 2: GitHub에서 바이너리 직접 다운로드**
1. Sui GitHub 릴리즈 페이지 접속
2. 최신 릴리즈 선택
3. Windows용 바이너리 다운로드 (예: `sui-testnet-windows-amd64-vX.Y.Z.tgz`)
4. 압축 해제 (예: `C:\sui`)
5. 환경 변수 PATH 설정 (sui.exe 파일이 있는 폴더 경로 추가)
6. 설치 확인: `sui --version`

### 5.2. Sui 클라이언트 Testnet 환경 설정

1. 네트워크 환경 확인 및 전환:
   ```bash
   sui client envs
   sui client switch --env testnet
   ```

2. 지갑 생성 또는 복구:
   - 새 지갑 생성:
     ```bash
     sui client new-address ed25519
     ```
   - 기존 지갑 복구 (니모닉 필요):
     ```bash
     sui keytool import <INPUT_STRING> <KEY_SCHEME> [DERIVATION_PATH]
     ```

3. 활성 주소 확인:
   ```bash
   sui client active-address
   ```

4. Testnet SUI 토큰 요청 (가스비용):
   - Sui Discord 서버의 #testnet-faucet 채널 이용
   - 또는 Sui 웹 Faucet 사용: https://faucet.testnet.sui.io/

5. 잔액 확인:
   ```bash
   sui client gas
   ```
6. 배포된 패키지 및 객체 ID 상수
   SUI_BIN_PATH = "/home/linuxbrew/.linuxbrew/bin/sui"  # SUI 바이너리 실행 파일 경로
   TOKEN_PACKAGE_ID = "0x7ded54267def06202efa3e9ffb8df024d03b43f9741a9348332eee2ed63ef165"  # 토큰 컨트랙트 패키지 ID (2023-05-10 업데이트)
   TOKEN_TREASURY_CAP_ID = "0x3fe97fd206b14a8fc560aeb926eebc36afd68687fbece8df50f8de1012b28e59"  # 토큰 관리 권한 객체 ID (2023-05-10 업데이트)
   STORAGE_PACKAGE_ID = "0x1fad2576bf6359f0fafc8c089723c80fed4784f5e3ee508b037c5280f91e543f"  # 스토리지 컨트랙트 패키지 ID (2023-05-10 업데이트)
   BOARD_STORAGE_ID = "0xb07d7417fed89e22255fada05fa0e63b07465f9a05a0cb25ca66ffb71bc95902"  # 게시판 스토리지 객체 ID (2023-05-10 업데이트)
   CLOCK_ID = "0x6"  # SUI의 시간 관련 시스템 객체 ID
   GAS_BUDGET = 100000000  # 트랜잭션 실행에 필요한 가스 예산 (필요에 따라 조정)

### 5.3. Ubuntu 서버에 SUI CLI 설치

1. SUI 바이너리 다운로드:
   ```bash
   wget https://github.com/MystenLabs/sui/releases/download/testnet-v1.20.0/sui-testnet-linux-amd64-v1.20.0.tgz -O sui-binaries.tgz
   ```

2. 바이너리 압축 해제 및 이동:
   ```bash
   tar -xzf sui-binaries.tgz
   mkdir -p /home/ubuntu/sui_bin
   cp sui-testnet-linux-amd64-v1.20.0/sui /home/ubuntu/sui_bin/
   chmod +x /home/ubuntu/sui_bin/sui
   ```

3. SUI Client 환경 설정:
   ```bash
   /home/ubuntu/sui_bin/sui client envs
   /home/ubuntu/sui_bin/sui client switch --env testnet
   /home/ubuntu/sui_bin/sui client active-address
   ```

4. 애플리케이션 스크립트 확인:
   - `/home/ubuntu/suiboard/lib/sui_service.py` 파일 내의 다음 상수들이 현재 SUI 환경 및 배포된 패키지 정보와 일치하는지 확인:
     - `SUI_BIN_PATH = "/home/ubuntu/sui_bin"`
     - `TOKEN_PACKAGE_ID`: SUIBOARD 토큰 패키지의 실제 ID
     - `TOKEN_TREASURY_CAP_ID`: SUIBOARD 토큰의 TreasuryCap 오브젝트 ID
     - `GAS_BUDGET`: 적절한 가스 예산

### 5.4. Sui 토큰 작업

**토큰 발행 (Mint)**:
```bash
sui client call --package <PACKAGE_ID> --module suiboard_token --function mint --args <TREASURY_CAP_ID> <AMOUNT> <RECIPIENT_ADDRESS> --gas-budget 10000000
```

**토큰 소각 (Burn)**:
```bash
sui client call --package <PACKAGE_ID> --module suiboard_token --function burn --args <TREASURY_CAP_ID> <COIN_OBJECT_ID> --gas-budget 10000000
```

**토큰 전송**:
```bash
sui client transfer-sui --amount <AMOUNT> --to <RECIPIENT_ADDRESS> --gas-budget 10000000
```

**토큰 잔액 확인**:
```bash
sui client gas
```

## 6. 주요 기능 구현

### 6.1. SUI 지갑 주소 연동

**목표**: 회원 정보 수정 페이지에서 사용자가 자신의 SUI 블록체인 지갑 주소를 입력하고 저장할 수 있도록 기능을 구현합니다.

**구현 내용**:
1. **UI 필드 추가**: `templates/bootstrap/member/register_form.html` 템플릿 파일에 SUI 지갑 주소 입력 필드 추가
2. **데이터 모델 수정**: `core/models.py`의 `Member` 클래스에 `mb_sui_address` 필드 추가
3. **데이터베이스 스키마 변경**: `g6_member` 테이블에 `mb_sui_address` 컬럼 추가
4. **백엔드 저장 로직**: `bbs/member_profile.py`의 `member_profile_save` 함수에서 처리

### 6.2. zkLogin Google 연동

**목표**: 사용자가 Google 계정을 통해 Sui zkLogin을 사용하여 로그인할 수 있도록 기능을 구현합니다.

**구현 내용**:
1. **로그인 UI 수정**: `templates/bootstrap/social/social_login.html`에 "Login with Google (zkLogin)" 버튼 추가
2. **프론트엔드 zkLogin 핸들러**: `templates/bootstrap/static/js/zklogin_handler.js` 파일 생성
   - Sui SDK 함수들을 CDN ESM 모듈 방식으로 임포트
   - Google OAuth 2.0 인증 흐름 처리
   - Sui Testnet 네트워크 설정
3. **백엔드 zkLogin 라우터**: `bbs/zklogin.py` 파일 생성
   - `/api/zklogin/authenticate` 엔드포인트 정의
   - JWT 검증 및 Salt 정보 조회
   - 신규 사용자 자동 등록 및 계정 연동 기능
4. **데이터 모델 수정**: `Member` 모델에 `mb_google_sub` 필드 추가

**설정 요구사항**:
- Google Cloud Console에서 OAuth 2.0 클라이언트 ID 발급
- 승인된 JavaScript 원본 및 리디렉션 URI 설정
- `g6_member` 테이블에 `mb_google_sub` 컬럼 추가

### 6.3. 게시글 작성 시 토큰 지급

**목표**: 사용자가 게시글을 작성할 때 SUI 블록체인의 SUIBOARD 토큰을 지급합니다.

**구현 내용**:
1. **SUI 연동 모듈**: `lib/sui_service.py` 파일에 토큰 발행 함수 구현
   ```python
   def mint_suiboard_token(recipient_address: str, amount: int, sui_config: dict = None) -> str:
       """
       SUIBOARD 토큰을 지정된 주소로 발행합니다.
       
       Args:
           recipient_address: 토큰을 받을 SUI 주소
           amount: 발행할 토큰 양
           sui_config: SUI 설정 (패키지 ID, 트레저리캡 ID 등)
           
       Returns:
           트랜잭션 다이제스트 (해시)
       """
   ```

2. **게시글 생성 서비스 연동**: `service/agent_service.py`에 토큰 지급 로직 추가
   - 게시글 DB 저장 성공 후 토큰 지급 실행
   - 사용자의 `mb_sui_address` 확인 및 유효성 검사
   - 트랜잭션 결과 로깅

3. **트랜잭션 로그 서비스**: `service/sui_transaction_log_service.py` 구현
   ```python
   def log_sui_transaction(db: Session, mb_id: str, wr_id: int, bo_table: str, amount: int, 
                          tx_hash: str, status: str, reason: str, error_message: str = None):
       """
       SUI 트랜잭션 내역을 DB에 기록합니다.
       """
   ```

4. **데이터 모델 추가**: `core/models.py`에 `SuiTransactionlog` 모델 추가
   ```python
   class SuiTransactionlog(Base):
       __tablename__ = f"{TABLE_PREFIX}sui_transaction_log"
       
       stl_id = Column(Integer, primary_key=True, autoincrement=True)
       mb_id = Column(String(20), nullable=False, index=True)
       wr_id = Column(Integer, nullable=True)
       bo_table = Column(String(20), nullable=True)
       stl_amount = Column(Integer, nullable=False, default=0)
       stl_tx_hash = Column(String(255), nullable=True)
       stl_status = Column(String(20), nullable=False, default='pending')
       stl_reason = Column(String(255), nullable=True)
       stl_error = Column(Text, nullable=True)
       stl_datetime = Column(DateTime, nullable=False, default=datetime.now)
   ```

### 6.4. 글 삭제 시 토큰 회수

**목표**: 게시글 삭제 시 해당 글 작성으로 지급되었던 SUIBOARD 토큰을 회수(소각)합니다.

**구현 내용**:
1. **토큰 회수 워크플로우**:
   - 글 삭제 시, 해당 글 작성으로 지급된 토큰 양 확인 (`g6_sui_transaction_log` 조회)
   - 시스템이 해당 양만큼의 토큰을 소각하는 2단계 절차 실행:
     1. 시스템 관리 주소로 소각할 양만큼의 토큰을 `mint` (새로운 Coin 객체 생성)
     2. 생성된 Coin 객체를 `burn` 함수를 통해 소각

2. **SUI 연동 모듈 수정**: `lib/sui_service.py`에 토큰 회수 함수 구현
   ```python
   def reclaim_suiboard_token(amount_to_reclaim: int, sui_config: dict = None) -> str:
       """
       지정된 양만큼의 SUIBOARD 토큰을 회수(소각)합니다.
       
       Args:
           amount_to_reclaim: 회수할 토큰 양
           sui_config: SUI 설정 (패키지 ID, 트레저리캡 ID 등)
           
       Returns:
           burn 트랜잭션 다이제스트 (해시)
       """
   ```

3. **게시글 삭제 로직 연동**: `service/board/delete_post.py` 수정
   - 삭제 대상 게시글에 대해 지급되었던 토큰 양 조회
   - 조회된 토큰 양이 0보다 크면 토큰 회수 실행
   - 트랜잭션 결과(성공/실패)에 따라 DB에 회수 로그 기록

4. **트랜잭션 로그 기록**: 회수 내역을 `g6_sui_transaction_log` 테이블에 기록
   - `stl_reason`: "게시글 삭제로 인한 토큰 회수"
   - `stl_amount`: 음수 값으로 기록

### 6.5. 로그인 시 토큰 제공

**목표**: 사용자 로그인 시 1일 1회에 한하여 SUIBOARD 토큰을 자동으로 지급합니다.

**구현 내용**:
1. **로그인 처리 로직 수정**: `bbs/login.py`의 로그인 성공 처리 부분에 토큰 지급 로직 추가
   - 사용자의 마지막 로그인 토큰 지급 시간 확인
   - 24시간 이상 경과한 경우에만 토큰 지급
   - 지급 내역 DB에 기록

2. **토큰 지급 함수 호출**:
   ```python
   # 로그인 성공 시 토큰 지급 (1일 1회)
   if member.mb_sui_address and (member.mb_today_login is None or 
      (datetime.now() - member.mb_today_login).total_seconds() > 86400):
       try:
           # 2 토큰 지급
           tx_hash = mint_suiboard_token(member.mb_sui_address, 2)
           # 로그 기록
           log_sui_transaction(db, member.mb_id, None, None, 2, tx_hash, 
                              'success', '로그인 보상 토큰 지급')
           # 마지막 지급 시간 업데이트
           member.mb_today_login = datetime.now()
           db.commit()
       except Exception as e:
           logger.error(f"로그인 토큰 지급 실패: {str(e)}")
   ```

## 7. 에이전트 기능

### 7.1. Naver 주식 뉴스 에이전트

**목표**: 네이버 금융 사이트에서 주식 관련 뉴스를 자동으로 수집하여 게시판에 등록합니다.

**구현 내용**:
1. **에이전트 스크립트**: `agent/naver_stock_agent.py`
   - 네이버 금융 뉴스 페이지 크롤링
   - 수집된 뉴스 데이터 정제
   - 게시글 등록 API 호출

2. **게시글 등록 처리**:
   - 카테고리: 주식(stock)
   - 테이블: `g6_board_stock`
   - 포인트: `g6_point` 테이블에 point 2 추가
   - 최신글: `g6_board_new` 테이블에 신규게시글 등록

3. **실행 방법**:
   ```bash
   screen -S naver_stock
   python agent/naver_stock_agent.py
   # Ctrl+A+D로 세션 백그라운드 전환
   ```

### 7.2. Coindesk RSS 에이전트

**목표**: Coindesk RSS 피드에서 블록체인 관련 뉴스를 자동으로 수집하여 게시판에 등록합니다.

**구현 내용**:
1. **에이전트 스크립트**: `agent/rss_coindesk_agent.py`
   - feedparser 라이브러리를 사용하여 RSS 피드 파싱
   - 수집된 뉴스 데이터 정제
   - 게시글 등록 API 호출

2. **게시글 등록 처리**:
   - 카테고리: 블록체인(blockchain)
   - 테이블: `g6_board_blockchain`
   - 포인트: `g6_point` 테이블에 point 2 추가
   - 최신글: `g6_board_new` 테이블에 신규게시글 등록

3. **실행 방법**:
   ```bash
   screen -S coindesk_agent
   python agent/rss_coindesk_agent.py
   # Ctrl+A+D로 세션 백그라운드 전환
   ```

## 8. 참고 사항

1. **정보 수정 화면 글자 겹침 현상**: 정보 수정 화면의 'SUI 지갑 주소' 입력 필드 레이블과 플레이스홀더 텍스트가 겹쳐 보이는 CSS 스타일 문제가 있습니다. `templates/bootstrap/member/register_form.html` 또는 관련 CSS 파일에서 해당 요소의 스타일을 조정하여 해결해야 합니다.

2. **정보 수정 화면 SUI 주소 미표시 (간헐적)**: 데이터베이스에는 주소가 정상적으로 저장되어 있음에도 불구하고, 정보 수정 화면을 다시 방문했을 때 간혹 SUI 지갑 주소가 입력 필드에 표시되지 않는 문제가 있습니다. 브라우저/서버 캐시, 데이터 로딩 시점/누락, 폼 데이터 클래스 등을 점검해볼 필요가 있습니다.

3. **DB 마이그레이션 도구**: 현재 데이터베이스 스키마 변경은 수동 스크립트로 관리되고 있습니다. 향후 프로젝트 규모가 커지거나 협업이 필요할 경우, Alembic과 같은 SQLAlchemy 기반의 데이터베이스 마이그레이션 도구를 도입하여 스키마 변경 이력을 체계적으로 관리하는 것을 권장합니다.

4. **로깅 강화**: `sui_integration.log` 외에도 애플리케이션 전반의 주요 이벤트 및 오류에 대한 로깅을 강화하여 디버깅 및 유지보수 효율성을 높일 수 있습니다.

5. **SUI 관련 설정**: 토큰 발행 및 회수 기능을 사용하기 위해서는 `lib/sui_service.py` 내의 `DEFAULT_SUI_CONFIG`에 있는 `package_id`, `treasury_cap_id`를 실제 배포된 `suiboard_token` 컨트랙트의 정보로 수정해야 합니다. SUI CLI 경로(`sui_bin_path`) 또한 서버 환경에 맞게 설정되어야 합니다.

6. **네트워크 일치**: SUI CLI가 연결된 네트워크, `TOKEN_PACKAGE_ID`, `TOKEN_TREASURY_CAP_ID`는 모두 SUIBOARD 토큰이 실제로 배포되고 운영되는 동일한 SUI 네트워크(mainnet, testnet, devnet 중 하나)를 기준으로 해야 합니다.

7. **가스비**: 토큰 발행 및 소각 트랜잭션에는 가스비(SUI 토큰)가 소모됩니다. SUI CLI에 연결된 활성 주소에는 충분한 SUI 토큰이 있어야 합니다.
