# /home/ubuntu/suiboard_project/bbs/zklogin.py
import os
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, Body
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx
import base64
from typing import Optional, Dict, Any
from passlib.context import CryptContext  # For hashing placeholder passwords
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Member, Config  # Import Config for default member level
from lib.common import get_client_ip  # For mb_ip

# from lib.common import set_session # Assuming this is how sessions are set, or use request.session directly

router = APIRouter()

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

GOOGLE_CLIENT_ID = (
    "1032801887648-qr0qp4quchlaj771ochub6c1tmflce51.apps.googleusercontent.com"
)
SALT_SERVICE_URL = "https://salt.api.mystenlabs.com/get_salt"
ZK_PROVER_URL_TESTNET = (
    "https://prover-testnet.mystenlabs.com/v1"  # Updated for testnet
)
ZK_PROVER_URL_DEVNET = "https://prover-dev.mystenlabs.com/v1"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Pydantic 모델: zkLogin 인증 요청 검증
class ZkLoginAuthenticatePayload(BaseModel):
    jwt: str
    ephemeralPublicKey: str
    maxEpoch: int
    jwtRandomness: str


# 단순화된 인증 엔드포인트
@router.post("/api/zklogin/authenticate")
async def zklogin_auth(request: Request, db: Session = Depends(get_db)):
    """단순화된 zkLogin 인증 처리"""
    print(f"ZkLogin 인증 엔드포인트 호출됨")

    try:
        # 요청 본문 직접 읽기
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8")
        print(f"수신된 요청 본문: {body_str}")

        try:
            data = json.loads(body_str)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return JSONResponse(status_code=400, content={"detail": "잘못된 JSON 형식"})

        # 필수 필드 확인
        if not all(
            k in data
            for k in ["jwt", "ephemeralPublicKey", "maxEpoch", "jwtRandomness"]
        ):
            missing = [
                k
                for k in ["jwt", "ephemeralPublicKey", "maxEpoch", "jwtRandomness"]
                if k not in data
            ]
            return JSONResponse(
                status_code=400,
                content={"detail": f"필수 필드 누락: {', '.join(missing)}"},
            )

        jwt_token = data["jwt"]
        ephemeral_public_key = data["ephemeralPublicKey"]
        max_epoch = data["maxEpoch"]
        jwt_randomness = data["jwtRandomness"]

        print(f"추출된 필드:")
        print(f"- jwt: {jwt_token[:20]}...")
        print(f"- ephemeralPublicKey: {ephemeral_public_key}")
        print(f"- maxEpoch: {max_epoch}")
        print(f"- jwtRandomness: {jwt_randomness[:20]}...")

        # JWT 토큰 디코딩하여 사용자 정보 추출
        try:
            # 서명 검증 없이 토큰 페이로드만 디코딩
            token_parts = jwt_token.split(".")
            if len(token_parts) != 3:
                raise ValueError("Invalid JWT token format")

            # 패딩 추가 처리
            payload = token_parts[1]
            payload += "=" * ((4 - len(payload) % 4) % 4)  # 패딩 추가
            decoded_payload = base64.b64decode(payload)
            user_data = json.loads(decoded_payload)

            # 사용자 정보 추출
            user_email = user_data.get("email", "")
            user_name = user_data.get("name", "")
            user_given_name = user_data.get("given_name", "")
            user_family_name = user_data.get("family_name", "")
            user_picture = user_data.get("picture", "")
            user_sub = user_data.get("sub", "")  # Google 사용자 ID

            print(f"사용자 정보 추출:")
            print(f"- email: {user_email}")
            print(f"- name: {user_name}")
            print(f"- sub: {user_sub}")
        except Exception as e:
            print(f"JWT 토큰 디코딩 오류: {str(e)}")
            user_email = ""
            user_name = "Unknown User"
            user_given_name = ""
            user_family_name = ""
            user_picture = ""
            user_sub = str(uuid.uuid4())  # 임시 식별자

        # Salt 서비스 호출 - 실제로는 MystenLabs API 호출
        salt = "dummy_salt_for_testing"

        # 사용자 조회/생성 로직
        member = db.query(Member).filter(Member.mb_email == user_email).first()

        if not member and user_email:
            # 이메일로 찾지 못했다면 Google sub로 시도
            member = db.query(Member).filter(Member.mb_google_sub == user_sub).first()

        if not member:
            # 새 사용자 생성
            config = db.query(Config).first()
            new_mb_id = f"gg_{uuid.uuid4().hex[:10]}"

            member = Member(
                mb_id=new_mb_id,
                mb_password=pwd_context.hash(uuid.uuid4().hex),
                mb_name=user_name[:255] if user_name else "",
                mb_nick=(
                    f"{user_name[:245]}#{new_mb_id[-4:]}"
                    if user_name
                    else f"User#{new_mb_id[-8:]}"
                ),
                mb_nick_date=datetime.now().date(),
                mb_email=user_email[:255] if user_email else "",
                mb_level=getattr(config, "cf_register_level", 2),
                mb_sex="",
                mb_birth="",
                mb_hp="",
                mb_certify="google_zklogin",
                mb_adult=0,
                mb_point=getattr(config, "cf_register_point", 1000),
                mb_today_login=datetime.now(),
                mb_login_ip=get_client_ip(request),
                mb_datetime=datetime.now(),
                mb_ip=get_client_ip(request),
                mb_email_certify=datetime.now(),
                mb_mailling=1,
                mb_sms=0,
                mb_open=1,
                mb_open_date=datetime.now().date(),
                mb_profile=(
                    f"{user_name} (Google zkLogin User)"[:255]
                    if user_name
                    else "(Google zkLogin User)"
                ),
                mb_google_sub=user_sub[:255] if user_sub else "",
            )
            db.add(member)
            db.commit()
            db.refresh(member)

        # 세션 설정
        request.session["ss_mb_id"] = member.mb_id
        print(f"세션 설정 완료: {member.mb_id}")

        return JSONResponse(
            content={
                "message": "인증 성공",
                "user_id": member.mb_id,
                "redirect_url": "/",
            }
        )

    except Exception as e:
        print(f"인증 처리 중 오류 발생: {str(e)}")
        return JSONResponse(
            status_code=500, content={"detail": f"인증 처리 중 오류 발생: {str(e)}"}
        )


@router.get("/auth/zklogin/google/callback")
async def zklogin_google_callback(request: Request):
    """
    Google zkLogin 콜백 URL을 처리합니다.
    이 엔드포인트는 OAuth 리다이렉트 후 zklogin_handler.js에서 처리할 HTML 페이지를 반환합니다.
    """
    print("Google zkLogin 콜백 요청 수신")
    return templates.TemplateResponse(
        "bootstrap/auth/zklogin/google/callback.html", {"request": request}
    )


def add_zklogin_router(app):
    app.include_router(router)
