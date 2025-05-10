# 프로젝트 인수인계 문서: SUIBOARD

## 1. 프로젝트 개요

이 문서는 SUIBOARD 애플리케이션의 현재 상태, 구조, 주요 기능 및 최근 작업 내역을 다음 작업자에게 인계하기 위해 작성되었습니다.

*   **애플리케이션 목적**: SUI 블록체인과 연동되는 기능을 갖춘 온라인 커뮤니티 게시판 플랫폼입니다. 사용자들은 게시글 및 댓글을 작성하고, SUI 토큰 기반의 보상 시스템과 상호작용할 수 있습니다.
*   **주요 기능**:
    *   회원 가입, 로그인, 정보 수정
    *   게시글 작성, 조회, 수정, 삭제
    *   댓글 작성, 조회, 수정, 삭제
    *   SUI 지갑 주소 등록 및 이를 활용한 기능 (예: 토큰 지급)
*   **기술 스택**:
    *   백엔드: Python, FastAPI
    *   데이터베이스: PostgreSQL
    *   ORM: SQLAlchemy
    *   템플릿 엔진: Jinja2
    *   프론트엔드: HTML, CSS (Bootstrap 기반), JavaScript (jQuery)

## 2. 프로젝트 구조

프로젝트는 `/home/ubuntu/suiboard/` 디렉토리에 위치하며, 주요 폴더 및 파일은 다음과 같습니다.

*   **`/home/ubuntu/suiboard/` (루트 디렉토리)**
    *   `main.py`: FastAPI 애플리케이션의 주 진입점입니다. 미들웨어, 라우터, 예외 처리기, 생명주기 이벤트 등을 설정합니다.
    *   `.env`: 데이터베이스 연결 정보, 테이블 접두사 등 주요 환경 변수를 정의하는 파일입니다.
    *   `sui_integration.log`: SUI 관련 기능 및 기타 주요 이벤트에 대한 로그 파일입니다.
    *   `requirements.txt`: Python 패키지 의존성 목록입니다.
*   **`core/`**: 애플리케이션의 핵심 로직을 담고 있는 폴더입니다.
    *   `database.py`: SQLAlchemy 엔진 생성, 세션 관리 등 데이터베이스 연결 및 설정을 담당합니다.
    *   `models.py`: SQLAlchemy를 사용하여 데이터베이스 테이블에 매핑되는 모델 클래스(예: `Member`, `Board`, `WriteBaseModel`, `Config` 등)를 정의합니다.
    *   `template.py`: Jinja2 템플릿 엔진 설정, 사용자 정의 필터 및 전역 함수 등록, 테마 관리 등을 담당합니다.
    *   `routers.py`: 애플리케이션의 주요 라우터들을 모아 등록하는 역할을 합니다. 각 기능별 라우터(예: `bbs/`, `admin/`)를 포함합니다.
    *   `formclass.py`: FastAPI의 Form 데이터를 처리하기 위한 Pydantic 모델들을 정의합니다. (예: `UpdateMemberForm`)
    *   `exception.py`: 사용자 정의 예외 클래스 및 예외 처리 핸들러를 정의합니다.
    *   `middleware.py`: FastAPI 미들웨어를 정의하고 등록합니다.
*   **`bbs/`**: 게시판 시스템(Bulletin Board System)과 관련된 기능 모듈이 위치합니다.
    *   `index.py`: 웹사이트의 메인 페이지 (루트 URL `/`) 라우트를 처리합니다.
    *   `member_profile.py`: 회원 정보 수정 관련 라우트 (`/member_confirm`, `/member_profile`)를 처리합니다.
    *   `board.py`: 특정 게시판의 게시글 목록 조회, 게시글 작성/읽기/수정/삭제, 댓글 작성 등 게시판 핵심 기능을 담당하는 라우트 및 로직을 포함합니다.
    *   `login.py`: 로그인/로그아웃 관련 라우트를 처리합니다.
    *   `register.py`: 회원 가입 관련 라우트를 처리합니다.
    *   기타: `content.py`, `faq.py`, `qa.py`, `memo.py` 등 다양한 게시판 관련 부가 기능 라우터들이 존재합니다.
*   **`templates/`**: Jinja2 템플릿 파일들이 위치하는 폴더입니다.
    *   `bootstrap/`: 현재 사용 중인 기본 테마 폴더입니다. (예: `basic` 테마 대신 `bootstrap` 테마를 사용 중일 수 있음)
        *   `base.html`: 모든 페이지의 기본 레이아웃을 정의하는 템플릿입니다.
        *   `index.html`: 메인 페이지의 내용을 구성하는 템플릿입니다.
        *   `member/`: 회원 관련 템플릿 폴더입니다.
            *   `register_form.html`: 회원 가입 및 정보 수정 시 사용되는 폼 템플릿입니다.
            *   `member_confirm.html`: 정보 수정 전 비밀번호를 확인하는 폼 템플릿입니다.
        *   `board/`: 게시판 관련 템플릿 폴더입니다.
            *   `read_post.html`: 게시글 읽기 페이지 템플릿입니다.
        *   기타: `head.html`, `header.html`, `footer.html` 등 공통 UI 컴포넌트 템플릿들이 존재합니다.
*   **`static/`**: CSS 파일, JavaScript 파일, 이미지 등 정적 파일들이 위치합니다.
*   **`lib/`**: 공통 라이브러리 및 헬퍼 함수들을 포함합니다.
    *   `common.py`: 전역적으로 사용되는 유틸리티 함수들 (예: IP 주소 가져오기, 이미지 처리, 고유 ID 생성 등)을 포함합니다.
    *   `dependency/`: FastAPI 의존성 주입 관련 함수들을 포함합니다.
    *   `template_filters.py`, `template_functions.py`: Jinja2 템플릿에서 사용될 사용자 정의 필터 및 함수를 정의합니다.
*   **`admin/`**: 관리자 페이지 관련 기능 및 템플릿을 포함합니다.
*   **`install/`**: 애플리케이션 초기 설치 관련 라우터 및 로직을 포함합니다.
*   **`api/`**: 외부 API 연동 또는 애플리케이션 자체 API 엔드포인트를 정의합니다.
*   **`data/`**: cache된 페이지를 제공합니다. 화면이 수정사항을 반영하지 않는다면 이 캐시 폴더의 파일들을 삭제하세요.
*   **`agent/`**: 독립적으로 외부의 사이트를 다양한 방식으로 스크래핑해서 게시글을 자동으로 생성합니다. 

## 3. 주요 실행 흐름

1.  **요청 수신**: 사용자의 HTTP 요청이 FastAPI 애플리케이션으로 들어옵니다.
2.  **미들웨어 처리**: `main.py`에 등록된 미들웨어들이 순차적으로 실행됩니다. (예: DB 세션 설정, 사용자 인증 정보 로드, IP 차단 등)
3.  **라우팅**: 요청된 URL 경로에 따라 `core/routers.py` 및 각 하위 모듈(예: `bbs/member_profile.py`)에 정의된 라우트 함수가 매칭됩니다.
4.  **의존성 주입**: 라우트 함수에 정의된 의존성(예: `db_session`, `get_login_member`)들이 실행되어 필요한 객체나 데이터가 함수로 전달됩니다.
5.  **비즈니스 로직 처리**: 라우트 함수 내에서 핵심 비즈니스 로직이 수행됩니다. (예: 데이터베이스 조회/수정, 외부 API 호출, 데이터 가공 등)
6.  **템플릿 렌더링**: 필요한 경우, `core/template.py`에 설정된 Jinja2 템플릿 엔진을 사용하여 HTML 응답을 생성합니다. 컨텍스트 데이터가 템플릿으로 전달되어 동적으로 페이지가 구성됩니다.
7.  **응답 반환**: 생성된 HTML, JSON 또는 리디렉션 응답이 사용자에게 반환됩니다.

*   **사용자 인증**: 세션 기반으로 처리되며, 로그인 시 세션에 사용자 ID가 저장됩니다. `get_login_member` 의존성을 통해 현재 로그인한 사용자 정보를 가져옵니다.
*   **회원 정보 수정**: `/bbs/member_confirm`에서 비밀번호 확인 후, `/bbs/member_profile`에서 실제 정보 수정 폼을 보여주고, 폼 제출 시 저장 로직이 실행됩니다.

## 4. 환경 설정 (`.env`) 주요 내용

`.env` 파일은 프로젝트 루트에 위치하며, 주요 설정은 다음과 같습니다.

*   `DB_TABLE_PREFIX='g6_'`: 데이터베이스 테이블명의 접두사입니다.
*   `DB_ENGINE='postgresql'`: 사용 중인 데이터베이스 엔진입니다.
*   `DB_USER='postgres'`: PostgreSQL 데이터베이스 사용자 이름입니다.
*   `DB_PASSWORD='marketmaker'`: PostgreSQL 데이터베이스 비밀번호입니다.
*   `DB_HOST='38.242.139.223'`: PostgreSQL 데이터베이스 호스트 주소입니다.
*   `DB_PORT=5432`: PostgreSQL 데이터베이스 포트 번호입니다.
*   `DB_NAME='marketmaker'`: 사용 중인 데이터베이스 이름입니다.
*   `DB_CHARSET='utf8mb4'`: 데이터베이스 문자 인코딩 설정입니다.

## 5. 최근 주요 작업 내역: SUI 지갑 주소 연동 기능 추가

*   **목표**: 회원 정보 수정 페이지에서 사용자가 자신의 SUI 블록체인 지갑 주소를 입력하고 저장할 수 있도록 기능을 구현합니다. 저장된 주소는 향후 토큰 보상 등의 기능에 활용될 예정입니다.
*   **작업 과정 및 해결된 이슈**:
    1.  **UI 필드 추가**: `/home/ubuntu/suiboard/templates/bootstrap/member/register_form.html` 템플릿 파일에 SUI 지갑 주소를 입력받기 위한 `<input type="text" name="mb_sui_address" ...>` 필드를 추가했습니다. 이 필드는 기존 회원 정보 수정 폼의 '기타 개인설정' 섹션에 위치합니다.
    2.  **데이터 모델 수정**: `/home/ubuntu/suiboard/core/models.py` 파일의 `Member` SQLAlchemy 모델 클래스에 `mb_sui_address = Column(String(255), nullable=True, default="")` 필드를 추가하여 SUI 지갑 주소를 저장할 수 있도록 했습니다.
    3.  **데이터베이스 스키마 변경**: 실제 PostgreSQL 데이터베이스의 `g6_member` 테이블에 `mb_sui_address` 컬럼 (VARCHAR(255), NULL 허용, 기본값 빈 문자열)을 추가했습니다. 이 작업은 `/home/ubuntu/add_sui_column_to_db.py` 스크립트를 작성 및 실행하여 수행했습니다. 초기에는 스크립트의 `DB_TABLE_PREFIX` import 문제 및 경로 문제가 있었으나, 환경 변수에서 직접 읽어오도록 수정하여 해결했습니다.
    4.  **백엔드 저장 로직 확인**: `/home/ubuntu/suiboard/bbs/member_profile.py`의 `member_profile_save` 함수에서 `UpdateMemberForm`을 통해 전달된 `mb_sui_address` 값이 `member_service.update_member`를 통해 정상적으로 Member 객체에 반영되고 데이터베이스에 저장되는지 확인했습니다. `UpdateMemberForm` (`core/formclass.py`)에도 해당 필드가 포함되어야 합니다 (이 부분은 이전 작업에서 누락되었을 수 있으므로 확인 필요).
    5.  **데이터베이스 저장 값 검증**: `/home/ubuntu/check_admin_sui_address.py` 스크립트를 작성하여, 특정 사용자(예: 'admin')의 `mb_sui_address`가 데이터베이스에 올바르게 저장되었는지 직접 쿼리하여 검증했습니다. 초기에는 스크립트 실행 시 `core` 모듈 경로 문제, SQLite 연결 시도 문제 (실제 DB는 PostgreSQL), `Member` 모델에 `mb_sui_address` 속성 부재 오류 등이 발생했으나, PYTHONPATH 설정, `.env` 파일 명시적 로드, 모델 수정 후 재확인 등을 통해 해결했습니다.
    6.  **메인 페이지 접속 오류 해결**: 작업 도중 간헐적으로 메인 페이지 접속 불가 또는 'server address in use already' 오류가 발생했습니다. 이는 uvicorn 서버 프로세스가 중복 실행되거나 포트가 정상적으로 해제되지 않아 발생한 문제로, `sudo lsof -t -i:PORT | xargs -r sudo kill -9` 명령으로 기존 프로세스를 완전히 종료하고 서버를 재시작하여 해결했습니다.
*   **현재 상태**: `Member` 모델과 `g6_member` DB 테이블에 `mb_sui_address` 컬럼이 성공적으로 추가되었으며, 사용자가 정보 수정 페이지에서 입력한 SUI 지갑 주소가 데이터베이스에 정상적으로 저장되는 것을 확인했습니다. 템플릿(`register_form.html`)에도 해당 값을 표시하기 위한 `value="{{ member.mb_sui_address|default('', true) }}"` 바인딩이 되어 있습니다.

## 6. 향후 참고 사항 (Notes for Next AI)

*   **정보 수정 화면 글자 겹침 현상**: 사용자가 제공한 스크린샷에서 정보 수정 화면의 'SUI 지갑 주소' 입력 필드 레이블과 플레이스홀더 텍스트가 겹쳐 보이는 CSS 스타일 문제가 있습니다. `/home/ubuntu/suiboard/templates/bootstrap/member/register_form.html` 또는 관련 CSS 파일에서 해당 요소의 스타일(예: `padding`, `margin`, `line-height`, `position` 등)을 조정하여 해결해야 합니다.
*   **정보 수정 화면 SUI 주소 미표시 (간헐적)**: 데이터베이스에는 주소가 정상적으로 저장되어 있음에도 불구하고, 정보 수정 화면을 다시 방문했을 때 간혹 SUI 지갑 주소가 입력 필드에 표시되지 않는다는 사용자 피드백이 있었습니다. 이는 다음 가능성을 점검해볼 필요가 있습니다:
    *   **브라우저/서버 캐시**: 캐시로 인해 이전 데이터가 표시될 수 있습니다. 브라우저 캐시 삭제 및 서버 재시작 후 확인이 필요합니다.
    *   **데이터 로딩 시점/누락**: `/home/ubuntu/suiboard/bbs/member_profile.py`의 `member_profile` 라우트 함수가 회원 정보를 조회하여 템플릿으로 전달할 때, `mb_sui_address` 필드가 포함된 최신 `Member` 객체가 전달되는지 확인해야 합니다. 현재 로직상으로는 문제가 없어 보이지만, 데이터 흐름을 다시 한번 면밀히 검토할 필요가 있습니다.
    *   **폼 데이터 클래스**: `core/formclass.py`의 `UpdateMemberForm`에 `mb_sui_address: Optional[str] = None` (또는 적절한 타입) 필드가 명시적으로 정의되어 있는지 확인해야 합니다. FastAPI가 폼 데이터를 파싱하고 검증할 때 이 클래스를 사용하므로, 필드가 누락되면 데이터가 제대로 처리되지 않을 수 있습니다.
*   **DB 마이그레이션 도구**: 현재 데이터베이스 스키마 변경은 수동 스크립트(`add_sui_column_to_db.py`)로 관리되고 있습니다. 향후 프로젝트 규모가 커지거나 협업이 필요할 경우, Alembic과 같은 SQLAlchemy 기반의 데이터베이스 마이그레이션 도구를 도입하여 스키마 변경 이력을 체계적으로 관리하는 것을 권장합니다.
*   **로깅 강화**: `sui_integration.log` 외에도 애플리케이션 전반의 주요 이벤트 및 오류에 대한 로깅을 강화하여 디버깅 및 유지보수 효율성을 높일 수 있습니다.

이 문서가 다음 작업자에게 도움이 되기를 바랍니다.

## 7. SUI CLI 설치 및 설정 가이드 (Ubuntu 서버)
SUI 바이너리 다운로드 경로 확인 및 다운로드:
Sui 공식 GitHub 릴리스 페이지(https://github.com/MystenLabs/sui/releases )에서 최신 버전의 Linux용 바이너리(sui-mainnet-linux-amd64-vX.Y.Z.tgz 또는 sui-testnet-linux-amd64-vX.Y.Z.tgz 형태, 현재 사용하시는 네트워크에 맞는 버전을 선택하세요. SUIBOARD 토큰 및 패키지가 배포된 네트워크와 일치해야 합니다)의 다운로드 링크를 복사합니다.
서버에서 다음 명령어를 사용하여 다운로드합니다 (예시 링크이므로 실제 링크로 대체해야 합니다):
bash
wget https://github.com/MystenLabs/sui/releases/download/mainnet-v1.20.0/sui-mainnet-linux-amd64-v1.20.0.tgz -O sui-binaries.tgz
바이너리 압축 해제 및 이동:
다운로드한 파일의 압축을 해제합니다:
bash
tar -xzf sui-binaries.tgz
압축 해제 후 생성된 폴더 (예: sui-mainnet-linux-amd64-v1.20.0) 안에 sui 실행 파일이 있는지 확인합니다.
sui_integration.py 스크립트에서는 SUI 바이너리 경로를 /home/ubuntu/sui_bin으로 예상하고 있습니다. 이 경로에 sui 실행 파일을 위치시키거나, 스크립트 내의 SUI_BIN_PATH 변수를 실제 sui 파일이 있는 경로로 수정해야 합니다. /home/ubuntu/sui_bin 경로를 사용하려면 다음처럼 디렉토리를 만들고 파일을 옮깁니다:
bash
mkdir -p /home/ubuntu/sui_bin
# 예: 압축 해제된 폴더가 sui-mainnet-linux-amd64-v1.20.0 이고 그 안에 sui 파일이 있다면
cp sui-mainnet-linux-amd64-v1.20.0/sui /home/ubuntu/sui_bin/
sui 파일에 실행 권한을 부여합니다:
bash
chmod +x /home/ubuntu/sui_bin/sui
SUI Client 환경 설정 (네트워크 연결):
SUI CLI가 올바른 네트워크(예: testnet, devnet, mainnet)를 바라보도록 설정해야 합니다. SUIBOARD 토큰이 배포된 네트워크를 사용해야 합니다.
다음 명령어를 사용하여 사용 가능한 환경을 확인하고, 원하는 환경으로 전환합니다. (예: testnet으로 전환)
bash
/home/ubuntu/sui_bin/sui client envs
/home/ubuntu/sui_bin/sui client switch --env testnet 
(또는 mainnet, devnet 등 실제 사용하는 네트워크명)
활성 주소가 있는지, 네트워크에 연결되었는지 확인합니다. 필요하다면 주소를 생성하거나 가져와야 합니다. 이 주소는 토큰 발행 트랜잭션의 가스비를 지불하는 데 사용됩니다.
bash
/home/ubuntu/sui_bin/sui client active-address
만약 주소가 없다면, sui client new-address ed25519 (또는 secp256k1) 명령으로 새 주소를 만들거나, sui keytool import "<YOUR_PRIVATE_KEY_MNEMONIC>" ed25519 (또는 secp256k1) 명령으로 기존 지갑을 가져올 수 있습니다. 새 주소를 만들었다면 해당 주소에 가스 토큰(SUI)이 필요합니다.
애플리케이션 스크립트 확인 (sui_integration.py):
/home/ubuntu/suiboard/sui_integration.py 파일 내의 다음 상수들이 현재 SUI 환경 및 배포된 패키지 정보와 일치하는지 다시 한번 확인하십시오:
SUI_BIN_PATH = "/home/ubuntu/sui_bin" (위에서 설정한 경로와 일치해야 함)
TOKEN_PACKAGE_ID: SUIBOARD 토큰 패키지의 실제 ID여야 합니다.
TOKEN_TREASURY_CAP_ID: SUIBOARD 토큰의 TreasuryCap 오브젝트 ID여야 합니다.
GAS_BUDGET: 적절한 가스 예산으로 설정되어 있어야 합니다.
이 값들은 토큰을 발행(publish)할 때 얻을 수 있는 정보입니다.
테스트:
모든 설정이 완료되면, suiboard 애플리케이션에서 게시글을 작성하여 토큰이 정상적으로 지급되는지 테스트합니다.
sui_integration.log 파일에서 오류 없이 토큰 발행(mint) 관련 로그가 성공적으로 기록되는지 확인합니다. 성공 시 "Transaction Digest:" 와 함께 트랜잭션 ID가 로그에 남아야 합니다.
SUI 익스플로러(예: Suiscan, Suivision 등 사용하는 네트워크에 맞는 익스플로러)에서 해당 트랜잭션 ID로 실제 트랜잭션 내용을 확인하거나, 수신자 지갑 주소의 토큰 잔액 변동을 확인합니다.
중요 사항:
네트워크 일치: SUI CLI가 연결된 네트워크, TOKEN_PACKAGE_ID, TOKEN_TREASURY_CAP_ID는 모두 SUIBOARD 토큰이 실제로 배포되고 운영되는 동일한 SUI 네트워크(mainnet, testnet, devnet 중 하나)를 기준으로 해야 합니다.
가스비: 토큰 발행 트랜잭션에는 가스비(SUI 토큰)가 소모됩니다. SUI CLI에 연결된 활성 주소에는 충분한 SUI 토큰이 있어야 합니다.
권한: sui 바이너리 실행 및 로그 파일 작성 등에 필요한 파일 시스템 권한이 애플리케이션 실행 사용자에게 주어져야 합니다.


## 8. 추가된 주요 작업 내역: zkLogin Google 연동 및 신규 사용자 자동 등록 (Sui Testnet 기반)

*   **목표**: 기존 로그인 방식에 더하여, 사용자가 Google 계정을 통해 Sui zkLogin을 사용하여 로그인할 수 있도록 기능을 구현합니다. 신규 사용자의 경우 자동으로 계정이 생성되며, 기존 사용자는 Google 계정과 연동됩니다. 모든 기능은 Sui Testnet 환경을 기준으로 개발 및 설정되었습니다.
*   **주요 변경 및 추가 파일**:
    1.  **로그인 UI 수정**: `/home/ubuntu/suiboard/templates/bootstrap/social/social_login.html` 파일의 기존 소셜 로그인 섹션에 "Login with Google (zkLogin)" 버튼을 추가했습니다.
    2.  **프론트엔드 zkLogin 핸들러 추가**: `/home/ubuntu/suiboard/templates/bootstrap/static/js/zklogin_handler.js` 파일을 신규 생성했습니다.
        *   Sui SDK 함수들 (Ed25519Keypair, SuiClient, getFullnodeUrl, generateNonce, generateRandomness, jwtToAddress, fromB64 등)을 CDN ESM 모듈 방식으로 임포트하여 사용합니다.
        *   Google OAuth 2.0 인증 흐름을 시작하고, 인증 후 콜백을 처리하여 ID 토큰을 백엔드로 전송하는 로직을 포함합니다.
        *   Sui 네트워크는 **Testnet** (`SUI_NETWORK = 'testnet'`)으로 설정되어 있습니다.
        *   사용자는 이 파일 내의 `GOOGLE_CLIENT_ID` 플레이스홀더를 실제 Google Cloud Console에서 발급받은 클라이언트 ID로 교체해야 합니다.
        *   리디렉션 URI는 `window.location.origin + "/auth/zklogin/callback"`으로 설정되어 있습니다.
    3.  **베이스 템플릿 수정**: `/home/ubuntu/suiboard/templates/bootstrap/base.html` 파일의 `<body>` 태그 하단에 `zklogin_handler.js`를 모듈 타입으로 포함시켰습니다.
    4.  **백엔드 zkLogin 라우터 추가**: `/home/ubuntu/suiboard/bbs/zklogin.py` 파일을 신규 생성했습니다.
        *   FastAPI APIRouter를 사용하여 `/api/zklogin/authenticate` 엔드포인트를 정의합니다.
        *   프론트엔드에서 전달받은 JWT(ID 토큰)를 Google 공개키를 사용하여 검증합니다.
        *   Mysten Labs의 Salt Service (`https://salt.api.mystenlabs.com/get_salt`)를 호출하여 사용자별 Salt 값을 가져옵니다.
        *   **신규 사용자 자동 등록 및 계정 연동**: 
            *   먼저 JWT의 `sub` (Google 사용자 고유 ID) 값을 기준으로 `Member` 테이블에서 `mb_google_sub` 필드와 일치하는 사용자를 찾습니다.
            *   일치하는 사용자가 없으면, JWT의 이메일 주소를 기준으로 `Member` 테이블에서 `mb_email` 필드와 일치하는 사용자를 찾습니다. 해당 사용자가 존재하고 `mb_google_sub` 필드가 비어있으면, 현재 Google `sub` 값으로 업데이트하여 계정을 연동합니다.
            *   위 두 경우 모두 해당 사용자가 없으면 신규 사용자로 판단하여 `Member` 테이블에 새 레코드를 생성합니다.
                *   `mb_id`: `gg_` 접두사와 Google `sub` 값의 일부를 조합하여 생성 (중복 시 UUID 일부 추가).
                *   `mb_password`: 임의의 강력한 해시값으로 설정 (실제 비밀번호 로그인 불가, zkLogin 전용).
                *   `mb_name`, `mb_nick`: JWT에서 가져온 이름 또는 이메일 기반으로 설정.
                *   `mb_email`: JWT에서 가져온 이메일 주소.
                *   `mb_level`: `config` 테이블의 `cf_register_level` 값 또는 기본값(2)으로 설정.
                *   `mb_certify`: "google_zklogin"으로 설정.
                *   `mb_email_certify`: 현재 시간으로 설정 (Google 인증 이메일로 간주).
                *   `mb_google_sub`: JWT의 `sub` 값 저장.
                *   기타 필수 필드들은 기본값 또는 JWT에서 파생된 값으로 채워집니다.
        *   사용자 인증(또는 생성) 성공 시, 기존 시스템과 동일하게 세션(`request.session["ss_mb_id"]`)을 설정합니다.
        *   사용자는 이 파일 내의 `GOOGLE_CLIENT_ID` 플레이스홀더를 실제 클라이언트 ID로 교체하거나, `GOOGLE_CLIENT_ID_ZKLOGIN` 환경 변수를 설정해야 합니다.
        *   Sui Testnet Prover URL (`https://prover-testnet.mystenlabs.com/v1`)이 참조용으로 코드 내에 명시되어 있습니다 (현재 백엔드에서 직접 ZK Proof를 생성하지는 않음).
    5.  **데이터 모델 수정**: `/home/ubuntu/suiboard/core/models.py` 파일의 `Member` SQLAlchemy 모델 클래스에 `mb_google_sub = Column(String(255), nullable=True, unique=True, index=True)` 필드를 추가했습니다. 이 필드는 Google 사용자의 고유 `sub` ID를 저장하여 계정 연동 및 식별에 사용됩니다.
        *   **DB 스키마 변경 필요**: 기존 운영 중인 데이터베이스에는 해당 컬럼이 없을 수 있습니다. 애플리케이션 실행 전 또는 최초 실행 시 `g6_member` (또는 설정된 접두사를 따르는 member 테이블)에 `mb_google_sub VARCHAR(255) NULL UNIQUE` 컬럼을 수동으로 추가하거나, SQLAlchemy의 마이그레이션 도구(예: Alembic, 현재 프로젝트에는 미적용)를 사용해야 합니다. 만약 새로운 DB에서 SQLAlchemy가 테이블을 자동 생성하는 환경이라면 이 필드가 포함되어 생성됩니다.
    6.  **메인 애플리케이션 라우터 등록**: `/home/ubuntu/suiboard/main.py` 파일에 위에서 생성한 `zklogin_router`를 FastAPI 앱에 포함시켜 API 엔드포인트가 정상적으로 동작하도록 수정했습니다.
*   **Sui Testnet 환경 설정**:
    *   프론트엔드 `zklogin_handler.js`의 `SUI_NETWORK` 상수가 `'testnet'`으로 설정되었습니다.
    *   백엔드 `zklogin.py`의 Prover URL 주석이 Testnet 기준으로 업데이트 되었습니다.
    *   사용자는 `suiboard` 토큰 및 관련 SUI 패키지 ID들이 **Sui Testnet**에 배포되어 있고, 애플리케이션 설정(필요한 경우 `sui_integration.py` 등)이 Testnet 환경에 맞게 구성되어 있는지 확인해야 합니다.
*   **사용자 설정 및 테스트 필수 사항**:
    1.  **Google Cloud 프로젝트 및 OAuth 2.0 클라이언트 ID 생성**: 사용자 본인의 Google Cloud Console에서 새 프로젝트를 생성하고, OAuth 2.0 클라이언트 ID를 발급받아야 합니다.
    2.  **클라이언트 ID 설정**: 위 "주요 변경 및 추가 파일" 항목에 명시된 대로 프론트엔드(`zklogin_handler.js`)와 백엔드(`zklogin.py` 또는 환경변수) 양쪽에 발급받은 클라이언트 ID를 정확히 설정해야 합니다.
    3.  **승인된 JavaScript 원본 및 리디렉션 URI 설정**: Google Cloud Console의 OAuth 2.0 클라이언트 ID 설정에서 "승인된 JavaScript 원본" (예: `http://localhost:8000` 또는 실제 배포된 도메인)과 "승인된 리디렉션 URI" (예: `http://localhost:8000/auth/zklogin/callback`)를 정확히 설정해야 합니다. 리디렉션 URI는 `zklogin_handler.js`의 `REDIRECT_URI`와 일치해야 합니다.
    4.  **데이터베이스 `mb_google_sub` 컬럼 확인/추가**: 위 "데이터 모델 수정" 항목에 설명된 대로 `Member` 테이블에 `mb_google_sub` 컬럼이 존재하는지 확인하고, 없다면 추가해야 합니다.
    5.  **전체 흐름 테스트 (Testnet)**: 모든 설정 완료 후, 애플리케이션을 실행하고 로그인 팝업에서 "Login with Google (zkLogin)" 버튼을 클릭하여 다음 시나리오를 포함한 전체 인증 흐름을 Sui Testnet 환경에서 테스트해야 합니다.
        *   완전히 새로운 Google 계정으로 로그인 시 신규 회원 자동 가입.
        *   기존에 이메일로 가입된 사용자가 해당 Google 계정으로 최초 로그인 시 계정 연동 (mb_google_sub 필드 채워짐).
        *   이미 연동된 Google 계정으로 로그인.
*   **향후 개선 가능성**: 현재는 `mb_id`를 `gg_` 접두사로 생성하고, 패스워드는 임의값으로 설정합니다. 사용자 경험을 위해 닉네임 중복 처리, 초기 설정 페이지 안내 등의 기능을 추가할 수 있습니다.
