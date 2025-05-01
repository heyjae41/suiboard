import time
import requests
from pydantic import BaseModel
from token_gen import get_token


class Article(BaseModel):
    """커뮤니티 게시판 글 작성을 위한 모델"""

    wr_subject: str = ""
    wr_content: str = ""
    wr_name: str = "AINewsAgent"
    wr_password: str = "Jennifer!002"
    wr_email: str = "moneyit777@gmail.com"
    wr_homepage: str = "https://marketmaker.store"
    wr_link1: str = ""
    wr_link2: str = ""
    wr_option: str = ""
    html: str = "html1"
    mail: str = ""
    secret: str = ""
    ca_name: str = ""
    notice: bool = False
    parent_id: int = 0
    wr_comment: int = 0


def post_to_board(article_data: dict) -> bool:
    """게시판에 글 작성"""
    try:
        # 토큰 가져오기
        access_token = get_token()
        if not access_token:
            print("토큰을 가져올 수 없습니다.")
            return False

        # API 요청 헤더 설정
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "accept": "application/json",
        }

        # Article 모델에 맞게 데이터 구성
        article = Article(
            wr_subject=article_data["title"],
            wr_content=article_data["content"],
            ca_name=article_data["ca_name"],
        )

        # API 엔드포인트 설정
        api_url = "https://marketmaker.store/api/v1/boards/blockchain/writes"

        # API 요청
        response = requests.post(api_url, headers=headers, json=article.model_dump())

        if response.status_code == 200:
            print(f"게시글 작성 성공: {article.wr_subject}")
            return True
        elif response.status_code == 429:
            print("너무 많은 요청이 발생했습니다. 잠시 후 다시 시도합니다.")
            time.sleep(60)  # 1분 대기 후 재시도
            return post_to_board(article_data)  # 재귀적으로 다시 시도
        else:
            print(f"게시글 작성 실패: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"게시글 작성 중 오류 발생: {str(e)}")
        return False
