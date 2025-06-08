from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import csv
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from telethon.errors import SessionPasswordNeededError
import schedule
import time
import sys

# Add project root to sys.path to allow importing project modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

# 환경 변수 로드
load_dotenv()

# API 정보
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

# Configuration
CHANNEL_USERNAME = "coinnesskr"# 채널 정보 https://t.me/coinnesskr
BOARD_TABLE_NAME = "blockchain"  # Target board table (bo_table)
AGENT_MEMBER_ID = "AINewsAgent" # Member ID for the agent
AGENT_MEMBER_NICKNAME = "AINewsAgent"

last_processed_message_id = None

# --- Database Setup --- #
def get_db():
    from core.database import db_connect
    db = db_connect.sessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_telegram_client():
    """텔레그램 클라이언트 생성 및 인증"""
    client = TelegramClient("insider_session", api_id, api_hash)
    client.connect()

    if not client.is_user_authorized():
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input("텔레그램으로 받은 코드 입력: "))
        except SessionPasswordNeededError:
            client.sign_in(password=input("2단계 인증 비밀번호 입력: "))

    return client


def process_message(message):
    """메시지 처리 및 게시판에 포스팅"""
    try:
        # 메시지 내용 구성
        content = message.text

        # 필터링할 메시지 패턴
        skip_patterns = [
            "안녕하세요 구독자님들",
            "안녕하세요 여러분",
            "안녕하세요",
            "구독자 여러분",
            r"^안녕하세요.*님들$",  # "안녕하세요"로 시작하고 "님들"로 끝나는 정규표현식 패턴
            r"^안녕하세요.*여러분$",  # "안녕하세요"로 시작하고 "여러분"으로 끝나는 정규표현식 패턴
            # 기타 필터링하고 싶은 패턴들...
        ]

        # 필터링 패턴 체크
        if any(message.text.startswith(pattern) for pattern in skip_patterns):
            print(f"필터링된 메시지: {message.text[:50]}...")
            return False

        # 이미지가 있는 경우 URL 추가
        if message.media:
            if hasattr(message.media, "photo"):
                # 이미지 정보 가져오기
                photo = message.media.photo
                # 이미지 있음을 표시
                content += "\n\n[이미지가 포함된 메시지입니다]"

            elif hasattr(message.media, "document"):
                # 문서 파일 정보
                doc = message.media.document
                content += f"\n\n[파일 정보: {doc.mime_type}]"
                if hasattr(doc, "file_name"):
                    content += f"\n파일명: {doc.file_name}"

        # 시간 변환 (UTC -> KST)
        kst_time = message.date + timedelta(hours=9)
        
        # 게시판에 포스팅할 데이터 구성
        article_title = f"코인니스 트래킹 ({kst_time.strftime('%Y-%m-%d %H:%M')})"
        
        # telegram_insider_agent.py와 동일한 구조로 create_post_by_agent 사용
        try:
            from core.database import db_connect
            from service.agent_service import create_post_by_agent
            
            db_session_gen = get_db()
            db = next(db_session_gen)
            
            new_post = create_post_by_agent(
                db=db,
                bo_table=BOARD_TABLE_NAME,
                mb_id=AGENT_MEMBER_ID,
                wr_subject=article_title,
                wr_content=content,
                wr_link1="",  # 텔레그램 메시지는 링크가 없음
                wr_name=AGENT_MEMBER_NICKNAME,
                wr_ip="127.0.0.1"  # Placeholder IP for agent
            )
            print(f"게시글 작성 성공 - ID: {new_post.wr_id}, 제목: {new_post.wr_subject}")
            db.close()
            time.sleep(60)  # 1분 대기
            return True
            
        except Exception as e:
            print(f"게시글 작성 실패 '{article_title}': {e}")
            return False

    except Exception as e:
        print(f"메시지 처리 중 오류 발생: {str(e)}")
        return False


def process_telegram_messages():
    """텔레그램 채널의 메시지 처리"""
    global last_processed_message_id

    try:
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 텔레그램 메시지 처리 시작"
        )
        client = get_telegram_client()

        # 채널 정보 가져오기
        channel = client.get_entity(CHANNEL_USERNAME)

        # 마지막으로 처리한 메시지 이후의 메시지 가져오기
        messages = client.get_messages(
            channel,
            limit=50,  # 한 번에 가져올 메시지 수
            min_id=last_processed_message_id if last_processed_message_id else 0,
        )

        if messages:
            # 메시지 처리
            for message in messages:
                if process_message(message):
                    last_processed_message_id = message.id

            print(f"처리된 메시지 수: {len(messages)}")
        else:
            print("새로운 메시지가 없습니다.")

        client.disconnect()
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 텔레그램 메시지 처리 완료"
        )
    except Exception as e:
        print(f"텔레그램 메시지 처리 중 오류 발생: {str(e)}")


def setup_schedule():
    """스케줄 설정"""
    # 매시 10분에 실행
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 스케줄러 설정: 매시 10분마다 실행"
    )
    job = schedule.every().hour.at(":10").do(process_telegram_messages)
    next_run = schedule.next_run()
    if next_run:
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 다음 예정된 실행 시간: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
        )
    else:
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 경고: 다음 실행 시간을 가져올 수 없습니다."
        )

    # 초기 실행
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 초기 실행 시작")
    process_telegram_messages()
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 초기 실행 완료")


def run_scheduler():
    """스케줄러 실행"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 스케줄러 루프 시작")
    while True:
        schedule.run_pending()

        # 매 10분마다 스케줄러 상태 로깅
        if datetime.now().minute % 10 == 0 and datetime.now().second == 0:
            next_run = schedule.next_run()
            if next_run:
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 다음 예정된 실행 시간: {next_run.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                print(
                    f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 경고: 다음 실행 시간을 가져올 수 없습니다."
                )

        time.sleep(1)


def main():
    """메인 함수"""
    try:
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 텔레그램 코인니스 트래킹 봇 시작..."
        )
        setup_schedule()
        run_scheduler()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 프로그램 종료")
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 오류 발생: {str(e)}")


if __name__ == "__main__":
    main()
