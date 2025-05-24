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
from core.database import db_connect
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
        print(f"페이지 로드 성공. 응답 크기: {len(response.text)} bytes")
        
        # 디버깅: 페이지의 주요 구조 확인
        print("=== 페이지 구조 디버깅 ===")
        
        # 1. mainNewsList 확인
        main_news_section = soup.find("div", class_="mainNewsList")
        print(f"mainNewsList 섹션 찾음: {main_news_section is not None}")
        
        # 2. 다른 가능한 뉴스 섹션들 확인
        possible_sections = [
            "newsList", "news_list", "main_news", "news_area", 
            "articleList", "article_list", "contentarea_left"
        ]
        
        for section_class in possible_sections:
            section = soup.find("div", class_=section_class) or soup.find("ul", class_=section_class)
            print(f"{section_class} 섹션 찾음: {section is not None}")
            if section:
                links = section.find_all("a")
                print(f"  - {section_class}에서 링크 {len(links)}개 발견")
        
        # 3. 전체 페이지에서 뉴스 관련 링크들 확인
        all_links = soup.find_all("a", href=True)
        news_links = [link for link in all_links if "news" in link.get("href", "")]
        print(f"전체 페이지에서 뉴스 관련 링크: {len(news_links)}개")
        
        # 4. 기존 로직 시도
        if main_news_section:
            print("mainNewsList 섹션에서 뉴스 추출 시도...")
            news_dls = main_news_section.find_all("dl")
            print(f"dl 요소 {len(news_dls)}개 발견")
            
            for i, dl_item in enumerate(news_dls[:5]): # Get top 5 articles
                title_tag = dl_item.find("dt", class_="articleSubject")
                summary_tag = dl_item.find("dd", class_="articleSummary")
                
                print(f"기사 {i+1}: title_tag={title_tag is not None}, summary_tag={summary_tag is not None}")
                
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

                    content = summary 
                    if not content: # If summary is empty, use title as content
                        content = title

                    articles.append({"title": title, "link": link, "content": content})
                    print(f"추출된 기사: {title}")
        else:
            print("mainNewsList 섹션을 찾을 수 없음. 대체 방법 시도...")
            
            # 대체 방법 1: 일반적인 뉴스 링크 패턴 찾기
            news_links = soup.find_all("a", href=lambda href: href and "news.naver.com" in href)[:10]
            print(f"news.naver.com 링크 {len(news_links)}개 발견")
            
            for i, link in enumerate(news_links[:5]):
                title = link.get_text(strip=True)
                if title and len(title) > 10:  # 제목이 충분히 긴 경우만
                    href = link["href"]
                    if not href.startswith("http"):
                        href = "https://finance.naver.com" + href
                    
                    articles.append({
                        "title": title,
                        "link": href,
                        "content": title  # 요약이 없으므로 제목을 내용으로 사용
                    })
                    print(f"대체 방법으로 추출된 기사: {title}")
            
            # 대체 방법 2: 더 일반적인 패턴으로 기사 찾기
            if not articles:
                print("더 일반적인 패턴으로 기사 찾기 시도...")
                # 제목이 긴 링크들을 찾기
                all_links = soup.find_all("a", href=True)
                potential_articles = []
                
                for link in all_links:
                    text = link.get_text(strip=True)
                    href = link.get("href", "")
                    
                    # 뉴스 기사로 보이는 조건들
                    if (len(text) > 15 and 
                        len(text) < 200 and
                        ("read.naver.com" in href or "news" in href) and
                        not any(skip in text.lower() for skip in ["더보기", "관련기사", "댓글", "공유"])):
                        
                        potential_articles.append({
                            "title": text,
                            "link": href if href.startswith("http") else "https://finance.naver.com" + href,
                            "content": text
                        })
                
                # 중복 제거 후 상위 5개 선택
                seen_titles = set()
                for article in potential_articles:
                    if article["title"] not in seen_titles and len(articles) < 5:
                        articles.append(article)
                        seen_titles.add(article["title"])
                        print(f"일반 패턴으로 추출된 기사: {article['title']}")

        print(f"=== 최종 결과: {len(articles)}개 기사 추출 ===")

    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {NAVER_FINANCE_NEWS_URL}: {e}")
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        import traceback
        traceback.print_exc()
    
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

