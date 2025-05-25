from datetime import datetime
from typing import Optional, Dict, Any
import requests
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()


class TokenResponse(BaseModel):
    """토큰 응답 모델"""

    access_token: str
    access_token_expire_at: datetime
    refresh_token: str
    refresh_token_expire_at: datetime
    token_type: str


class TokenManager:
    """토큰 관리 클래스"""

    def __init__(self):
        # 환경변수에서 BASE_URL을 가져오고, 없으면 기본값 사용
        base_url = os.getenv("BASE_URL", "https://marketmaker.store")
        self.base_url = f"{base_url}/api/v1"
        self.token_data: Optional[TokenResponse] = None

    def get_access_token(self, username: str, password: str) -> Optional[TokenResponse]:
        """액세스 토큰 발급"""
        try:
            headers = {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {
                "grant_type": "password",
                "username": username,
                "password": password,
                "scope": "",
                "client_id": "string",
                "client_secret": "string",
            }

            response = requests.post(
                f"{self.base_url}/token", headers=headers, data=data
            )

            if response.status_code == 200:
                self.token_data = TokenResponse(**response.json())
                return self.token_data
            elif response.status_code == 403:
                print(f"인증 실패: {response.json().get('message')}")
            elif response.status_code == 422:
                print(f"입력값 오류: {response.json().get('detail')}")

            return None

        except Exception as e:
            print(f"토큰 발급 중 오류 발생: {str(e)}")
            return None

    def refresh_token(self, refresh_token: str) -> Optional[TokenResponse]:
        """리프레시 토큰을 사용하여 새로운 액세스 토큰 발급"""
        try:
            headers = {
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {
                "refresh_token": refresh_token,
            }

            response = requests.post(
                f"{self.base_url}/token/refresh", headers=headers, data=data
            )

            if response.status_code == 200:
                self.token_data = TokenResponse(**response.json())
                return self.token_data
            elif response.status_code == 422:
                print(f"토큰 갱신 오류: {response.json().get('detail')}")

            return None

        except Exception as e:
            print(f"토큰 갱신 중 오류 발생: {str(e)}")
            return None

    def is_token_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if not self.token_data:
            return True

        now = datetime.utcnow()
        return now >= self.token_data.access_token_expire_at

    def get_valid_token(self) -> Optional[str]:
        """유효한 액세스 토큰 반환"""
        if not self.token_data:
            return None

        if self.is_token_expired():
            # 토큰이 만료되었으면 리프레시 토큰으로 갱신 시도
            refreshed = self.refresh_token(self.token_data.refresh_token)
            if not refreshed:
                return None

        return self.token_data.access_token


# 싱글톤 인스턴스 생성
token_manager = TokenManager()


def get_token() -> Optional[str]:
    """유효한 토큰 반환 (다른 모듈에서 사용할 함수)"""
    load_dotenv()

    if not token_manager.token_data:
        username = "AINewsAgent"
        password = "Jennifer!002"

        token_manager.get_access_token(username, password)

    return token_manager.get_valid_token()


if __name__ == "__main__":
    print(get_token())
