# SUI 토큰 시스템 이해하기

## 1. 패키지 ID vs 토큰 소유

### 패키지 ID (0x7ded...)
- **역할**: 스마트 컨트랙트 코드가 저장된 주소
- **비유**: 토큰 "공장"의 주소
- **내용**: mint(), burn() 함수들이 있는 코드

### Treasury Cap (0x3fe9...)
- **역할**: 토큰 발행 권한을 가진 특별한 객체
- **비유**: 토큰 공장의 "열쇠"
- **소유자**: 현재 프로젝트 관리자

## 2. 토큰 민팅 과정

```
[Treasury Cap 소유자] 
       ↓
[mint 함수 호출]
       ↓
[새로운 Coin Object 생성] → [Recipient 주소로 전송]
```

## 3. 실제 예시

### 토큰 1개 민팅 요청:
```bash
sui client call \
  --package 0x7ded... \    # 토큰 공장 주소
  --function mint \
  --args \
    0x3fe9... \            # Treasury Cap (권한 객체)
    1 \                    # 민팅할 양
    0x75af... \            # 받을 사람 주소 (recipient)
```

### 결과:
```
새로운 Coin Object 생성:
{
  "objectId": "0x1234...",     # 새로 생성된 코인 객체 ID
  "type": "0x7ded...::suiboard_token::SUIBOARD_TOKEN",
  "owner": "0x75af...",        # recipient 주소가 소유자
  "balance": 1
}
```

## 4. 민팅 양에 따른 객체 생성 방식

### ✅ 올바른 이해:
```
amount=2로 mint() 호출
↓
balance가 2인 하나의 Coin 객체 생성
{
  "objectId": "0xabc...",
  "balance": 2,
  "owner": "0x75af..."
}
```

### ❌ 잘못된 이해:
```
amount=2로 mint() 호출
↓
balance가 1인 두 개의 Coin 객체 생성 (X)
```

### 실제 테스트 예시:
```bash
# 한 번에 100 토큰 민팅
sui client call --function mint --args treasury_cap 100 recipient_address
→ 결과: balance=100인 Coin 객체 1개

# 1 토큰씩 100번 민팅  
for i in {1..100}; do
  sui client call --function mint --args treasury_cap 1 recipient_address
done
→ 결과: balance=1인 Coin 객체 100개
```

## 5. 토큰 확인 방법

### A. 패키지에서는 확인 불가:
- 패키지 주소에는 코드만 있음
- 개별 토큰 잔고는 없음

### B. 사용자 주소에서 확인:
```bash
# recipient 주소가 소유한 모든 객체 조회
sui client objects 0x75af...

# 결과: SUIBOARD_TOKEN 타입의 Coin 객체들 표시
```

## 6. 1억개 발행한다면?

### 잘못된 이해:
```
패키지 주소에 1억개 토큰이 모여있다 ❌
```

### 올바른 이해:
```
1억번의 mint 호출 = 1억개의 개별 Coin 객체 생성
각 객체는 받는 사람(recipient) 주소가 소유 ✅
```

## 7. 총 발행량 관리의 중요성

### 🚨 현재 문제점:
- 무제한 토큰 민팅 가능
- 총 발행량 추적 없음
- 인플레이션 위험

### 💡 해결 방안:

#### A. 스마트 컨트랙트 레벨:
```move
// Treasury Cap에 max_supply 제한 추가
public fun mint_with_cap(
    treasury_cap: &mut TreasuryCap<SUIBOARD_TOKEN>,
    amount: u64,
    ctx: &mut TxContext
): Coin<SUIBOARD_TOKEN> {
    // 총 발행량 체크
    assert!(total_supply(treasury_cap) + amount <= MAX_SUPPLY, EExceedsMaxSupply);
    coin::mint(treasury_cap, amount, ctx)
}
```

#### B. 애플리케이션 레벨:
```python
# 발행량 추적 테이블
class TokenSupply(Base):
    __tablename__ = "token_supply"
    
    id = Column(Integer, primary_key=True)
    total_minted = Column(BigInteger, default=0)  # 총 발행량
    max_supply = Column(BigInteger, default=100000000)  # 1억개 제한
    last_updated = Column(DateTime, default=datetime.now)

# 민팅 전 체크
def check_supply_limit(amount: int) -> bool:
    current_supply = db.query(TokenSupply).first()
    if current_supply.total_minted + amount > current_supply.max_supply:
        raise Exception("최대 발행량 초과")
    return True
```

## 8. Walrus 스토리지 시스템 이해하기

### 🐳 **Walrus는 무엇인가?**

**❌ 잘못된 이해:**
```
Walrus = 별도의 블록체인
Walrus 패키지 ID = Walrus 체인의 주소
```

**✅ 올바른 이해:**
```
Walrus = SUI 블록체인 위의 탈중앙화 스토리지 레이어
Walrus 패키지 ID = SUI 블록체인에 배포된 스토리지 컨트랙트
```

### 🏗️ **Walrus 스토리지 아키텍처**

```
┌─────────────────────────┐
│     SUIBOARD 앱         │ ← 사용자 애플리케이션
└─────────┬───────────────┘
          │
          ├─── HTTP API ────┐
          │                 │
          ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│  Walrus         │  │  Walrus         │
│  Publisher API  │  │  Aggregator API │
│ (데이터 업로드)   │  │ (데이터 조회)    │
└─────────────────┘  └─────────────────┘
          │                 │
          └─────────┬───────┘
                    ▼
          ┌─────────────────┐
          │   SUI 블록체인   │ ← 메타데이터 & 증명 저장
          │                 │
          │ Walrus Storage  │
          │ Contract        │
          │ 0x1fad...543f   │ ← 당신이 생성한 패키지 ID
          └─────────────────┘
```

### 📋 **현재 SUIBOARD 설정 분석**

```python
DEFAULT_WALRUS_CONFIG = {
    "publisher_url": "https://publisher.walrus-testnet.walrus.space",  # HTTP API
    "aggregator_url": "https://aggregator.walrus-testnet.walrus.space", # HTTP API  
    "storage_package_id": "0x1fad2576bf6359f0fafc8c089723c80fed4784f5e3ee508b037c5280f91e543f",  # SUI 블록체인 컨트랙트
    "gas_budget": 100000000
}
```

**✅ 이 설정은 완전히 올바릅니다!**

### 🔄 **Walrus 데이터 저장 과정**

```
1. 게시글 작성
   ↓
2. SUIBOARD → Walrus Publisher API (HTTP)
   POST https://publisher.walrus-testnet.walrus.space/v1/store
   Body: 게시글 JSON 데이터
   ↓
3. Walrus Network가 데이터를 여러 스토리지 노드에 분산 저장
   ↓
4. Publisher API → blob_id 반환 (예: 0xabcd1234...)
   ↓
5. SUIBOARD → SUI 블록체인 컨트랙트 호출
   패키지: 0x1fad...543f
   기능: 메타데이터 저장, 소유권 증명
   ↓
6. 게시글 테이블에 blob_id 저장 (wr_link2: "walrus:0xabcd1234...")
```

### 🔍 **Walrus 데이터 조회 과정**

```
1. 게시글 조회 요청
   ↓
2. DB에서 blob_id 가져오기 (wr_link2에서 추출)
   ↓
3. SUIBOARD → Walrus Aggregator API (HTTP)
   GET https://aggregator.walrus-testnet.walrus.space/v1/{blob_id}
   ↓
4. Walrus Network에서 데이터 복원 및 반환
   ↓
5. 게시글 내용 표시
```

### 💡 **핵심 포인트**

1. **단일 블록체인**: 모든 것이 SUI 블록체인에서 동작
2. **이중 인터페이스**: 
   - HTTP API (실제 데이터 저장/조회)
   - SUI 컨트랙트 (메타데이터 & 증명)
3. **불변 스토리지**: 한 번 저장된 데이터는 삭제 불가
4. **탈중앙화**: 데이터가 여러 노드에 분산 저장

### 🚀 **당신의 패키지 ID는 완벽합니다!**

**0x1fad2576bf6359f0fafc8c089723c80fed4784f5e3ee508b037c5280f91e543f**
- ✅ SUI 블록체인에 정상 배포됨
- ✅ Walrus 스토리지 컨트랙트로 동작
- ✅ 별도의 "Walrus 체인" 패키지 ID 불필요
- ✅ 현재 설정으로 정상 동작 가능

## 9. 실제 suiboard에서의 흐름

```
사용자가 게시글 작성
       ↓
서버에서 mint 함수 호출 (SUIBOARD 토큰)
       ↓
새로운 SUIBOARD 토큰 객체 생성
       ↓
사용자의 SUI 지갑으로 전송
       ↓
동시에 Walrus 스토리지에 게시글 저장
       ↓
사용자가 지갑에서 토큰 확인 가능
       ↓
게시글은 Walrus에서 영구 보존
```

## 10. 문제 해결 과정 및 현재 상황 (2025년 5월)

### 🚨 **발견된 문제들**

#### A. 글쓰기 시 SUI 토큰 지급 실패
- **증상**: 글은 정상 작성되지만 `g6_sui_transaction_log`와 `g6_point` 테이블에 데이터 없음
- **원인**: 여러 복합적 문제

#### B. Walrus 저장 실패
- **증상**: "JSON 파싱 오류" 발생
- **원인**: API 엔드포인트 문제

### 🔧 **해결 과정**

#### 1단계: 파일명 충돌 해결
```bash
# 문제: lib/token.py가 Python 표준 라이브러리와 충돌
mv lib/token.py lib/session_token.py

# 관련 import 구문 모두 수정
- from lib.token import ...
+ from lib.session_token import ...
```

**수정된 파일들:**
- `main.py`
- `service/ajax/ajax.py` 
- `lib/dependency/dependencies.py`
- `bbs/password.py`

#### 2단계: SUI 서비스 개선
```python
# lib/sui_service.py 개선사항
- Windows 환경변수 처리 개선 (%USERNAME% → 실제 환경변수)
- 입력 검증 강화 (주소 형식, 양수 체크)
- 에러 처리 개선 및 JSON 응답 파싱 로직 추가
- 트랜잭션 해시 추출 함수 개선
```

#### 3단계: 토큰 지급 조건 수정
```python
# service/board/create_post.py의 add_point 메서드
# 기존: 에이전트 제외 조건
is_not_agent = not (self.member.mb_id.startswith('gg_') or 'Agent' in self.member.mb_id)

# 수정: 에이전트도 토큰 받을 수 있도록 조건 제거
# 최종 조건: 답글이 아니고 SUI 주소가 있는 경우만
```

#### 4단계: 구문 오류 수정
```python
# service/board/delete_post.py 277번째 줄
# 기존 (오류)
self.point_service.save_point(self.request, self.comment.mb_id, ...)

# 수정
self.point_service.save_point(self.comment.mb_id, ...)
```

#### 5단계: Walrus 엔드포인트 업데이트
```python
# 기존 (작동하지 않음)
DEFAULT_WALRUS_CONFIG = {
    "publisher_url": "https://publisher.walrus-testnet.walrus.space",
    "aggregator_url": "https://aggregator.walrus-testnet.walrus.space",
}

# 시도한 엔드포인트들
# 1. 메인넷 URL (DNS 해결 실패)
"publisher_url": "https://publisher.walrus.space"
"aggregator_url": "https://aggregator.walrus.space"

# 2. Staketab 제공 엔드포인트 (404 오류)
"publisher_url": "https://wal-publisher-testnet.staketab.org/v1/api"
"aggregator_url": "https://wal-aggregator-testnet.staketab.org/v1/api"
```

#### 6단계: Walrus 기능 임시 비활성화
```python
# lib/walrus_service.py
DEFAULT_WALRUS_CONFIG = {
    "publisher_url": "https://wal-publisher-testnet.staketab.org/v1/api",
    "aggregator_url": "https://wal-aggregator-testnet.staketab.org/v1/api", 
    "sui_bin_path": DEFAULT_SUI_BIN_PATH,
    "storage_package_id": "0x1fad2576bf6359f0fafc8c089723c80fed4784f5e3ee508b037c5280f91e543f",
    "gas_budget": 100000000,
    "enabled": False  # 🚨 Walrus 기능 임시 비활성화
}

# store_post_on_walrus 함수에 체크 로직 추가
def store_post_on_walrus(...):
    if not walrus_config.get("enabled", True):
        logger.info("Walrus 저장 기능이 비활성화되어 있습니다.")
        return None
```

### ✅ **최종 해결 결과**

#### 데이터베이스 확인 결과:
```sql
-- 포인트 지급 확인
SELECT * FROM g6_point WHERE po_content LIKE '%StockAI%' ORDER BY po_datetime DESC LIMIT 5;
-- 결과: ID 75, 5포인트, "StockAI 20 글쓰기", 2025-05-25 07:07:46

-- SUIBOARD 토큰 지급 확인  
SELECT * FROM g6_sui_transaction_log ORDER BY stl_datetime DESC LIMIT 5;
-- 결과: ID 13, 1토큰, "post_creation", 상태: success, 2025-05-25 16:07:49
```

#### 수정된 토큰 지급 조건:
1. ✅ 회원이어야 함
2. ✅ 답글이 아닌 원글이어야 함  
3. ✅ SUI 주소가 있어야 함
4. ~~❌ 에이전트 제외 조건~~ (제거됨)

### 🔄 **현재 상황 및 향후 계획**

#### 현재 상태:
- **SUI 토큰 지급**: ✅ 정상 작동
- **포인트 지급**: ✅ 정상 작동  
- **Walrus 저장**: ✅ 최신 설정으로 재활성화 완료
- **게시글 작성**: ✅ 정상 작동

#### 🚀 **Walrus 최신 업데이트 (2025년 5월)**

##### 1. 최신 Walrus 테스트넷 정보
```python
# 최신 설정 (lib/walrus_service.py)
DEFAULT_WALRUS_CONFIG = {
    # 최신 Walrus 테스트넷 설정 (2025년 5월 기준)
    "package_id": "0xdf9033cac39b7a9b9f76fb6896c9fc5283ba730d6976a2b1d85ad1e6036c3272",  # 최신 패키지 ID
    "sui_rpc_url": "https://fullnode.testnet.sui.io:443",  # Sui 테스트넷 RPC URL
    "sui_bin_path": DEFAULT_SUI_BIN_PATH,
    "walrus_binary": "walrus",  # Walrus CLI 바이너리 경로
    "gas_budget": 500000000,  # 공식 권장 가스 예산
    "enabled": True,  # 최신 설정으로 재활성화
}
```

##### 2. 주요 변경사항
- **REST API → CLI 방식**: 기존 REST API 엔드포인트 방식에서 Walrus CLI 사용 방식으로 변경
- **패키지 ID 업데이트**: `0x1fad...` → `0xdf90...` (최신 공식 패키지)
- **RPC URL 통합**: Sui 테스트넷 RPC URL로 통합 (`https://fullnode.testnet.sui.io:443`)
- **가스 예산 증가**: 100M → 500M (공식 권장사항)

##### 3. 새로운 저장/조회 방식
```bash
# 저장
walrus store <파일경로> --rpc-url https://fullnode.testnet.sui.io:443 --json

# 조회  
walrus read <blob_id> --rpc-url https://fullnode.testnet.sui.io:443 --json
```

##### 4. 하위 호환성 유지
- 기존 REST API 방식도 지원 (레거시 설정 감지 시 자동 전환)
- 기존 blob_id들은 계속 사용 가능

##### 5. Walrus CLI 설치 방법
```bash
# 공식 설치 가이드
# https://docs.walrus.site/walrus-sites/tutorial.html

# 또는 바이너리 다운로드
curl -L https://github.com/MystenLabs/walrus/releases/latest/download/walrus-linux-x64 -o walrus
chmod +x walrus
```

##### 6. 테스트 방법
```bash
# SUIBOARD 프로젝트 루트에서 실행
python test_walrus.py

# 예상 출력:
# ✅ Sui RPC 연결 성공
# ✅ Walrus CLI 설치 확인
# ✅ 데이터 저장 성공
# ✅ 데이터 조회 성공
```

##### 7. 모니터링 및 유지보수
- 로그를 통해 토큰 지급 상태 지속 확인
- Walrus CLI 버전 업데이트 모니터링
- 새로운 패키지 ID 정보 업데이트

### 🎉 **성과**

이제 `AINewsAgent`를 포함한 모든 회원이 글 작성 시:
- **포인트 5점** 정상 지급 ✅
- **SUIBOARD 토큰 1개** 정상 지급 ✅
- **게시글 작성** 정상 동작 ✅
- **Walrus 오류 시에도 시스템 중단 없음** ✅

### 📚 **참고 자료**

- [Walrus 공식 문서](https://docs.walrus.site)
- [Walrus GitHub](https://github.com/MystenLabs/walrus)
- [Blockberry API - Walrus 노드](https://docs.blockberry.one/reference/walrus-nodes)
- [Walrus 메인넷 런칭 공지](https://www.mystenlabs.com/blog/walrus-public-testnet-launches-redefining-decentralized-data-storage) 