import requests
from bs4 import BeautifulSoup
import schedule
import time
from datetime import datetime
from board_rest_api import post_to_board

latest_schedule_first_article_title = None  # 이전 스케줄의 첫 번째 기사 제목


def process_stock_news():
    global latest_schedule_first_article_title
    try:
        url = "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=401"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 상단과 하단의 뉴스 리스트를 각각 가져옴
        top_news_list = soup.select_one("#contentarea_left > ul > li.newsList.top")
        bottom_news_list = soup.select_one("#contentarea_left > ul > li:nth-child(2)")

        if not top_news_list or not bottom_news_list:
            print("기사를 찾을 수 없습니다.")
            return

        content = ""
        current_first_title = None  # 현재 실행에서의 첫 번째 기사 제목

        # 상단과 하단 뉴스 리스트를 순차적으로 처리
        for news_list in [top_news_list, bottom_news_list]:
            # dl 태그 내의 모든 기사와 요약을 가져옴
            articles = news_list.select("dl dd.articleSubject")
            summaries = news_list.select("dl dd.articleSummary")

            for article, summary in zip(articles, summaries):
                article_link = article.select_one("a")
                if not article_link:
                    continue

                title = article_link.text.strip()
                link = article_link["href"]

                # 현재 실행의 첫 번째 기사 제목 저장
                if current_first_title is None:
                    current_first_title = title
                    print(f"현재 스케줄의 첫 번째 기사: {current_first_title}")

                # 이전 스케줄의 첫 번째 기사를 만나면 중단
                if title == latest_schedule_first_article_title:
                    print(f"이전 스케줄의 첫 번째 기사 발견: {title}")
                    # 지금까지 수집한 새로운 기사가 있다면 출력
                    if content:
                        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                        article_data = {
                            "title": f"증권 시황 전망 ({current_time})",
                            "content": content,
                            "ca_name": "stock",
                        }
                        print(f"새로운 기사 {len(content.split('<hr>'))-1}개 발견")
                        print(article_data)
                    return

                summary_text = summary.text.strip()
                time_text = (
                    summary.select_one(".wdate").text.strip()
                    if summary.select_one(".wdate")
                    else ""
                )

                content += f"<h3><a href='{link}' target='_blank'>{title}</a></h3>\n"
                content += f"<p>{summary_text}</p>\n"
                content += f"<p><small>{time_text}</small></p>\n"
                content += "<hr>\n"

        # 모든 기사를 처리한 후, 현재 실행의 첫 번째 기사 제목을 저장
        if current_first_title:
            latest_schedule_first_article_title = current_first_title
            print(
                f"다음 스케줄을 위한 첫 번째 기사 제목 저장: {latest_schedule_first_article_title}"
            )

        if content:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            article_data = {
                "title": f"증권 시황 전망 ({current_time})",
                "content": content,
                "ca_name": "stock",
            }

            # print(f"새로운 기사 {len(content.split('<hr>'))-1}개 발견")
            # print(article_data)
            if post_to_board(article_data):
                print("게시글 작성 성공")
            else:
                print("게시글 작성 실패")

    except Exception as e:
        print(f"오류 발생: {str(e)}")


def setup_schedule():
    """스케줄 설정"""
    # 매시 정각에 실행
    schedule.every().hour.at(":00").do(process_stock_news)
    # 초기 실행
    process_stock_news()


def run_scheduler():
    """스케줄러 실행"""
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    """메인 함수"""
    try:
        print("네이버 주식 뉴스 수집기 시작...")
        setup_schedule()
        run_scheduler()
    except KeyboardInterrupt:
        print("\n프로그램 종료")
    except Exception as e:
        print(f"오류 발생: {str(e)}")


if __name__ == "__main__":
    main()
