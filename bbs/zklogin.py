# /home/ubuntu/suiboard_project/bbs/zklogin.py
import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
from jose import jwt, JWTError
from typing import Optional
from passlib.context import CryptContext  # For hashing placeholder passwords

from core.database import db_session
from core.models import Member, Config  # Import Config for default member level
from lib.common import get_client_ip  # For mb_ip

# from lib.common import set_session # Assuming this is how sessions are set, or use request.session directly

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID_ZKLOGIN")
SALT_SERVICE_URL = "https://salt.api.mystenlabs.com/get_salt"
ZK_PROVER_URL_TESTNET = (
    "https://prover-testnet.mystenlabs.com/v1"  # Updated for testnet
)
ZK_PROVER_URL_DEVNET = "https://prover-dev.mystenlabs.com/v1"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ZkLoginAuthenticatePayload(BaseModel):
    jwt: str
    ephemeralPublicKey: str
    maxEpoch: int
    jwtRandomness: str


async def get_google_public_keys():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://www.googleapis.com/oauth2/v3/certs")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"Error fetching Google public keys: {e}")
            raise HTTPException(
                status_code=500,
                detail="Could not fetch Google public keys for JWT validation.",
            )
        except Exception as e:
            print(f"Unexpected error fetching Google public keys: {e}")
            raise HTTPException(
                status_code=500,
                detail="Unexpected error during Google public key fetch.",
            )


async def verify_google_jwt(token: str, client_id: str):
    keys = await get_google_public_keys()
    headers = jwt.get_unverified_headers(token)
    kid = headers.get("kid")
    if not kid:
        raise HTTPException(status_code=400, detail="kid not found in JWT header")

    key = next((k for k in keys["keys"] if k["kid"] == kid), None)
    if not key:
        raise HTTPException(status_code=400, detail="Public key not found for kid")

    try:
        decoded_token = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=client_id,
        )
        return decoded_token
    except JWTError as e:
        print(f"JWT Validation Error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid JWT: {e}")
    except Exception as e:
        print(f"Unexpected JWT Decode Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error decoding JWT: {e}")


@router.post("/api/zklogin/authenticate")
async def zklogin_authenticate(
    request: Request, payload: ZkLoginAuthenticatePayload, db: db_session = Depends()
):
    if (
        GOOGLE_CLIENT_ID
        == "1032801887648-qr0qp4quchlaj771ochub6c1tmflce51.apps.googleusercontent.com"
    ):
        raise HTTPException(
            status_code=500,
            detail="Google Client ID for zkLogin is not configured on the server.",
        )

    try:
        decoded_jwt = await verify_google_jwt(payload.jwt, GOOGLE_CLIENT_ID)
        user_email = decoded_jwt.get("email")
        user_sub = decoded_jwt.get("sub")  # Google's unique ID
        user_name_from_jwt = decoded_jwt.get(
            "name", user_email.split("@")[0]
        )  # Use name or derive from email
        user_picture = decoded_jwt.get("picture")  # Can be used for profile picture

        if not user_email or not user_sub:
            raise HTTPException(
                status_code=400, detail="Email or sub not found in JWT."
            )

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        print(f"Error during JWT verification: {e}")
        return JSONResponse(
            status_code=500, content={"detail": "JWT verification failed."}
        )

    salt = None
    try:
        async with httpx.AsyncClient() as client:
            salt_response = await client.post(
                SALT_SERVICE_URL, json={"token": payload.jwt}
            )
            salt_response.raise_for_status()
            salt_data = salt_response.json()
            salt = salt_data.get("salt")
            if not salt:
                raise HTTPException(
                    status_code=500, detail="Failed to retrieve salt from salt service."
                )
    except httpx.HTTPStatusError as e:
        print(
            f"Error getting salt from MystenLabs: {e.response.text if e.response else e}"
        )
        return JSONResponse(
            status_code=500, content={"detail": f"Failed to get user salt: {e}"}
        )
    except Exception as e:
        print(f"Unexpected error getting salt: {e}")
        return JSONResponse(
            status_code=500, content={"detail": "Unexpected error getting user salt."}
        )

    # Check if user exists by Google Subject ID first
    member = db.query(Member).filter(Member.mb_google_sub == user_sub).first()

    if not member:
        # If no user by google_sub, check by email (for linking existing accounts or if google_sub wasn't stored before)
        member_by_email = db.query(Member).filter(Member.mb_email == user_email).first()
        if member_by_email:
            # Found user by email, link their account by setting mb_google_sub
            member = member_by_email
            if (
                not member.mb_google_sub
            ):  # Only update if not already set (or if different, handle accordingly)
                member.mb_google_sub = user_sub
                db.commit()
        else:
            # User does not exist, create a new one
            config = db.query(Config).first()
            new_mb_id = (
                f"gg_{user_sub[:15]}"  # Generate a unique mb_id, ensure it's unique
            )
            # Check for mb_id collision (rare, but good practice)
            while db.query(Member).filter(Member.mb_id == new_mb_id).first():
                new_mb_id = f"gg_{user_sub[:10]}_{uuid.uuid4().hex[:4]}"

            member = Member(
                mb_id=new_mb_id,
                mb_password=pwd_context.hash(
                    uuid.uuid4().hex
                ),  # Secure placeholder password
                mb_name=user_name_from_jwt,
                mb_nick=user_name_from_jwt,  # Or generate a unique nick
                mb_nick_date=datetime.now().date(),
                mb_email=user_email,
                mb_level=getattr(
                    config, "cf_register_level", 2
                ),  # Default registration level from config or 2
                mb_sex="",  # Or try to get from JWT if available, else empty
                mb_birth="",
                mb_hp="",
                mb_certify="google_zklogin",  # Mark as certified by Google zkLogin
                mb_adult=0,  # Assume not adult unless JWT provides info
                mb_point=getattr(config, "cf_register_point", 0),
                mb_today_login=datetime.now(),
                mb_login_ip=get_client_ip(request),
                mb_datetime=datetime.now(),
                mb_ip=get_client_ip(request),
                mb_email_certify=datetime.now(),  # Email is considered certified by Google
                mb_mailling=1,  # Default to allow mailing
                mb_sms=0,
                mb_open=1,  # Default to open profile
                mb_open_date=datetime.now().date(),
                mb_profile=decoded_jwt.get("name", "") + " (Google zkLogin User)",
                mb_google_sub=user_sub,  # Store Google Subject ID
                # mb_profile_img = user_picture # If you have a field for profile image URL
            )
            db.add(member)
            try:
                db.commit()
                db.refresh(member)
            except Exception as e:
                db.rollback()
                print(f"Error creating new zkLogin user: {e}")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Failed to create new user account."},
                )

    try:
        request.session["ss_mb_id"] = member.mb_id
        print(f"Session set for user: {member.mb_id}")
    except Exception as e:
        print(f"Error setting session: {e}")
        return JSONResponse(
            status_code=500, content={"detail": "Failed to set user session."}
        )

    return JSONResponse(
        content={
            "message": "Authentication successful via zkLogin",
            "user_email": user_email,
            "sui_address_derived_conceptually": f"address_for_{user_sub}_with_salt_{salt}",
            "redirect_url": "/",
        }
    )


def add_zklogin_router(app):
    app.include_router(router)
