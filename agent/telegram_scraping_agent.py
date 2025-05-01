from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import csv
import datetime
import os
from dotenv import load_dotenv
from telethon.errors import SessionPasswordNeededError

load_dotenv()

# API 정보 입력
api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")
phone = os.getenv("TELEGRAM_PHONE")

# 클라이언트 생성 및 로그인
client = TelegramClient("session_name", api_id, api_hash)
client.connect()

# 인증 확인
if not client.is_user_authorized():
    client.send_code_request(phone)
    try:
        client.sign_in(phone, input("텔레그램으로 받은 코드 입력: "))
    except SessionPasswordNeededError:
        # 2단계 인증이 활성화된 경우 비밀번호 입력
        client.sign_in(password=input("2단계 인증 비밀번호 입력: "))

# 모든 대화(채널, 그룹 등) 가져오기
dialogs_result = client.get_dialogs()

# 대화 목록 표시
groups = []
for i, dialog in enumerate(dialogs_result):
    if dialog.is_group or dialog.is_channel:
        print(f"{i}. {dialog.title}")
        groups.append(dialog)

"""
# 스크래핑할 그룹 선택
1번 그룹 미국 주식 인사이더
2번 그룹 Trends & Tips
"""
group_index = int(input("스크래핑할 그룹 번호 입력: "))
target_group = groups[group_index]

print("메시지 가져오는 중...")

# 지정한 날짜 이후의 메시지만 가져오기 (선택사항)
specific_date = datetime.datetime.now() - datetime.timedelta(
    hours=1
)  # 현재 시간에서 1시간 전까지의 메시지

# 메시지 가져오기
messages = client.get_messages(
    target_group,
    limit=100,  # 가져올 메시지 수 제한
    offset_date=specific_date,  # 특정 날짜 이후 메시지만 (선택사항)
)

# CSV 파일로 저장
with open("telegram_messages.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["날짜", "발신자", "내용"])

    for message in messages:
        if message.text:  # 텍스트가 있는 메시지만
            writer.writerow(
                [
                    message.date.strftime("%Y-%m-%d %H:%M:%S"),
                    (
                        message.sender.first_name
                        if hasattr(message.sender, "first_name")
                        else "알 수 없음"
                    ),
                    message.text,
                ]
            )

print("메시지 저장 완료!")
