## 실행명령어
cd /root/g6
source venv/bin/activate
### telegram_insider_agent 로그인 처리가 있어서 
screen -S telegram_agent
python agent/telegram_insider_agent.py
인증 코드 입력 후 screen 세션 분리: Ctrl+A+D를 누르면 세션이 백그라운드로 전환됩니다.
나중에 세션으로 돌아가려면: screen -r telegram_agent

### naver_stock_agent
nohup python agent/naver_stock_agent.py > naver_stock_agent.log 2>&1 &

### rss_coindesk_agent
nohup python agent/rss_coindesk_agent.py > rss_coindesk_agent.log 2>&1 &