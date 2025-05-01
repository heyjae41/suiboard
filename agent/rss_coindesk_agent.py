import feedparser
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from datetime import datetime
from dotenv import load_dotenv
import time
import json
import schedule
from board_rest_api import post_to_board


def get_openai_client():
    """OpenAI 클라이언트 초기화"""
    llm = ChatOpenAI(
        temperature=0.1,
        max_tokens=4000,  # 응답에 사용할 최대 토큰 수 (입력 토큰 제외)
        model_name="gpt-4o",
    )
    return llm


def translate_and_summarize_article(
    client: ChatOpenAI, title: str, content: str
) -> dict:
    """기사 번역 및 요약"""
    # 영어 제목과 내용을 한글로 번역
    translation_prompt = f"Translate the following English text to Korean:\n\nTitle: {title}\n\nContent: {content}"
    translation_response = client.invoke([HumanMessage(content=translation_prompt)])
    translated_text = translation_response.content.strip()

    # 번역된 텍스트에서 제목과 내용 분리
    try:
        # 먼저 "Title:" 과 "Content:" 로 구분해보기
        parts = translated_text.split("Content:")
        if len(parts) == 2:
            translated_title = parts[0].replace("Title:", "").strip()
            translated_content = parts[1].strip()
        else:
            # 실패하면 첫 줄을 제목으로, 나머지를 내용으로
            lines = translated_text.split("\n")
            translated_title = lines[0].strip()
            translated_content = "\n".join(lines[1:]).strip()

        # 내용이 비어있으면 제목을 내용으로 사용
        if not translated_content:
            translated_content = translated_title

        # '제목: '과 '내용: ' 접두어 제거
        translated_title = translated_title.replace("제목: ", "").strip()
        translated_content = translated_content.replace("내용: ", "").strip()

        return {
            "title": translated_title,
            "content": translated_content,
        }

    except Exception as e:
        print(f"텍스트 파싱 중 오류 발생: {str(e)}")
        return {
            "title": title,  # 오류 발생시 원본 제목 사용
            "content": translated_text,  # 전체 번역 텍스트를 내용으로 사용
        }


def process_rss_feed(rss_url: str) -> list:
    """RSS 피드 처리"""
    client = get_openai_client()
    articles = []

    # RSS 피드 파싱
    feed = feedparser.parse(rss_url)

    # 현재 시각을 UTC로 변환
    current_time = datetime.utcnow()

    for entry in feed.entries:
        try:
            # print(entry)
            # 글 작성 시각 파싱 (RSS의 시간은 이미 UTC)
            try:
                # timezone 정보가 있는 경우
                pub_date = datetime.strptime(
                    entry.published, "%a, %d %b %Y %H:%M:%S %z"
                )
            except ValueError:
                try:
                    # timezone 정보가 없는 경우
                    pub_date = datetime.strptime(
                        entry.published, "%a, %d %b %Y %H:%M:%S"
                    )
                except ValueError:
                    try:
                        # ISO 형식 시도
                        pub_date = datetime.fromisoformat(
                            entry.published.replace("Z", "+00:00")
                        )
                    except ValueError as e:
                        print(f"날짜 파싱 오류: {str(e)} - {entry.published}")
                        continue

            # print(pub_date)
            pub_date = pub_date.astimezone().replace(
                tzinfo=None
            )  # UTC로 변환 후 timezone 정보 제거

            # 현재 시각과의 차이 계산 (시간 단위)
            time_diff = (current_time - pub_date).total_seconds() / 3600

            # 1시간 이상 지난 글은 건너뛰기
            if time_diff > 1:
                continue

            # 기사 제목
            title = entry.title

            # 기사 내용 가져오기 (content:encoded 태그 내용 우선)
            content = ""
            if "content" in entry and entry.content:
                # HTML 콘텐츠 찾기 (type이 'text/html'인 항목)
                for content_item in entry.content:
                    if content_item.get("type") == "text/html":
                        content = content_item.value
                        break
                # HTML 콘텐츠가 없으면 첫 번째 콘텐츠 사용
                if not content and entry.content:
                    content = entry.content[0].value
            elif "content_encoded" in entry:
                content = entry.content_encoded
            else:
                content = entry.get("description", "")

            # HTML 태그 제거 (선택적)
            # content = content.replace("<p>", "\n").replace("</p>", "\n")
            # content = content.replace("<h1>", "\n").replace("</h1>", "\n")
            # content = content.replace("<h4>", "\n").replace("</h4>", "\n")
            # content = content.replace("<br>", "\n").replace("<br/>", "\n")
            # content = content.replace("</div>", "\n").replace("</section>", "\n")

            # 링크 태그 처리
            # while "<a href=" in content:
            #     start = content.find("<a href=")
            #     end = content.find("</a>", start) + 4
            #     if end > 4:  # </a>를 찾았을 경우
            #         link_text = content[start:end]
            #         # 링크 텍스트만 추출
            #         text_start = link_text.find(">")
            #         if text_start != -1:
            #             text = link_text[text_start + 1 : link_text.find("</a>")]
            #             content = content.replace(link_text, text)
            #     else:
            #         break  # 무한루프 방지

            # 연속된 빈 줄 제거
            while "\n\n\n" in content:
                content = content.replace("\n\n\n", "\n\n")

            content = content.strip()

            # 대표 이미지 URL 가져오기
            image_url = ""
            if "media_content" in entry and entry.media_content:
                image_url = entry.media_content[0]["url"]

            # 기사 번역 및 요약
            article = translate_and_summarize_article(client, title, content)
            if article:
                articles.append(article)

                # 게시판 데이터에 이미지 URL 추가
                article_data = {
                    "title": article["title"],
                    "content": (
                        f'<p><img src="{image_url}" width="1280"></p>\n\n{article["content"]}'
                        if image_url
                        else article["content"]
                    ),
                    "ca_name": "blockchain",
                }

                # 번역된 기사를 게시판에 작성
                if not post_to_board(article_data):
                    print(f"게시글 작성 실패: {article['title']}")
                time.sleep(60)  # 요청 간격을 1분으로 늘림

        except Exception as e:
            print(f"기사 처리 중 오류 발생: {str(e)}")
            continue

    return articles


def run_news_collector():
    """뉴스 수집 작업 실행"""
    try:
        # 시작 시간 기록
        start_time = time.time()
        start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n작업 시작 시간: {start_datetime}")

        # RSS 피드 처리
        rss_url = "https://www.coindesk.com/arc/outboundfeeds/rss"
        articles = process_rss_feed(rss_url)

        # 종료 시간 기록
        end_time = time.time()
        end_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed_time = end_time - start_time

        # 결과 출력
        print(json.dumps(articles, ensure_ascii=False, indent=2))

        # 시간 정보 출력
        print(f"\n작업 종료 시간: {end_datetime}")
        print(f"총 소요 시간: {elapsed_time:.2f}초")

    except Exception as e:
        print(f"오류 발생: {str(e)}")
        print("다음 예약된 실행을 기다립니다.")


def main():
    """메인 함수"""
    load_dotenv()

    print("뉴스 수집 에이전트가 시작되었습니다.")
    print("매 시간 정각에 뉴스를 수집합니다.")

    # 매 시간 정각에 실행되도록 스케줄 설정
    schedule.every().hour.at(":05").do(run_news_collector)

    # 프로그램 시작 시 즉시 한 번 실행
    run_news_collector()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")


if __name__ == "__main__":
    main()
