# /home/ubuntu/suiboard_project_v3/agent/rss_coindesk_agent.py
import feedparser
import datetime
import os
import sys
from bs4 import BeautifulSoup # To clean up HTML content from RSS summary

# Add project root to sys.path to allow importing project modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from sqlalchemy.orm import Session
from core.database import db_connect
from service.agent_service import create_post_by_agent
from core.models import Member, Board # To check/create agent member and board

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
        print(f"Agent member {AGENT_MEMBER_ID} not found. Creating...")
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
        print(f"Agent member {AGENT_MEMBER_ID} created.")
    else:
        print(f"Agent member {AGENT_MEMBER_ID} found.")

    # 2. Ensure target board exists (assuming it should be pre-created by an admin)
    target_board = db.query(Board).filter(Board.bo_table == BOARD_TABLE_NAME).first()
    if not target_board:
        print(f"Error: Board '{BOARD_TABLE_NAME}' not found. Please create it manually.")
        # Depending on policy, could raise an error or attempt to create a basic board.
        # For now, we let create_post_by_agent handle the board not found error if it occurs.
        pass
    else:
        print(f"Target board '{BOARD_TABLE_NAME}' found.")

# --- RSS Parsing Logic --- #
def parse_coindesk_rss():
    articles = []
    try:
        feed = feedparser.parse(COINDESK_RSS_URL)
        if feed.bozo:
            print(f"Warning: RSS feed is ill-formed. Bozo exception: {feed.bozo_exception}")

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
            print(f"Parsed from RSS: {title}")
            
    except Exception as e:
        print(f"An error occurred during RSS parsing: {e}")
    
    return articles

# --- Main Agent Logic --- #
if __name__ == "__main__":
    print(f"Starting Coindesk RSS Agent at {datetime.datetime.now()}...")
    db_session_gen = get_db()
    db = next(db_session_gen)

    try:
        ensure_agent_setup(db) # Ensure agent member and board (check) are ready
        
        parsed_articles = parse_coindesk_rss()
        
        if not parsed_articles:
            print("No articles parsed from RSS. Exiting.")
        else:
            print(f"Successfully parsed {len(parsed_articles)} articles. Posting to board '{BOARD_TABLE_NAME}'...")

        for article_data in parsed_articles:
            try:
                # Check for duplicates (e.g., by wr_link1) before posting is recommended.
                # This check is omitted for brevity here.
                
                article_title = article_data['title']
                print(f"Posting article: {article_title}")
                
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
                print(f"Successfully posted article ID: {new_post.wr_id}, Title: {new_post.wr_subject}")
                # Point and SUI token logic is handled within create_post_by_agent / insert_point

            except Exception as e:
                article_title = article_data.get('title', 'Unknown')
                print(f"Error posting article '{article_title}' from RSS: {e}")
                # Log this error
    
    except Exception as e:
        print(f"An error occurred in the Coindesk agent's main loop: {e}")

    finally:
        print(f"Coindesk RSS Agent finished at {datetime.datetime.now()}.")
        db.close() 