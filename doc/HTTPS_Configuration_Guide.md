# SUIBOARD HTTPS 설정 가이드

## 개요

SUIBOARD 프로젝트에서 HTTP에서 HTTPS로 통신하도록 설정하는 방법을 설명합니다.

## 문제 상황

- 정보 수정/업데이트 시 HTTP로 전달되어 "Method Not Allowed" 오류 발생
- 하드코딩된 HTTPS URL로 인한 프로토콜 불일치
- 개발환경과 프로덕션 환경 간의 URL 차이
- 로그인 시 무한 리다이렉트 루프 발생
- 정적 파일(CSS, JS) 404/403 오류 발생
- SUI SDK 로드 실패

## 해결 방안

### 1. 환경변수 설정

`.env` 파일에 다음 설정을 추가하세요:

```env
# 기본 URL 설정 (프로토콜 포함)
BASE_URL=https://marketmaker.store

# HTTPS 강제 사용 여부
FORCE_HTTPS=True

# 쿠키 도메인 설정
COOKIE_DOMAIN=marketmaker.store
```

### 2. 개발환경 설정

로컬 개발 시에는 다음과 같이 설정:

```env
BASE_URL=http://localhost:8000
FORCE_HTTPS=false
COOKIE_DOMAIN=localhost
```

### 3. 프로덕션 환경 설정

프로덕션 환경에서는 다음과 같이 설정:

```env
BASE_URL=https://marketmaker.store
FORCE_HTTPS=false  # Nginx에서 HTTPS 리다이렉트 처리하므로 비활성화
COOKIE_DOMAIN=marketmaker.store
```

**중요**: 프로덕션 환경에서는 웹서버(Nginx/Apache)에서 HTTPS 리다이렉트를 처리하는 것이 더 효율적이므로 FastAPI의 `FORCE_HTTPS`는 `false`로 설정합니다.

## 주요 변경사항

### 1. 템플릿 파일 수정

모든 `base_sub.html` 파일에서 하드코딩된 URL을 동적 URL로 변경:

```javascript
// 변경 전
const g6_url = "https://marketmaker.store/";

// 변경 후
const g6_url = "{{ request.url.scheme }}://{{ request.url.netloc }}/";
```

### 2. 에이전트 파일 수정

`agent/token_gen.py`와 `agent/board_rest_api.py`에서 환경변수 사용:

```python
# 환경변수에서 BASE_URL 가져오기
base_url = os.getenv("BASE_URL", "https://marketmaker.store")
```

### 3. 프록시 헤더 처리

`main.py`의 미들웨어에서 Nginx에서 전달된 HTTPS 정보를 인식하도록 설정:

```python
# 프록시 헤더 처리 (Nginx에서 전달된 HTTPS 정보 인식)
if "x-forwarded-proto" in request.headers:
    forwarded_proto = request.headers["x-forwarded-proto"]
    if forwarded_proto == "https":
        # HTTPS 요청으로 인식하도록 URL 스키마 업데이트
        request.scope["scheme"] = "https"

# HTTPS 강제 리다이렉트 (개발환경에서만 사용)
if settings.FORCE_HTTPS and request.url.scheme == "http":
    if request.url.path.startswith(("/admin", "/api")) and request.method == "GET":
        https_url = request.url.replace(scheme="https")
        return RedirectResponse(url=str(https_url), status_code=301)
```

### 4. 로그인 폼 URL 수정

모든 로그인 폼에서 하드코딩된 URL을 동적 URL로 변경:

```html
<!-- 변경 전 -->
<form action="/bbs/login" method="post">

<!-- 변경 후 -->
<form action="{{ url_for('login') }}" method="post">
```

영향받는 파일:
- `templates/bootstrap/bbs/outlogin_before.html`
- `templates/basic/bbs/outlogin_before.html`
- `templates/bootstrap/bbs/login_form.html`

## 웹서버 설정

### Nginx 설정 예시

실제 적용된 설정 (`/etc/nginx/sites-available/default`):

```nginx
# HTTP에서 HTTPS로 리다이렉트
server {
    listen 80;
    server_name marketmaker.store www.marketmaker.store;
    
    # Let's Encrypt 인증서 갱신을 위한 경로
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # 모든 HTTP 요청을 HTTPS로 리다이렉트
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS 서버 설정
server {
    listen 443 ssl http2;
    server_name marketmaker.store www.marketmaker.store;

    # SSL 인증서 설정 (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/marketmaker.store/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/marketmaker.store/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # 보안 헤더
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # 로그 설정
    access_log /var/log/nginx/your-access.log;
    error_log  /var/log/nginx/your-error.log;

    # 정적 파일 캐싱
    location /static/ {
        alias /var/www/suiboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    location /data/ {
        alias /var/www/suiboard/data/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # FastAPI 애플리케이션으로 프록시
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;  # 중요: HTTPS 인식을 위해 추가
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket 지원 (필요한 경우)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 정적 파일은 로그에서 제외
        if ($request_uri ~* \.(css|js|ico|gif|png|jpe?g|svg)$) {
            access_log off;
        }
    }

    # 파일 업로드 크기 제한
    client_max_body_size 50M;
}
```

### Apache 설정 예시

```apache
<VirtualHost *:80>
    ServerName marketmaker.store
    Redirect permanent / https://marketmaker.store/
</VirtualHost>

<VirtualHost *:443>
    ServerName marketmaker.store
    
    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
    
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
    ProxyPreserveHost On
    ProxyAddHeaders On
</VirtualHost>
```

## 테스트 방법

### 1. 개발환경 테스트

```bash
# 개발 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8000

# HTTP로 접속하여 폼 제출 테스트
curl -X POST http://localhost:8000/admin/config_form_update \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test=data"
```

### 2. 프로덕션 환경 테스트

```bash
# HTTPS로 접속하여 폼 제출 테스트
curl -X POST https://marketmaker.store/admin/config_form_update \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "test=data"
```

## 정적 파일 권한 문제 해결

### 1. 권한 문제 진단

정적 파일 404/403 오류가 발생하는 경우:

```bash
# 정적 파일 접근 테스트
curl -I https://marketmaker.store/static/js/jquery.min.js

# 403 Forbidden 오류 발생 시 권한 확인
ls -la /root/
```

### 2. 해결 방법

#### 방법 1: 심볼릭 링크 사용 (권장)

```bash
# 웹 서버용 디렉토리 생성
mkdir -p /var/www/suiboard

# 심볼릭 링크 생성
ln -s /root/suiboard/static /var/www/suiboard/static
ln -s /root/suiboard/data /var/www/suiboard/data

# root 디렉토리 실행 권한 추가
chmod 755 /root
```

#### 방법 2: 파일 복사 (비권장)

```bash
# 정적 파일 복사
cp -r /root/suiboard/static/ /var/www/suiboard/
cp -r /root/suiboard/data/ /var/www/suiboard/

# 웹 서버 사용자에게 소유권 부여
chown -R www-data:www-data /var/www/suiboard/
```

### 3. Nginx 설정 업데이트

```nginx
# 정적 파일 경로를 새로운 위치로 변경
location /static/ {
    alias /var/www/suiboard/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

location /data/ {
    alias /var/www/suiboard/data/;
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}
```

## 문제 해결

### 1. 무한 리다이렉트 루프

**증상**: POST 요청 시 계속 301 리다이렉트 발생

**해결**:
```python
# main.py에서 POST 요청에 대한 리다이렉트 제거
if settings.FORCE_HTTPS and request.url.scheme == "http":
    # POST 요청은 리다이렉트하지 않음
    if request.url.path.startswith(("/admin", "/api")) and request.method == "GET":
        https_url = request.url.replace(scheme="https")
        return RedirectResponse(url=str(https_url), status_code=301)
```

### 2. SSL 인증서 오류

```bash
# Let's Encrypt 인증서 발급
sudo certbot --nginx -d marketmaker.store -d www.marketmaker.store
```

### 3. 프록시 헤더 설정

웹서버에서 다음 헤더를 설정해야 합니다:

```
X-Forwarded-Proto: https
X-Forwarded-For: client_ip
X-Forwarded-Host: marketmaker.store
Host: marketmaker.store
```

### 4. 쿠키 보안 설정

HTTPS 환경에서는 쿠키에 `Secure` 플래그를 설정:

```python
response.set_cookie(
    key="session",
    value=session_value,
    secure=True,  # HTTPS에서만 전송
    httponly=True,  # XSS 방지
    samesite="Lax"  # CSRF 방지
)
```

## 주의사항

1. **환경변수 우선순위**: `.env` 파일의 설정이 시스템 환경변수보다 우선됩니다.
2. **캐시 클리어**: 설정 변경 후 브라우저 캐시를 클리어하세요.
3. **SSL 인증서**: 프로덕션 환경에서는 유효한 SSL 인증서가 필요합니다.
4. **보안 헤더**: HTTPS 사용 시 추가 보안 헤더 설정을 권장합니다.

## 실제 적용 단계별 가이드

### 1단계: FastAPI 설정 수정

```bash
# core/settings.py 수정
FORCE_HTTPS: bool = False  # Nginx에서 처리하므로 비활성화

# main.py에 프록시 헤더 처리 추가
# 프록시 헤더 처리 (Nginx에서 전달된 HTTPS 정보 인식)
if "x-forwarded-proto" in request.headers:
    forwarded_proto = request.headers["x-forwarded-proto"]
    if forwarded_proto == "https":
        request.scope["scheme"] = "https"
```

### 2단계: 로그인 폼 URL 수정

```bash
# 모든 로그인 폼에서 하드코딩된 URL을 동적 URL로 변경
# templates/bootstrap/bbs/outlogin_before.html
# templates/basic/bbs/outlogin_before.html  
# templates/bootstrap/bbs/login_form.html

# 변경: action="/bbs/login" → action="{{ url_for('login') }}"
```

### 3단계: Nginx 설정 수정

```bash
# 백업 생성
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 설정 파일 수정 (/etc/nginx/sites-available/default)
# - X-Forwarded-Proto 헤더 추가
# - 보안 헤더 추가
# - 정적 파일 경로 설정

# 설정 테스트 및 적용
nginx -t
systemctl reload nginx
```

### 4단계: 정적 파일 권한 문제 해결

```bash
# 웹 서버용 디렉토리 생성
mkdir -p /var/www/suiboard

# 심볼릭 링크 생성
ln -s /root/suiboard/static /var/www/suiboard/static
ln -s /root/suiboard/data /var/www/suiboard/data

# root 디렉토리 실행 권한 추가
chmod 755 /root

# Nginx 설정에서 정적 파일 경로 업데이트
# alias /var/www/suiboard/static/;
# alias /var/www/suiboard/data/;

# 설정 적용
nginx -t && systemctl reload nginx
```

### 5단계: 테스트 및 검증

```bash
# 정적 파일 로드 테스트
curl -I https://marketmaker.store/static/js/jquery.min.js
curl -I https://marketmaker.store/static/js/vendor/sui-fallback.js

# 로그인 테스트
# 브라우저에서 로그인 폼 제출 테스트

# 로그 확인
tail -f /var/log/nginx/your-access.log
tail -f /root/suiboard/uvicorn.log
```

## 관련 파일

### 수정된 파일
- `core/settings.py`: 환경변수 설정
- `main.py`: 프록시 헤더 처리 미들웨어
- `templates/bootstrap/bbs/outlogin_before.html`: 동적 로그인 URL
- `templates/basic/bbs/outlogin_before.html`: 동적 로그인 URL
- `templates/bootstrap/bbs/login_form.html`: 동적 로그인 URL
- `templates/*/base_sub.html`: 동적 URL 생성
- `agent/token_gen.py`: API 토큰 생성
- `agent/board_rest_api.py`: 게시판 API 호출

### 시스템 설정 파일
- `/etc/nginx/sites-available/default`: Nginx 웹서버 설정
- `/var/www/suiboard/`: 정적 파일 심볼릭 링크 위치 