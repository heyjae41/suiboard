# /home/ubuntu/suiboard_project_v3/agent/rss_coindesk_agent.py
import feedparser
import datetime
import os
import sys
import logging
from bs4 import BeautifulSoup # To clean up HTML content from RSS summary

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # 콘솔 출력
        logging.FileHandler('agent/logs/rss_coindesk_agent.log', encoding='utf-8')  # 파일 출력
    ]
)
logger = logging.getLogger(__name__)

# Add project root to sys.path to allow importing project modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

logger.info(f"프로젝트 루트 경로: {PROJECT_ROOT}")
logger.info(f"sys.path에 추가됨: {PROJECT_ROOT}")

try:
    from sqlalchemy.orm import Session
    from core.database import db_connect
    from service.agent_service import create_post_by_agent
    from core.models import Member, Board # To check/create agent member and board
    logger.info("모든 모듈 임포트 성공")
except ImportError as e:
    logger.error(f"모듈 임포트 실패: {e}")
    sys.exit(1)

# Configuration
COINDESK_RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"
BOARD_TABLE_NAME = "blockchain"  # Target board table (bo_table)
AGENT_MEMBER_ID = "AINewsAgent" # Member ID for the agent
AGENT_MEMBER_NICKNAME = "AINewsAgent"

# --- Database Setup --- #
def get_db():
    db = db_connect.sessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helper function to ensure agent member and board exist --- #
def ensure_agent_setup(db: Session):
    # 1. Ensure agent member exists
    agent_member = db.query(Member).filter(Member.mb_id == AGENT_MEMBER_ID).first()
    if not agent_member:
        logger.info(f"에이전트 멤버 {AGENT_MEMBER_ID}를 찾을 수 없습니다. 생성 중...")
        new_agent = Member(
            mb_id=AGENT_MEMBER_ID,
            mb_password="!impossible_password_hash", 
            mb_name=AGENT_MEMBER_NICKNAME,
            mb_nick=AGENT_MEMBER_NICKNAME,
            mb_email=f"{AGENT_MEMBER_ID}@example.com",
            mb_level=2, 
            mb_mailling=0,
            mb_open=0,
            mb_email_certify=datetime.datetime.now(),
            mb_datetime=datetime.datetime.now(),
            mb_ip = "0.0.0.0",
            mb_leave_date = "",
            mb_intercept_date = "",
            mb_memo_call = "",
            mb_sui_address = ""
        )
        db.add(new_agent)
        db.commit()
        logger.info(f"에이전트 멤버 {AGENT_MEMBER_ID} 생성 완료.")
    else:
        logger.info(f"에이전트 멤버 {AGENT_MEMBER_ID}를 찾았습니다.")

    # 2. Ensure target board exists (assuming it should be pre-created by an admin)
    target_board = db.query(Board).filter(Board.bo_table == BOARD_TABLE_NAME).first()
    if not target_board:
        logger.warning(f"게시판 '{BOARD_TABLE_NAME}'을 찾을 수 없습니다. 수동으로 생성해주세요.")
        # Depending on policy, could raise an error or attempt to create a basic board.
        # For now, we let create_post_by_agent handle the board not found error if it occurs.
        pass
    else:
        logger.info(f"대상 게시판 '{BOARD_TABLE_NAME}'을 찾았습니다.")

# --- RSS Parsing Logic --- #
def parse_coindesk_rss():
    articles = []
    try:
        logger.info(f"RSS 피드 파싱 시작: {COINDESK_RSS_URL}")
        feed = feedparser.parse(COINDESK_RSS_URL)
        if feed.bozo:
            logger.warning(f"RSS 피드가 잘못된 형식입니다. Bozo exception: {feed.bozo_exception}")

        logger.info(f"RSS 피드에서 {len(feed.entries)}개의 항목을 찾았습니다.")
        
        for entry in feed.entries[:5]: # Get top 5 entries
            title = entry.get("title", "No Title")
            link = entry.get("link", "")
            
            # Content: feedparser provides entry.summary or entry.content
            # Coindesk RSS usually has summary_detail (with HTML) or summary.
            content_html = ""
            if hasattr(entry, "summary_detail") and entry.summary_detail:
                content_html = entry.summary_detail.get("value", "")
            elif hasattr(entry, "summary"):
                content_html = entry.summary
            
            # Clean HTML from content if needed, or use it as html1 content
            # For simplicity, let's extract text, but keep some basic structure if possible.
            # Using BeautifulSoup to get cleaner text from HTML summary
            soup = BeautifulSoup(content_html, "html.parser")
            content_text = soup.get_text(separator="\n", strip=True)
            if not content_text: # Fallback if text extraction is empty
                content_text = title # Use title if content is blank
            
            # Published date
            published_time = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_time = datetime.datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                 published_time = datetime.datetime(*entry.updated_parsed[:6])
            
            articles.append({
                "title": title,
                "link": link,
                "content": content_text, # Use cleaned text content
                "published_date": published_time
            })
            logger.info(f"RSS에서 파싱됨: {title}")
            
    except Exception as e:
        logger.error(f"RSS 파싱 중 오류 발생: {e}", exc_info=True)
    
    return articles

# --- Main Agent Logic --- #
if __name__ == "__main__":
    logger.info(f"Starting Coindesk RSS Agent at {datetime.datetime.now()}...")
    
    try:
        logger.info("데이터베이스 연결 시도 중...")
        db_session_gen = get_db()
        db = next(db_session_gen)
        logger.info("데이터베이스 연결 성공")

        logger.info("에이전트 설정 확인 중...")
        ensure_agent_setup(db) # Ensure agent member and board (check) are ready
        
        logger.info("Coindesk RSS 파싱 시작...")
        parsed_articles = parse_coindesk_rss()
        
        if not parsed_articles:
            logger.warning("RSS에서 파싱된 기사가 없습니다. 종료합니다.")
        else:
            logger.info(f"성공적으로 {len(parsed_articles)}개의 기사를 파싱했습니다. '{BOARD_TABLE_NAME}' 게시판에 포스팅 중...")

        for article_data in parsed_articles:
            try:
                # Check for duplicates (e.g., by wr_link1) before posting is recommended.
                # This check is omitted for brevity here.
                
                article_title = article_data['title']
                logger.info(f"기사 포스팅 중: {article_title}")
                
                # Prepare content. If original content was HTML and you want to keep it:
                # wr_option="html1", and pass the HTML content to wr_content.
                # For now, using the extracted text content.
                new_post = create_post_by_agent(
                    db=db,
                    bo_table=BOARD_TABLE_NAME,
                    mb_id=AGENT_MEMBER_ID,
                    wr_subject=article_data['title'],
                    wr_content=article_data['content'],
                    wr_link1=article_data['link'],
                    wr_name=AGENT_MEMBER_NICKNAME,
                    # wr_option="html1", # Uncomment if content is HTML and should be rendered as such
                    wr_ip = "127.0.0.1" # Placeholder IP for agent
                )
                logger.info(f"기사 포스팅 성공 - ID: {new_post.wr_id}, 제목: {new_post.wr_subject}")
                # Point and SUI token logic is handled within create_post_by_agent / insert_point

            except Exception as e:
                article_title = article_data.get('title', 'Unknown')
                logger.error(f"기사 포스팅 실패 '{article_title}': {e}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Coindesk 에이전트 메인 루프에서 오류 발생: {e}", exc_info=True)

    finally:
        try:
            db.close()
            logger.info("데이터베이스 연결 종료")
        except:
            pass
        logger.info(f"Coindesk RSS Agent finished at {datetime.datetime.now()}.") 