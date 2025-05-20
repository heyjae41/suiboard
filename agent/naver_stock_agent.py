# /home/ubuntu/suiboard_project_v3/agent/naver_stock_agent.py
import requests
from bs4 import BeautifulSoup
import datetime
import os
import sys

# Add project root to sys.path to allow importing project modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from sqlalchemy.orm import Session
from core.database import SessionLocal, engine # Assuming SessionLocal is your session factory
from service.agent_service import create_post_by_agent
from core.models import Member, Board # To check/create agent member and board

# Configuration
NAVER_FINANCE_NEWS_URL = "https://finance.naver.com/news/mainnews.naver"
BOARD_TABLE_NAME = "stock"  # Target board table (bo_table)
AGENT_MEMBER_ID = "AINewsAgent" # Member ID for the agent
AGENT_MEMBER_NICKNAME = "AINewsAgent"
AGENT_MEMBER_EMAIL = "moneyit777@gmail.com"
AGENT_MEMBER_PASSWORD = "sha256:12000:efqEs0FMP6uM7M+xLFQXZTd1/41juBDb:mex5gcyH++hSY5UyhPc4EfIAHqc38QOk"

# --- Database Setup --- #
# This is a simplified setup. In a real app, SessionLocal might be managed by FastAPI dependencies.
def get_db():
    db = SessionLocal()
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
        # Create a basic agent member. Fill required fields.
        # Password should be a secure hash if direct login is ever possible/needed.
        # For agent-only, a placeholder or unloggable password is fine.
        new_agent = Member(
            mb_id=AGENT_MEMBER_ID,
            mb_password=AGENT_MEMBER_PASSWORD,
            mb_name=AGENT_MEMBER_NICKNAME,
            mb_nick=AGENT_MEMBER_NICKNAME,
            mb_email=AGENT_MEMBER_EMAIL,
            mb_level=2, # Adjust level as needed
            mb_mailling=0,
            mb_open=0,
            mb_email_certify=datetime.datetime.now(),
            mb_datetime=datetime.datetime.now(),
            mb_ip = "0.0.0.0",
            mb_leave_date = "",
            mb_intercept_date = "",
            mb_memo_call = "",
            mb_sui_address = "" # Optional SUI address for the agent
        )
        db.add(new_agent)
        db.commit()
        print(f"Agent member {AGENT_MEMBER_ID} created.")
    else:
        print(f"Agent member {AGENT_MEMBER_ID} found.")

    # 2. Ensure target board exists (optional, depends on whether boards are pre-created)
    target_board = db.query(Board).filter(Board.bo_table == BOARD_TABLE_NAME).first()
    if not target_board:
        # This part is more complex as boards have many settings.
        # For this agent, we assume the 'stock' board is already created by an admin.
        print(f"Error: Board '{BOARD_TABLE_NAME}' not found. Please create it manually.")
        # raise ValueError(f"Board '{BOARD_TABLE_NAME}' not found. Please create it manually.")
        # For now, we will proceed, but create_post_by_agent will fail if board doesn't exist.
        pass # Let create_post_by_agent handle the error if board is missing
    else:
        print(f"Target board '{BOARD_TABLE_NAME}' found.")

# --- Scraping Logic --- #
def scrape_naver_finance_news():
    articles = []
    try:
        response = requests.get(NAVER_FINANCE_NEWS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status() # Raise an exception for HTTP errors
        response.encoding = response.apparent_encoding # Or manually set to 'euc-kr' or 'utf-8'

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find news items. Selector might need adjustment if Naver changes layout.
        # Example: looking for <li> elements within a specific <ul> list of news
        # This is a common structure, but needs verification.
        # Let's try to find news items from the main news list area
        # Common selectors for Naver news lists are often like 'ul.realtime_news_list li' or similar.
        # For mainnews, it's often a bit different. Inspecting https://finance.naver.com/news/mainnews.naver
        # The news items are in <dd class="articleSubject"> or <dt class="articleSubject"> for titles
        # and <dd class="articleSummary"> for summaries.
        # Let's target the main news list section, often within a div like 'news_section'.
        # A more robust selector would be needed after careful inspection.
        # For now, let's try a general approach based on common Naver Finance news structure.
        # The structure is: <div class="news_cluster_list"> <div class="news_cluster"> <div class="cluster_head"> <a href="...">TITLE</a> </div> <div class="cluster_body"> <ul class="cluster_news_list"> <li> <a href="...">article_title</a> <span class="writing">press</span> <span class="date">date</span> </li> ...
        # This is for clustered news. Let's try the main news list which is simpler.
        # The main news list items are often in <dl class="newsList"> <dt> <a href="...">TITLE</a> </dt> <dd>SUMMARY <span class="articleInfo">...</span></dd> </dl>
        # Looking at the source of mainnews.naver, it seems like news items are in <li> tags inside <ul class="newsList"> (this is old structure)
        # Current structure (2024-2025) for mainnews.naver seems to be more complex.
        # Let's try to find elements with class "newsList" or "articleSubject" and "articleSummary".
        # A common pattern is a list of articles, each with a title and a link.
        # The main news page has several sections. We'll try the first prominent list.
        
        news_items = [] # Store (title, link, summary_or_content)
        
        # Attempt 1: Find news list by a common class like 'news_list' or 'main_news_list'
        # This is highly dependent on Naver's current HTML structure.
        # For https://finance.naver.com/news/mainnews.naver, news are within <ul> with class 'newsList'
        # and each item is an <li>. Inside <li>, there's an <a> tag for the title and link.
        # Example: <ul class="newsList"> <li> <span class="thumb"><img ...></span> <a href="URL">TITLE</a> <span class="writing">PRESS</span> <span class="date">DATE</span> </li> ... </ul>
        # This is for the image list. Text list is different.
        # Text list: <div class="news_text_list"> <ul> <li> <a href="URL">TITLE</a> <span class="writing">PRESS</span> <span class="date">DATE</span> </li> ... </ul> </div>

        # Let's try to get the main news headlines from the top section.
        # These are usually in <dd class="articleSubject"> or <dt class="articleSubject">
        # For mainnews.naver, the main headlines are in <div id="contentarea_left">
        # <div class="mainNewsList"> <dl> <dt class="articleSubject"> <a href="...">TITLE</a> </dt> <dd class="articleSummary"> SUMMARY... </dd> </dl> ... </div>
        
        main_news_section = soup.find("div", class_="mainNewsList")
        if main_news_section:
            news_dls = main_news_section.find_all("dl")
            for dl_item in news_dls[:5]: # Get top 5 articles
                title_tag = dl_item.find("dt", class_="articleSubject")
                summary_tag = dl_item.find("dd", class_="articleSummary")
                
                if title_tag and title_tag.a and summary_tag:
                    title = title_tag.a.get_text(strip=True)
                    link = title_tag.a["href"]
                    if not link.startswith("http"):
                        link = "https://finance.naver.com" + link # Ensure full URL
                    
                    summary_parts = []
                    for content_node in summary_tag.contents:
                        if content_node.name == 'span' and 'articleInfo' in content_node.get('class', []):
                            break # Stop before press/date info
                        if isinstance(content_node, str):
                            summary_parts.append(content_node.strip())
                        elif content_node.name != 'a': # Exclude links within summary if any
                             summary_parts.append(content_node.get_text(strip=True))
                    summary = " ".join(summary_parts).strip()
                    summary = summary.split("...")[0] + "..." # Often ends with '...'

                    # For content, we might need to fetch the article page (link)
                    # For now, let's use summary as content or a part of it.
                    # To keep it simple, we'll use summary as the main content for now.
                    # In a real scenario, you'd visit 'link' to get full article content.
                    content = summary 
                    if not content: # If summary is empty, use title as content
                        content = title

                    articles.append({"title": title, "link": link, "content": content})
                    print(f"Scraped: {title}")
        else:
            print("Could not find main news section. Scraping might fail or get no articles.")

    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {NAVER_FINANCE_NEWS_URL}: {e}")
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    
    return articles

# --- Main Agent Logic --- #
if __name__ == "__main__":
    print(f"Starting Naver Stock Agent at {datetime.datetime.now()}...")
    db_session_gen = get_db()
    db = next(db_session_gen)

    try:
        ensure_agent_setup(db) # Ensure agent member and board (check) are ready
        
        scraped_articles = scrape_naver_finance_news()
        
        if not scraped_articles:
            print("No articles scraped. Exiting.")
        else:
            print(f"Successfully scraped {len(scraped_articles)} articles. Posting to board '{BOARD_TABLE_NAME}'...")

        for article_data in scraped_articles:
            try:
                # Check if article with this link already exists to avoid duplicates
                # This requires querying WriteBaseModel for wr_link1 or similar field.
                # For simplicity, this check is omitted here but is important in production.
                
                print(f"Posting article: {article_data['title']}")
                new_post = create_post_by_agent(
                    db=db,
                    bo_table=BOARD_TABLE_NAME,
                    mb_id=AGENT_MEMBER_ID,
                    wr_subject=article_data["title"],
                    wr_content=article_data["content"], # Or fetch full content from article_data['link']
                    wr_link1=article_data["link"],
                    wr_name=AGENT_MEMBER_NICKNAME, # Agent's nickname
                    # wr_option="html1" # If content is HTML
                    wr_ip = "127.0.0.1" # Placeholder IP for agent
                )
                print(f"Successfully posted article ID: {new_post.wr_id}, Title: {new_post.wr_subject}")
                # SUI token and point logic is handled within create_post_by_agent / insert_point

            except Exception as e:
                print(f"Error posting article '{article_data['title']}': {e}")
                # Log this error to a file or monitoring system
    
    except Exception as e:
        print(f"An error occurred in the agent's main loop: {e}")

    finally:
        print(f"Naver Stock Agent finished at {datetime.datetime.now()}.")
        db.close()

