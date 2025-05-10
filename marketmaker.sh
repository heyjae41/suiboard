#!/bin/bash

# suiboard 프로젝트 업데이트 및 재시작 스크립트
# 작성자: AI Assistant
# 작성일: 2024-03-21

# 스크립트 실행 시 오류 발생하면 즉시 중단
set -e

# 로그 출력 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# 에러 로그 출력 함수
error_log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >&2
}

# OS 확인 및 작업 디렉토리 설정
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    PROJECT_DIR="C:/suiboard"  # 윈도우 환경
    log "윈도우 환경이 감지되었습니다. 프로젝트 경로: $PROJECT_DIR"
    PYTHON_CMD="python"
    VENV_ACTIVATE="$PROJECT_DIR/.venv/Scripts/activate"
else
    PROJECT_DIR="/home/root/suiboard"  # 기타 OS (Linux, macOS 등)
    log "유닉스 계열 환경이 감지되었습니다. 프로젝트 경로: $PROJECT_DIR"
    PYTHON_CMD="python3"
    VENV_ACTIVATE="$PROJECT_DIR/.venv/bin/activate"
fi
cd $PROJECT_DIR

# 1. 현재 작업 중인 변경사항 저장
log "현재 작업 중인 변경사항 저장..."
if git status --porcelain | grep -q .; then
    git stash
    log "변경사항이 스태시되었습니다."
else
    log "저장할 변경사항이 없습니다."
fi

# 2. main 브랜치로 전환
log "main 브랜치로 전환..."
git checkout main

# 3. 원격 저장소의 최신 변경사항 가져오기
log "원격 저장소에서 최신 변경사항 가져오기..."
git fetch origin

# 4. 원격 저장소의 변경사항 적용
log "원격 저장소의 변경사항 적용..."
git pull origin main

# 5. 스태시한 변경사항 복원
log "스태시한 변경사항 복원..."
if git stash list | grep -q .; then
    git stash pop
    log "스태시한 변경사항이 복원되었습니다."
else
    log "복원할 스태시가 없습니다."
fi

# 6. Python 가상환경 확인 및 설정
log "Python 가상환경 확인 및 설정..."
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    log "가상환경이 존재하지 않습니다. 새로운 가상환경을 생성합니다..."
    $PYTHON_CMD -m venv .venv
    log "가상환경이 생성되었습니다."
else
    log "기존 가상환경을 사용합니다."
fi

# 7. 가상환경 활성화 및 의존성 패키지 업데이트
log "가상환경 활성화 및 의존성 패키지 업데이트..."
source $VENV_ACTIVATE
pip install --upgrade pip
pip install -r requirements.txt
log "의존성 패키지 설치가 완료되었습니다."

# 8. 데이터베이스 마이그레이션
log "데이터베이스 마이그레이션 실행..."
alembic upgrade head

# 9. 기존 서비스 중지
log "기존 서비스 중지..."
if pgrep -f "uvicorn main:app" > /dev/null; then
    pkill -f "uvicorn main:app"
    log "기존 서비스가 중지되었습니다."
else
    log "실행 중인 서비스가 없습니다."
fi

# 10. 서비스 재시작
log "서비스 재시작..."
nohup $PROJECT_DIR/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 > suiboard.log 2>&1 &

# 11. 서비스 상태 확인
sleep 5
if pgrep -f "uvicorn main:app" > /dev/null; then
    log "서비스가 성공적으로 재시작되었습니다."
    log "로그 파일: $PROJECT_DIR/suiboard.log"
else
    error_log "서비스 재시작 실패"
    exit 1
fi

log "모든 작업이 완료되었습니다." 