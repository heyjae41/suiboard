# SUIBOARD Project Integrated Documentation

## 1. Project Overview

### 1.1. Introduction to SUIBOARD

SUIBOARD is an online community forum platform featuring integration with the SUI blockchain. Based on GNUBOARD6, this project incorporates SUI blockchain functionalities to implement a token reward system for user participation. Users can create posts and comments, interact with the SUI token-based reward system, and conveniently log in using their Google accounts via zkLogin. It also includes functionality to store post data using Walrus decentralized storage.

### 1.2. Key Features and Characteristics

- **Community Features**: Member registration, login (standard and zkLogin), profile updates, post creation/viewing/editing/deletion, comment creation/viewing/editing/deletion.
- **SUI Blockchain Integration**: SUI wallet address registration, automatic SUIBOARD token distribution for user activities (login, post creation), token reclamation upon post deletion.
- **zkLogin Authentication**: Simple login using Google accounts and SUI wallet integration.
- **Walrus Storage**: Storing post data on SUI blockchain-based decentralized storage (Currently inactive due to Ubuntu 20.04 compatibility issues; includes latest setup guide).
- **Automated Agents**: Automatic collection and posting of Naver stock news and Coindesk RSS feeds.

### 1.3. Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Template Engine**: Jinja2
- **Frontend**: HTML, CSS (Bootstrap-based), JavaScript (jQuery, Sui SDK)
- **Blockchain**: SUI (Testnet)
- **Authentication**: Session-based authentication, zkLogin (Google)
- **Web Server**: Nginx (Reverse proxy and HTTPS handling)
- **Storage**: Walrus (Decentralized storage, currently inactive)

### 1.4. Project Goals

- To build a new type of community ecosystem that provides tangible value for user participation and contribution using SUI blockchain technology.
- To operate a sustainable community platform through user activity-based token rewards, blockchain storage of content, and diverse revenue models (advertising, affiliate marketing, token listing).
- To enhance user convenience and lower the entry barrier to blockchain technology by adopting cutting-edge technologies like zkLogin.

## 2. System Architecture

### 2.1. Project Structure

The project is located in the `/home/ubuntu/suiboard/` directory (or a specified path in the local environment) and follows a modular structure.

```
suiboard/
├── .env                 # Environment variable configuration file
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python package dependency list
├── sui_integration.log  # SUI and key event log file
├── agent/               # Automation agent scripts
│   ├── naver_stock_agent.py
│   └── rss_coindesk_agent.py
├── bbs/                 # Core logic related to the bulletin board (routers)
│   ├── board.py
│   ├── index.py
│   ├── login.py
│   ├── member_profile.py
│   ├── register.py
│   └── zklogin.py
├── core/                # Core configuration and utilities
│   ├── database.py
│   ├── exception.py
│   ├── formclass.py
│   ├── middleware.py
│   ├── models.py
│   ├── routers.py
│   └── template.py
├── data/                # Storage for uploaded files and images (auto-generated)
├── lib/                 # Common libraries and services
│   ├── common.py
│   ├── sui_service.py
│   ├── walrus_service.py
│   ├── template_filters.py
│   ├── template_functions.py
│   └── dependency/
├── service/             # Business logic services
│   ├── agent_service.py
│   ├── sui_transaction_log_service.py
│   └── board/
├── suiboard_token/       # SUIBOARD token Move contract
│   └── sources/
│       └── suiboard_token.move
└── templates/           # Jinja2 template files
    └── bootstrap/       # Currently used theme
        ├── base.html
        ├── index.html
        ├── board/
        ├── member/
        ├── social/
        └── static/
            ├── css/
            ├── img/
            └── js/
                └── zklogin_handler.js
```

### 2.2. Key Directories and Files Description

- **main.py**: Initializes the FastAPI app, registers middleware/routers, server entry point.
- **.env**: Manages sensitive or environment-specific settings like database connection info, table prefix, API keys, base URL.
- **core/**: Contains core application components: database connection (`database.py`), model definitions (`models.py`), template settings (`template.py`), router integration (`routers.py`), exception handling (`exception.py`), middleware (`middleware.py`), etc.
- **bbs/**: Includes routers and core logic directly related to the user interface, such as boards, members, login.
- **lib/**: Contains reusable modules like common functions (`common.py`), SUI integration service (`sui_service.py`), Walrus integration service (`walrus_service.py`), template filters/functions, dependency injection functions.
- **service/**: Holds service classes that handle business logic for specific domains, such as post creation/deletion, transaction logging, agent execution.
- **agent/**: Standalone scripts that collect external data to automatically create posts.
- **templates/**: Jinja2 template files for generating HTML pages displayed to users.
- **suiboard_token/**: Source code for the SUIBOARD token Move smart contract deployed on the SUI blockchain.

### 2.3. Database Schema

Key tables are defined as SQLAlchemy models in `core/models.py`. Table names are prefixed with `DB_TABLE_PREFIX` defined in the `.env` file (e.g., `g6_member`).

- **g6_member**: Member information table
  - `mb_id`: Member ID (PK)
  - `mb_password`: Password (hashed)
  - `mb_name`: Name
  - `mb_email`: Email
  - `mb_sui_address`: SUI wallet address (for SUI integration)
  - `mb_google_sub`: Google account unique identifier (for zkLogin integration)
  - `mb_today_login`: Last login time (basis for login reward distribution)
  - ... other member information fields
- **g6_board**: Board settings table
- **g6_write_{bo_table}**: Post table for each board (e.g., `g6_write_free`)
  - `wr_id`: Post ID (PK)
  - `mb_id`: Author ID
  - `wr_subject`: Subject/Title
  - `wr_content`: Content
  - `wr_link1`, `wr_link2`: External links (wr_link2 can be used to store Walrus blob_id)
  - ... other post information fields
- **g6_board_new**: Latest posts table
- **g6_point**: Point history table
- **g6_sui_transaction_log**: SUI token distribution/reclamation transaction log table
  - `stl_id`: Log ID (PK)
  - `mb_id`: Related member ID
  - `wr_id`, `bo_table`: Related post information (optional)
  - `stl_amount`: Amount of token distributed/reclaimed (negative for reclamation)
  - `stl_tx_hash`: SUI transaction hash
  - `stl_status`: Transaction status ("success", "failed", "pending")
  - `stl_reason`: Reason for distribution/reclamation (e.g., "Post creation", "Login reward", "Token reclamation due to post deletion")
  - `stl_error`: Error message on failure
  - `stl_datetime`: Log timestamp
- **TokenSupply**: (Proposed) Table for managing total token supply.

### 2.4. Main Execution Flow

1.  **Request Reception**: User HTTP request is forwarded through Nginx to the FastAPI application (`main.py`).
2.  **Middleware Processing**: Registered middleware (`core/middleware.py`) executes for request preprocessing (DB session creation, proxy header processing, etc.) and response postprocessing (DB session closing, etc.).
3.  **Routing**: The router function matching the request URL (in `bbs/` or other router files) is executed.
4.  **Dependency Injection**: Dependencies required by the router function (`lib/dependency/`) are executed, passing arguments like DB session, current logged-in user info, etc.
5.  **Business Logic**: The router function or related services (`service/`) handle the core logic (data retrieval/modification, SUI integration, etc.).
6.  **Template Rendering**: If necessary, Jinja2 templates (`templates/`) are used to generate an HTML response.
7.  **Response Return**: FastAPI returns the final response (HTML, JSON, redirect, etc.) through Nginx to the user.




## 3. Environment Setup and Deployment

### 3.1. Installation Methods

The following procedure outlines how to install the SUIBOARD project in a local or server environment.

**1. Download Source Code (Using Git)**

```bash
# Navigate to desired installation path
cd /path/to/install

# Clone source code from Github (if it's a public repository)
# git clone <repository_url> suiboard
# Example (since it's based on GNUBOARD6)
git clone https://github.com/gnuboard/g6.git suiboard
cd suiboard
```

**2. Create and Activate Virtual Environment (Recommended)**

```bash
# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS
source venv/bin/activate
# Windows (cmd)
venv\Scripts\activate.bat
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Windows (Git Bash)
source venv/Scripts/activate
```

**3. Install Dependencies**

```bash
# Install packages specified in requirements.txt
python -m pip install -r requirements.txt
```

**4. Configure `.env` File**

Create a `.env` file in the project root directory and set database connection information and other necessary environment variables. (See [3.2. Database Configuration](#32-database-configuration) for details)

**5. Create Database Tables**

When the FastAPI application is first run, necessary tables can be automatically created according to SQLAlchemy model definitions. Alternatively, migration tools like Alembic can be used for management. (The current project may require automatic creation or manual creation.)

**6. Run FastAPI Server**

```bash
# Run development server (with auto-reload enabled)
# Linux/macOS/Windows
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

# Run in background for production environment (Linux example, using nohup)
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8000 > ~/suiboard/uvicorn.log 2>&1 &
# Or use process management tools like systemd, supervisor (recommended)
```

### 3.2. Database Configuration

Configure database connection information in the `.env` file in the project root. The following example is based on PostgreSQL.

```dotenv
# .env file example

# Table name prefix (e.g., g6_)
DB_TABLE_PREFIX=\'g6_\'

# Database engine (fixed as postgresql)
DB_ENGINE=\'postgresql\'

# Database username
DB_USER=\'your_db_user\'

# Database password
DB_PASSWORD=\'your_db_password\'

# Database host address (e.g., localhost or DB server IP)
DB_HOST=\'localhost\'

# Database port (PostgreSQL default: 5432)
DB_PORT=\'5432\'

# Database name
DB_NAME=\'suiboard_db\'

# Database character set (typically utf8)
DB_CHARSET=\'utf8\'

# --- Other environment variables ---
# Email sending settings (if needed)
SMTP_SERVER="localhost"
SMTP_PORT=25
SMTP_USERNAME=""
SMTP_PASSWORD=""

# Admin theme
ADMIN_THEME="basic"

# Image processing settings
UPLOAD_IMAGE_RESIZE="False"
UPLOAD_IMAGE_SIZE_LIMIT=20 # MB
UPLOAD_IMAGE_QUALITY=80
UPLOAD_IMAGE_RESIZE_WIDTH=1200
UPLOAD_IMAGE_RESIZE_HEIGHT=2800

# Debug mode (True for development, False for production)
APP_IS_DEBUG="False"

# Responsive/adaptive web settings
IS_RESPONSIVE="True"

# Cookie domain (set to your operational domain)
COOKIE_DOMAIN="yourdomain.com"

# Base URL (important for HTTPS configuration)
BASE_URL="http://localhost:8000" # Development environment example
# BASE_URL="https://yourdomain.com" # Production environment example

# Force HTTPS usage (False when handled by Nginx)
FORCE_HTTPS="False"

# Google zkLogin client ID
GOOGLE_CLIENT_ID_ZKLOGIN="YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
```

**Note**: The `.env` file contains sensitive information and should be added to the `.gitignore` file to prevent inclusion in the Git repository.

### 3.3. Local Development Environment Setup

Additional settings needed when developing and testing on a local PC.

1.  **Modify `.env` File**: Adjust `DB_*` variables to match your local PostgreSQL environment. Set `BASE_URL` to `http://localhost:8000` (or your chosen port), and `COOKIE_DOMAIN` to `localhost`. Set `APP_IS_DEBUG` to `True` to view debugging information.
2.  **Google Cloud Console Setup (zkLogin)**:
    *   Add `http://localhost` and `http://localhost:8000` (or your chosen port) to "Authorized JavaScript origins" in the OAuth 2.0 client ID settings.
    *   Add `http://localhost:8000/auth/zklogin/callback` (or your chosen port) to "Authorized redirect URIs".
3.  **Install and Configure SUI Client**: Install the SUI client on your local PC and configure it for the Testnet environment. (See [4.1.1. Windows PC Installation Guide](#411-windows-pc-installation-guide))
4.  **Run FastAPI Server**: Use the `--reload` option to automatically restart the server when code changes are made.
    ```bash
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
    ```

### 3.4. Production Environment Setup

Settings for the actual service operating environment.

1.  **Modify `.env` File**: Update `DB_*` variables with production database information. Set `BASE_URL` to your actual service domain (e.g., `https://marketmaker.store`), and set `COOKIE_DOMAIN` to the same domain. Set `APP_IS_DEBUG` to `False`. Typically, `FORCE_HTTPS` is set to `False` as HTTPS redirects are handled by Nginx.
2.  **Web Server Setup (Nginx Recommended)**: Place a web server like Nginx as a reverse proxy in front of the FastAPI application to handle static file serving, HTTPS processing, load balancing, etc. (See [3.6. Nginx Web Server Setup](#36-nginx-web-server-setup))
3.  **Process Management**: Register and manage the `uvicorn` server as a service using process management tools like `systemd` or `supervisor` for stable operation.
4.  **Install and Configure SUI Client**: Install the SUI CLI in the server environment and configure it for the required environment (Testnet or Mainnet). (See [4.1.2. Ubuntu Server Installation Guide](#412-ubuntu-server-installation-guide))
5.  **Enhance Security**: Strengthen server security with firewall settings, regular security updates, log monitoring, etc.

### 3.5. HTTPS Configuration

HTTPS is essential for secure communication in production environments. It's common to use Let's Encrypt to obtain free SSL/TLS certificates and configure them in Nginx.

**Key Configuration Steps**:

1.  **Install Certbot**: Install Certbot, a tool for issuing and renewing Let's Encrypt certificates.
    ```bash
    sudo apt update
    sudo apt install certbot python3-certbot-nginx
    ```
2.  **Issue Certificate**: Use the Nginx plugin to obtain a certificate and automatically configure Nginx.
    ```bash
    sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
    ```
    (Replace `yourdomain.com` with your actual domain)
3.  **Set Up Automatic Renewal**: Certbot typically sets up a cron job or systemd timer for automatic renewal during installation. Verify and test:
    ```bash
    sudo systemctl status certbot.timer
    sudo certbot renew --dry-run
    ```
4.  **Check Nginx Configuration**: Verify that directives like `listen 443 ssl`, `ssl_certificate`, `ssl_certificate_key` are correctly added to the Nginx configuration file (`/etc/nginx/sites-available/yourdomain.com` or `default`) modified by Certbot. (See [3.6. Nginx Web Server Setup](#36-nginx-web-server-setup))
5.  **Configure FastAPI**: Set `BASE_URL` to `https://yourdomain.com` in the `.env` file. Keep `FORCE_HTTPS` as `False`. Configure middleware in `main.py` to check the `X-Forwarded-Proto` header so FastAPI recognizes HTTPS requests. (See [7.4. Proxy Header Processing](#74-proxy-header-processing))

For detailed HTTPS configuration troubleshooting, refer to [8.3. Resolving HTTPS-related Issues](#83-resolving-https-related-issues).

### 3.6. Nginx Web Server Setup

Below is an example configuration for using Nginx as a reverse proxy to serve the FastAPI application. (File: `/etc/nginx/sites-available/yourdomain.com` or `default`)

```nginx
# HTTP (80) -> HTTPS (443) redirect server block
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Path for Let's Encrypt renewal
    location /.well-known/acme-challenge/ {
        root /var/www/html; # Default path used by Certbot
    }

    # Redirect all other requests to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS (443) server block
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificate settings (automatically added/modified by Certbot)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf; # Recommended SSL parameters
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # Diffie-Hellman parameters

    # Security headers (recommended)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Log settings
    access_log /var/log/nginx/yourdomain.access.log;
    error_log  /var/log/nginx/yourdomain.error.log;

    # Static file serving and caching
    location /static/ {
        alias /path/to/suiboard/static/; # Actual static folder path
        # alias /var/www/suiboard/static/; # When using symbolic links
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location /data/ {
        alias /path/to/suiboard/data/; # Actual data folder path
        # alias /var/www/suiboard/data/; # When using symbolic links
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Proxy forwarding to FastAPI application
    location / {
        proxy_pass http://127.0.0.1:8000; # FastAPI server address and port
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme; # Essential for HTTPS recognition
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # WebSocket support (if needed)
        # proxy_http_version 1.1;
        # proxy_set_header Upgrade $http_upgrade;
        # proxy_set_header Connection "upgrade";

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # File upload size limit (e.g., 50MB)
    client_max_body_size 50M;
}
```

**Apply Configuration**: After changing Nginx settings, check for syntax errors and restart or reload the service.

```bash
# Check configuration file syntax
sudo nginx -t

# Restart Nginx service (or reload)
sudo systemctl restart nginx
# Or
sudo systemctl reload nginx
```

## 4. SUI Blockchain Integration

This section covers the setup and understanding of SUI blockchain integration, a core feature of SUIBOARD.

### 4.1. SUI Client Installation and Configuration

The SUI client (CLI) must be installed on the SUIBOARD backend server or development environment to interact with the SUI blockchain.

#### 4.1.1. Windows PC Installation Guide

Methods for installing the SUI client in a local development environment (Windows).

**Method 1: Using Chocolatey (Recommended)**

1.  **Install Chocolatey**: Run the following command in PowerShell with administrator privileges:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```
2.  **Install Sui**:
    ```powershell
    choco install sui
    ```
3.  **Verify Installation**: Run in a new terminal window:
    ```powershell
    sui --version
    ```

**Method 2: Direct Binary Download**

1.  Visit the [Sui GitHub Releases](https://github.com/MystenLabs/sui/releases) page.
2.  Download the Windows binary for the latest release (Testnet or Mainnet version, e.g., `sui-testnet-windows-amd64-vX.Y.Z.tgz`).
3.  Extract (e.g., to `C:\sui`).
4.  Add the folder containing the `sui.exe` file (e.g., `C:\sui`) to the system environment variable `PATH`.
5.  Verify installation: Run `sui --version` in a new terminal window.

**Testnet Environment Setup (Windows)**

1.  **Check and Switch Network Environment**:
    ```bash
    sui client envs
    sui client switch --env testnet
    ```
2.  **Create or Recover Wallet**:
    *   New wallet: `sui client new-address ed25519` (securely store the mnemonic phrase)
    *   Recover existing wallet: `sui keytool import "<12_WORDS_MNEMONIC>" ed25519`
3.  **Check Active Address**: `sui client active-address`
4.  **Get Testnet SUI Tokens (Faucet)**: Use [Sui Testnet Faucet](https://faucet.testnet.sui.io/) or the `#testnet-faucet` channel in Sui Discord for gas fees.
5.  **Check Balance**: `sui client gas`

#### 4.1.2. Ubuntu Server Installation Guide

Methods for installing the SUI CLI in a production server environment (Ubuntu).

1.  **Download Binary**: (Check for the latest version, e.g., testnet-v1.20.0)
    ```bash
    # Modify URL after checking the latest version
    wget https://github.com/MystenLabs/sui/releases/download/testnet-v1.20.0/sui-testnet-linux-amd64-v1.20.0.tgz -O sui-binaries.tgz
    ```
2.  **Extract and Install**:
    ```bash
    tar -xzf sui-binaries.tgz
    # Specify installation path (e.g., /usr/local/bin or user home directory)
    sudo mv sui-testnet-linux-amd64-v1.20.0/sui /usr/local/bin/
    # Or
    # mkdir -p ~/sui_bin
    # mv sui-testnet-linux-amd64-v1.20.0/sui ~/sui_bin/
    # echo 'export PATH="$HOME/sui_bin:$PATH"' >> ~/.bashrc && source ~/.bashrc

    # Grant execution permission
    sudo chmod +x /usr/local/bin/sui
    ```
3.  **Verify Installation**: `sui --version`
4.  **Configure SUI Client Environment (Server)**:
    *   Set up the SUI client environment as the user account that runs the FastAPI application.
    *   `sui client envs`
    *   `sui client switch --env testnet`
    *   Create or recover a wallet to use on the server. **Note: Securely manage mnemonic phrases or key files in server environments.**
    *   `sui client active-address`
    *   Get Testnet SUI tokens from the Faucet if needed.
5.  **Check Application Configuration**: Verify that the `SUI_BIN_PATH` constant in the `lib/sui_service.py` file matches the actual path to the `sui` executable. (e.g., `/usr/local/bin/sui` or `/home/ubuntu/sui_bin/sui`)

### 4.2. Understanding SUI Token System

Key concepts related to the operation of the SUIBOARD token (`suiboard_token.move`).

#### 4.2.1. Package ID and Token Ownership Concepts

-   **Package ID**: The address of a smart contract (Move code) deployed on the SUI blockchain. For the SUIBOARD token, this is the ID of the package containing the `suiboard_token` module with functions like `mint`, `burn`, etc. (e.g., `0x7ded...`). Analogously, this is like the address of a 'factory' that makes tokens.
-   **Treasury Cap**: A special object that holds the authority to mint tokens. Only the owner of this object can issue new tokens. (e.g., `0x3fe9...`). This is analogous to a 'master key' for the token factory. This object is typically owned by the project manager or contract deployer.
-   **Coin Object**: The actual token object issued and stored in a user's wallet. Each coin object has a specific balance and owner information. A user's wallet address can own multiple coin objects.

**Key Point**: The Package ID itself does not own tokens. The code resides in the package, the minting authority is in the Treasury Cap object, and the actual tokens exist as Coin objects owned by user wallet addresses.

#### 4.2.2. Token Minting Process

The process of issuing new SUIBOARD tokens:

1.  **Authority Verification**: The entity owning the Treasury Cap object (e.g., the SUIBOARD server's management wallet) calls the `mint` function.
2.  **Function Call**: The `mint` function of the `suiboard_token` module is called via the `sui client call` command. Arguments passed include the Treasury Cap object ID, amount to mint, and recipient address.
    ```bash
    sui client call \
      --package <TOKEN_PACKAGE_ID> \
      --module suiboard_token \
      --function mint \
      --args <TOKEN_TREASURY_CAP_ID> <AMOUNT> <RECIPIENT_ADDRESS> \
      --gas-budget <GAS_BUDGET>
    ```
3.  **Object Creation**: The `mint` function creates a **new Coin object** with a balance equal to the `AMOUNT` passed.
4.  **Ownership Transfer**: The ownership of the created Coin object is set to the `RECIPIENT_ADDRESS`, transferring it to the user's wallet.

**Important**: Minting with `amount=100` creates **one** Coin object with a balance of 100, not 100 Coin objects with a balance of 1 each. Users can have multiple Coin objects, and SUI wallets show the sum of these balances as the total holdings.

#### 4.2.3. Token Supply Management

The current `suiboard_token.move` contract may not include a maximum supply limit feature, potentially allowing unlimited token issuance and risking inflation.

**Proposed Solutions**: (Based on SUIBOARD_Token_Explanation.md)

1.  **Smart Contract Level Restriction (Recommended)**: Add logic to track total supply (`total_supply`) and validate against a maximum supply (`MAX_SUPPLY`) in the `mint` function of the Move contract.
    ```move
    // Example: Proposed modification to suiboard_token.move
    struct TokenSupply has key {
        id: UID,
        total_minted: u64
    }

    const MAX_SUPPLY: u64 = 100000000; // Example: 100 million
    const EExceedsMaxSupply: u64 = 1;

    public fun mint(
        treasury_cap: &mut TreasuryCap<SUIBOARD_TOKEN>,
        amount: u64,
        recipient: address,
        ctx: &mut TxContext
    ) {
        // Get or create total supply object
        let supply = borrow_global_mut<TokenSupply>(ctx.sender()); // Or specific address

        // Check maximum supply
        assert!(supply.total_minted + amount <= MAX_SUPPLY, EExceedsMaxSupply);

        // Actual minting logic
        let coin = coin::mint(treasury_cap, amount, ctx);
        transfer::public_transfer(coin, recipient);

        // Update total supply
        supply.total_minted = supply.total_minted + amount;
    }
    ```
2.  **Application Level Restriction**: Check the total issuance recorded in the database before token issuance requests in the SUIBOARD backend (Python), and block issuance requests that would exceed the maximum supply. This requires a separate management table like `TokenSupply`.
    ```python
    # Example: Proposed addition to core/models.py
    class TokenSupply(Base):
        __tablename__ = f"{TABLE_PREFIX}token_supply"
        id = Column(Integer, primary_key=True)
        total_minted = Column(BigInteger, default=0)
        max_supply = Column(BigInteger, default=100000000) # 100 million
        last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Example: Proposed check logic addition to lib/sui_service.py
    def check_supply_limit(db: Session, amount_to_mint: int) -> bool:
        supply_info = db.query(TokenSupply).first()
        if not supply_info:
            # Create initial record or handle error
            raise Exception("TokenSupply information missing")
        if supply_info.total_minted + amount_to_mint > supply_info.max_supply:
            raise Exception("Maximum supply exceeded")
        return True

    def mint_suiboard_token(...):
        # ... existing logic ...
        try:
            # Check supply limit
            check_supply_limit(db, amount)

            # Execute sui client call
            # ...

            # Update supply on success
            supply_info = db.query(TokenSupply).first()
            supply_info.total_minted += amount
            db.commit()

            return tx_hash
        except Exception as e:
            # ... error handling ...
    ```
    Contract-level restriction is safer and more decentralized.

### 4.3. Walrus Storage System

Walrus is a decentralized data storage solution based on the SUI blockchain. SUIBOARD includes functionality to store post data in Walrus. (Note: This may currently be inactive due to compatibility issues with Ubuntu 20.04.)

#### 4.3.1. Understanding Walrus Architecture

-   **Walrus is not a separate blockchain**: Walrus is a storage layer built on top of the SUI blockchain.
-   **Dual Interface**: Walrus interacts in two ways:
    *   **HTTP API (Publisher/Aggregator)**: REST API endpoints used to upload and retrieve actual data (post content, etc.). (e.g., `https://publisher.walrus-testnet.walrus.space`)
    *   **SUI Smart Contract (Storage Package)**: Move contract that records and manages metadata (e.g., data identifiers, ownership proofs) on the SUI blockchain. (e.g., `0xdf90...` - latest Testnet package ID)
-   **Decentralization and Immutability**: Data is distributed across multiple storage nodes, and once stored, it is generally difficult to modify or delete.

#### 4.3.2. Data Storage and Retrieval Process

**Storage Process**: (Based on the latest Walrus CLI method)

1.  **Post Creation**: A user creates a post on SUIBOARD.
2.  **Data Preparation**: The backend server prepares the post content as a file.
3.  **Walrus CLI Call**: The server uses the `walrus store` command to upload the prepared file to the Walrus network.
    ```bash
    # Example command
    walrus store <temporary_post_file_path> --rpc-url https://fullnode.testnet.sui.io:443 --json
    ```
4.  **Blob ID Return**: Upon successful upload, the Walrus CLI returns a unique identifier called `blob_id` (e.g., `0xabcd...`).
5.  **SUI Contract Call (Optional)**: If needed, the SUI blockchain's Walrus storage contract can be called to record metadata (e.g., mapping between blob_id and post ID) on-chain.
6.  **DB Storage**: The backend stores the returned `blob_id` in the database record for that post (e.g., in the `wr_link2` field of the `g6_write_{bo_table}` table).

**Retrieval Process**: (Based on the latest Walrus CLI method)

1.  **Post View Request**: A user requests to view a specific post.
2.  **Blob ID Lookup**: The backend retrieves the `blob_id` for that post from the database.
3.  **Walrus CLI Call**: The server uses the `walrus read` command to retrieve the data corresponding to the `blob_id` from the Walrus network.
    ```bash
    # Example command
    walrus read <blob_id> --rpc-url https://fullnode.testnet.sui.io:443 --json
    ```
4.  **Data Return**: The Walrus CLI returns the retrieved data.
5.  **Content Display**: The backend displays the returned data to the user as post content.

#### 4.3.3. Latest Updates and Configuration (As of May 2025)

The Walrus system is continuously updated, and the latest Testnet settings are as follows. (Based on the `lib/walrus_service.py` file)

-   **Interaction Method Change**: Changed from the previous REST API method to using the **Walrus CLI**.
-   **Latest Package ID**: `0xdf9033cac39b7a9b9f76fb6896c9fc5283ba730d6976a2b1d85ad1e6036c3272` (Testnet)
-   **RPC URL**: Using SUI Testnet RPC URL (`https://fullnode.testnet.sui.io:443`)
-   **Walrus CLI Installation Required**: The `walrus` CLI binary must be installed in the server environment.
    ```bash
    # Example Walrus CLI installation (Linux)
    curl -L https://github.com/MystenLabs/walrus/releases/latest/download/walrus-linux-x64 -o walrus
    chmod +x walrus
    sudo mv walrus /usr/local/bin/
    ```
-   **Gas Budget**: Increased official recommended gas budget (e.g., 500,000,000 MIST)
-   **Ubuntu 20.04 Compatibility Issue**: The current SUIBOARD server environment (Ubuntu 20.04) has a GLIBC version (2.31) lower than what the latest Walrus CLI binary requires (2.32+), potentially causing compatibility issues. This may be why the Walrus feature is temporarily disabled.
    *   **Solution Options**: Upgrade server OS to Ubuntu 22.04 LTS or higher (recommended), use Docker, build from source, etc.

**Current SUIBOARD Configuration (`lib/walrus_service.py`)**: Check if the latest information is reflected in the `DEFAULT_WALRUS_CONFIG` dictionary, and whether the `enabled` flag is set to `True` or `False`.

```python
# lib/walrus_service.py example (reflecting latest settings)
DEFAULT_WALRUS_CONFIG = {
    "package_id": "0xdf9033cac39b7a9b9f76fb6896c9fc5283ba730d6976a2b1d85ad1e6036c3272",
    "sui_rpc_url": "https://fullnode.testnet.sui.io:443",
    "sui_bin_path": "/usr/local/bin/sui", # Verify actual sui path
    "walrus_binary": "/usr/local/bin/walrus", # Verify actual walrus path
    "gas_budget": 500000000,
    "enabled": False, # May be disabled due to Ubuntu 20.04 compatibility issues
}
```



## 5. Main Feature Implementation

Detailed explanation of SUIBOARD's core feature implementations.

### 5.1. SUI Wallet Address Integration

Users can register their SUI wallet address in their profile, which is used for token distribution/reclamation and other SUI-related features.

-   **UI**: A SUI wallet address input field has been added to the member information edit page (`templates/bootstrap/member/register_form.html`).
-   **Data Model**: The `mb_sui_address` field (String type) has been added to the `Member` model in `core/models.py`.
-   **Database**: The `mb_sui_address` column has been added to the `g6_member` table.
-   **Backend Logic**: When processing member information update requests (the `member_profile_save` function in `bbs/member_profile.py`), the validity of the entered SUI address is checked and stored in the database.

### 5.2. zkLogin Google Integration

Users can log in to SUIBOARD using their Google account without creating a separate wallet, and use SUI features.

-   **UI**: A "Login with Google (zkLogin)" button has been added to the login page (`templates/bootstrap/social/social_login.html`).
-   **Frontend**: The `templates/bootstrap/static/js/zklogin_handler.js` file handles the Google OAuth 2.0 authentication flow and performs zkLogin-related tasks using the Sui SDK (loaded via CDN). It sends the user's Google ID token to the backend.
-   **Backend**: The `/api/zklogin/authenticate` endpoint is defined in the `bbs/zklogin.py` file.
    *   It verifies the Google ID token received from the frontend.
    *   It uses Salt information obtained from the Sui developer portal to generate a unique SUI address for the user.
    *   It checks if the user is existing based on the Google account unique identifier (`sub`) in the `g6_member` table.
    *   For new users, it automatically processes registration and stores the Google `sub` value in the `mb_google_sub` field.
    *   For existing users, it processes login for that account.
-   **Data Model**: The `mb_google_sub` field (String type) has been added to the `Member` model.
-   **Database**: The `mb_google_sub` column has been added to the `g6_member` table.
-   **Configuration**: The OAuth 2.0 client ID issued from the Google Cloud Console must be set in the `.env` file or in the code.

### 5.3. Token Rewards for Post Creation

SUIBOARD tokens are distributed as rewards for community activities (post creation).

-   **Trigger**: When a user successfully creates a post (in the `save_write` function of `service/board/create_post.py` or related service logic).
-   **Conditions**: Checking conditions for token distribution:
    *   Must be a logged-in member.
    *   A valid SUI wallet address (`mb_sui_address`) must be registered in the member information.
    *   Must be an original post, not a reply (can be changed according to settings).
    *   (Previous) Agent exclusion condition has been removed (agents can now receive tokens).
-   **SUI Integration**: Calls the `mint_suiboard_token` function in `lib/sui_service.py` to mint a specified amount (e.g., 1 token) of SUIBOARD tokens to the user's `mb_sui_address`.
-   **Log Recording**: Records the token distribution transaction result (success/failure, transaction hash, error message, etc.) in the `g6_sui_transaction_log` table (using `service/sui_transaction_log_service.py`).
-   **Point Distribution**: May also distribute points through the existing GNUBOARD point system (`g6_point` table).

### 5.4. Token Reclamation on Post Deletion

To prevent abuse, tokens distributed for post creation are reclaimed (burned) when the post is deleted.

-   **Trigger**: When a user deletes a post (in the related logic of `service/board/delete_post.py`).
-   **Target Verification**: Checks the `g6_sui_transaction_log` table for previous token distribution records related to the post being deleted (`wr_id`, `bo_table`).
-   **Reclamation Logic**: If the distributed token amount (`stl_amount`) is greater than 0, calls the `reclaim_suiboard_token` function (or similar function) in `lib/sui_service.py`.
    *   **Two-Step Burning**: The current implementation may not directly retrieve tokens from the user's wallet, but instead **newly mint** the amount to be reclaimed to the system management wallet, then immediately **burn** that coin object. This may be easier to implement than directly deducting tokens from the user's wallet.
    *   `sui client call ... --function mint ...` (mint to admin address)
    *   `sui client call ... --function burn ...` (burn the just-minted coin object)
-   **Log Recording**: Records the token reclamation transaction result (success/failure, transaction hash, etc.) in the `g6_sui_transaction_log` table. The `stl_amount` is recorded as a negative value, and `stl_reason` as something like "Token reclamation due to post deletion".

### 5.5. Token Rewards for Login

Tokens are distributed upon login to encourage regular visits.

-   **Trigger**: When a user successfully logs in (in the login processing logic of `bbs/login.py`).
-   **Conditions**: Once-per-day distribution limit:
    *   The logged-in member must have a valid SUI wallet address (`mb_sui_address`).
    *   Checks the `mb_today_login` field (last login time) in the `g6_member` table, and only distributes if at least 24 hours have passed since the last login.
-   **SUI Integration**: Calls the `mint_suiboard_token` function in `lib/sui_service.py` to mint a specified amount (e.g., 2 tokens) of SUIBOARD tokens to the user's `mb_sui_address`.
-   **Log Recording and Time Update**: Records the token distribution transaction result in the `g6_sui_transaction_log` table, and upon success, updates the `mb_today_login` field in the `g6_member` table to the current time.

## 6. Automated Agents

Agent functionality that automatically collects external information to create posts, helping secure initial content and activate the community.

### 6.1. Naver Stock News Agent

-   **Script**: `agent/naver_stock_agent.py`
-   **Function**: Crawls major news updates from Naver Finance (finance.naver.com) to create stock-related news posts.
-   **Target Board**: Stock board (e.g., `bo_table='stock'`)
-   **Operation**: Periodically checks the Naver Finance news page, extracts title and summary content of new news, and calls SUIBOARD's post creation API or internal function to register posts.
-   **Rewards**: Agent accounts (`mb_id` with a specific pattern, e.g., 'gg_') can also receive points and SUIBOARD tokens for post creation depending on settings (currently set to receive).

### 6.2. Coindesk RSS Agent

-   **Script**: `agent/rss_coindesk_agent.py`
-   **Function**: Parses the RSS feed provided by the Coindesk website to create posts with the latest blockchain and cryptocurrency news.
-   **Target Board**: Blockchain board (e.g., `bo_table='blockchain'`)
-   **Operation**: Uses the `feedparser` library to periodically access the Coindesk RSS URL, checks for new news items, extracts title, link, and summary content, and registers posts.
-   **Rewards**: Like the Naver stock news agent, can receive point and token rewards depending on settings.

### 6.3. Agent Execution and Management

Agent scripts are independent Python files that need to run continuously in the background on the server.

-   **Execution Methods (Linux)**:
    *   **Using `screen` or `tmux`**: Maintains terminal sessions while running in the background
        ```bash
        # Start screen session
        screen -S stock_agent
        # Activate virtual environment (if needed)
        source /path/to/suiboard/venv/bin/activate
        # Run agent
        python /path/to/suiboard/agent/naver_stock_agent.py
        # Detach session (background): Ctrl + A, D

        # Run other agents similarly
        screen -S coindesk_agent
        python /path/to/suiboard/agent/rss_coindesk_agent.py
        # Ctrl + A, D

        # Check running sessions: screen -ls
        # Reattach to session: screen -r stock_agent
        ```
    *   **Using `nohup`**: Continues running after terminal closure
        ```bash
        nohup python /path/to/suiboard/agent/naver_stock_agent.py > ~/stock_agent.log 2>&1 &
        nohup python /path/to/suiboard/agent/rss_coindesk_agent.py > ~/coindesk_agent.log 2>&1 &
        # Check running processes: ps aux | grep agent.py
        # Terminate: kill <PID>
        ```
    *   **Using `systemd` or `supervisor` (Recommended)**: Register as services for stable management (automatic restart, log management, etc.)
-   **Frequency Setting**: Use `time.sleep()` within agent scripts to adjust execution frequency, or set up `cron` jobs to run scripts periodically.
-   **Log Checking**: Errors or status during agent execution should be recorded in standard output/error or separate log files for monitoring.

## 7. Security and Performance Optimization

Security and performance-related settings for stable and secure service operation.

### 7.1. HTTPS Security Configuration

-   **SSL/TLS Application**: Configure SSL/TLS certificates obtained through Let's Encrypt in Nginx to encrypt all communications. (See [3.5. HTTPS Configuration](#35-https-configuration))
-   **Use Latest Protocols**: Configure to use only secure latest protocols, such as `ssl_protocols TLSv1.2 TLSv1.3;`.
-   **Strong Cipher Suites**: Use the `ssl_ciphers` directive to allow only high-security encryption methods. (Use Let's Encrypt recommended settings)
-   **Security Headers**: Add the following HTTP security headers in Nginx configuration to defend against web vulnerabilities:
    *   `Strict-Transport-Security` (HSTS): Forces browsers to always connect via HTTPS.
    *   `X-Frame-Options`: Controls frame insertion to prevent Clickjacking attacks (`DENY` recommended).
    *   `X-Content-Type-Options`: Prevents browsers from ignoring `Content-Type` and MIME sniffing (`nosniff`).
    *   `X-XSS-Protection`: Activates browsers' built-in XSS filter functionality (`1; mode=block`).
    *   `Referrer-Policy`: Controls Referer header transmission policy to prevent information leakage (`strict-origin-when-cross-origin` recommended).

### 7.2. Static File Caching

Utilize browser caching for static files like CSS, JavaScript, images that change infrequently to improve loading speed and reduce server load.

-   **Nginx Configuration**: Use the `expires` directive in the `location` block to set a long cache validity period (e.g., `1y` - 1 year), and use the `add_header Cache-Control` directive to specify the cache policy (`public, immutable`).
    ```nginx
    location /static/ {
        alias /path/to/suiboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off; # Disable access logs for static files as they're unnecessary
    }
    location /data/ { ... }
    ```
-   **Cache Invalidation**: When static file content changes, use methods like including version information or hash values in filenames (changing filenames) or adding query parameters when linking in HTML to prompt browsers to download new files.

### 7.3. Cookie Security Settings

Enhance the security of cookies used for session management, etc.

-   **`Secure` Flag**: In HTTPS environments, set the `Secure` flag on cookies to ensure they are only transmitted over encrypted connections (HTTPS).
-   **`HttpOnly` Flag**: Set the `HttpOnly` flag to prevent JavaScript from accessing cookies, protecting against cookie theft through XSS (Cross-Site Scripting) attacks.
-   **`SameSite` Attribute**: Set the `SameSite` attribute on cookies to prevent CSRF (Cross-Site Request Forgery) attacks (`Lax` or `Strict`).
-   **FastAPI Configuration**: Set related parameters when using FastAPI's `response.set_cookie()` function.
    ```python
    response.set_cookie(
        key="session_id",
        value=session_value,
        secure=True,  # Only transmitted over HTTPS (can add condition: request.url.scheme == 'https')
        httponly=True,
        samesite="Lax"
    )
    ```

### 7.4. Proxy Header Processing

Settings to correctly recognize original client IP addresses or request protocols (HTTP/HTTPS) when running the FastAPI application behind a reverse proxy like Nginx.

-   **Nginx Configuration**: Use the `proxy_set_header` directive to pass necessary headers to FastAPI.
    ```nginx
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    ```
-   **FastAPI Configuration**: Check the `X-Forwarded-Proto` header in middleware registered in `main.py` to set `request.scope["scheme"]` to `https`, allowing functions like `url_for` to generate correct HTTPS URLs.
    ```python
    # main.py middleware example
    @app.middleware("http")
    async def https_redirect_middleware(request: Request, call_next):
        if "x-forwarded-proto" in request.headers:
            if request.headers["x-forwarded-proto"] == "https":
                request.scope["scheme"] = "https"
        response = await call_next(request)
        return response
    ```
    Using the `--proxy-headers` option when running Uvicorn is another method.

### 7.5. File Upload Security

Security settings for files (images, etc.) uploaded by users.

-   **Upload Size Limit**: Use the `client_max_body_size` directive in Nginx configuration to limit the maximum size of uploadable files (e.g., `50M`). File size limit logic can also be added on the FastAPI side.
-   **File Extension and Type Checking**: Check the extension and MIME type of uploaded files on the server side to process only allowed types of files. This prevents the upload of malicious script files.
-   **File Storage Path**: It's good practice to store uploaded files in a secure path outside the web root directory, preventing direct access by the web server. File access should only occur through the application.
-   **Filename Processing**: Instead of using filenames uploaded by users directly, generate and store new filenames in a secure way on the server. (e.g., using UUID)

## 8. Troubleshooting and Operation Guide

Major issues that may occur during SUIBOARD operation, their solutions, and operation tips.

### 8.1. Resolving Token Reward Failures

**Symptom**: SUIBOARD tokens are not properly distributed during post creation or login, and failure logs are recorded in the `g6_sui_transaction_log` table or no logs are recorded at all.

**Cause Analysis**: (Based on SUIBOARD_Token_Explanation.md)

1.  **SUI Client Path Error**: The `SUI_BIN_PATH` setting in `lib/sui_service.py` differs from the actual `sui` executable path.
2.  **SUI Environment Configuration Error**: SUI client environment (active address, network, etc.) is not properly configured on the server.
3.  **Insufficient Gas**: The management wallet lacks sufficient gas (SUI tokens) needed for SUI transaction execution.
4.  **Incorrect Argument Passing**: Recipient address (`recipient_address`), token amount (`amount`), package ID, treasury cap ID, etc. are incorrect when calling the `mint_suiboard_token` function.
5.  **Network Error**: Communication issues with SUI Testnet/Mainnet nodes.
6.  **Contract Error**: Issues with the deployed SUIBOARD token contract itself (low probability).
7.  **Application Logic Error**: Errors or insufficient exception handling in token distribution condition (SUI address verification, etc.) logic.
8.  **Permission Issue**: The FastAPI execution user account lacks permission to execute the `sui` command.

**Resolution Steps**: (Log checking essential)

1.  **Check Logs**: Check error messages in the `sui_integration.log` file and the `g6_sui_transaction_log` table.
2.  **Verify SUI Client Path**: Check `SUI_BIN_PATH` in `lib/sui_service.py` and verify it matches the actual path.
3.  **Check Server SUI Environment**: Log in as the FastAPI execution user and run `sui client envs`, `sui client active-address`, `sui client gas` commands to check environment and balance.
4.  **Test Manual Minting**: Directly execute the `sui client call ... mint ...` command in the server terminal to test if token issuance works normally.
5.  **Check Argument Values**: Debug the values of `recipient_address`, `amount`, `TOKEN_PACKAGE_ID`, `TOKEN_TREASURY_CAP_ID` passed when calling the `mint_suiboard_token` function in the code.
6.  **Check Network Status**: Check the SUI network status page or test node connection with `ping`, etc.
7.  **Review Application Logic**: Review related Python code including token distribution conditions and exception handling.

### 8.2. Resolving Walrus Storage Failures

**Symptom**: Data storage to Walrus storage fails during post creation, and related error logs appear (e.g., "JSON parsing error", "CLI execution error", "Compatibility error").

**Cause Analysis**: (Based on SUIBOARD_Token_Explanation.md)

1.  **Walrus CLI Not Installed or Path Error**: The `walrus` CLI is not installed on the server, or the `walrus_binary` path setting in `lib/walrus_service.py` is incorrect.
2.  **RPC URL Error**: The `sui_rpc_url` setting is incorrect (Latest Testnet: `https://fullnode.testnet.sui.io:443`).
3.  **GLIBC Compatibility Issue (Ubuntu 20.04)**: The server OS's GLIBC version (2.31) is lower than what the Walrus CLI requires (2.32+), making execution impossible.
4.  **Insufficient Gas**: Insufficient gas for Walrus-related SUI transactions (if needed).
5.  **Network Error**: Communication issues with SUI RPC nodes or the Walrus network.
6.  **Walrus Service Issue**: Temporary outage of the Walrus Testnet/Mainnet service.
7.  **Data Error**: Issues with the format of data being stored in Walrus.

**Resolution Steps**: (Log checking essential)

1.  **Check Logs**: Check Walrus-related error messages in the `sui_integration.log` file.
2.  **Check Walrus Activation Status**: Verify if the `DEFAULT_WALRUS_CONFIG["enabled"]` value in `lib/walrus_service.py` is `True`.
3.  **Check GLIBC Version (Ubuntu 20.04)**: Check GLIBC version with the `ldd --version` command. If it's 2.31, compatibility issues are likely.
    *   **Solution**: OS upgrade (22.04+), use Docker, or keep Walrus functionality disabled.
4.  **Check Walrus CLI Installation and Path**: Verify installation with the `which walrus` command and check the `walrus_binary` path setting.
5.  **Test Manual Storage**: Directly execute the `walrus store <test_file> --rpc-url ...` command in the server terminal to test storage.
6.  **Check RPC URL and Network**: Verify the configured RPC URL and check SUI network status.
7.  **Check Walrus Official Documentation/Community**: Check for Walrus service status or known issues.

### 8.3. Resolving HTTPS-related Issues

**Symptom**: After HTTPS configuration, site access fails, CSS/JS fails to load, login causes infinite redirects, "Method Not Allowed" errors, etc.

**Cause Analysis**: (Based on HTTPS_Configuration_Guide.md)

1.  **Nginx Configuration Error**: `listen 443 ssl`, certificate path, `server_name`, proxy settings (`proxy_pass`, `proxy_set_header`), etc. are incorrect.
2.  **SSL Certificate Error**: Certificate file path is incorrect, expired, or invalid.
3.  **Proxy Header Missing/Error**: Nginx doesn't forward the `X-Forwarded-Proto` header, or FastAPI doesn't process it, causing protocol mismatch.
4.  **FastAPI URL Generation Error**: Functions like `url_for` generate HTTP URLs, causing Mixed Content errors or redirect issues.
5.  **Hardcoded URLs**: `http://` URLs are hardcoded in templates or JavaScript code.
6.  **Cookie Setting Error**: Issues with cookies that don't have the `Secure` flag set.
7.  **Firewall Issue**: Port 443 is blocked by the firewall.

**Resolution Steps**: (Check Nginx logs, browser developer tools)

1.  **Validate Nginx Configuration**: Check for syntax errors with the `sudo nginx -t` command. Review configuration file content. (See [3.6. Nginx Web Server Setup](#36-nginx-web-server-setup))
2.  **Check SSL Certificate**: Verify certificate file existence and validity period. Check externally with `openssl s_client -connect yourdomain.com:443`.
3.  **Check Proxy Headers**: Verify inclusion of `proxy_set_header X-Forwarded-Proto $scheme;` in Nginx configuration. Check header processing logic in FastAPI middleware. (See [7.4. Proxy Header Processing](#74-proxy-header-processing))
4.  **Check URL Generation Method**: Verify use of the `url_for` function in templates. Check if JavaScript uses `request.url.scheme`, `request.url.netloc`, etc. to dynamically generate URLs.
5.  **Search for Hardcoded URLs**: Search for `http://` throughout the code and modify to use dynamic URL generation.
6.  **Check Cookie Settings**: Check the `Set-Cookie` header in FastAPI responses to verify inclusion of the `Secure` flag.
7.  **Check Firewall**: Verify port 443 allowance in server firewall (ufw, etc.) settings.
8.  **Browser Developer Tools**: Check for Mixed Content errors in the Console tab. Check redirect process and request/response headers in the Network tab.

### 8.4. Resolving Static File Permission Issues

**Symptom**: Static files (CSS, JavaScript, images) fail to load when accessing the website, resulting in 403 Forbidden or 404 Not Found errors.

**Cause Analysis**: (Based on HTTPS_Configuration_Guide.md)

1.  **Insufficient File System Permissions**: The Nginx execution user (typically `www-data`) lacks read permission for static files (`static/`, `data/` directories and files within). This is especially likely if the project path is in a location with access restrictions, like the root home directory.
2.  **Nginx Path Configuration Error**: The `alias` or `root` directive path in the `location /static/` or `location /data/` block in the Nginx configuration file doesn't match the actual file system path.
3.  **SELinux/AppArmor**: Security modules blocking Nginx's file access (uncommon).

**Resolution Steps**: (Check Nginx error logs)

1.  **Check Nginx Error Logs**: Look for "Permission denied" or similar error messages in the `/var/log/nginx/yourdomain.error.log` file.
2.  **Check File System Permissions**: Check permissions of `/path/to/suiboard/static` and parent directories with `ls -la`. Verify if the Nginx execution user (`www-data`) can access the path (execution permission `x`) and read files (read permission `r`).
3.  **Solution (Recommended: Symbolic Links)**:
    *   Create a directory in a path accessible to the web server (e.g., `/var/www/`): `sudo mkdir -p /var/www/suiboard`
    *   Create symbolic links to the original static file directories:
        ```bash
        sudo ln -s /path/to/suiboard/static /var/www/suiboard/static
        sudo ln -s /path/to/suiboard/data /var/www/suiboard/data
        ```
    *   Adjust permissions of parent directories if needed (consider security implications): e.g., `sudo chmod o+x /root`
    *   Update Nginx configuration: Modify `alias` path to the symbolic link path (e.g., `alias /var/www/suiboard/static/;`)
4.  **Solution (File Copying - Not Recommended)**:
    *   Copy static files to a web server accessible path: `sudo cp -r /path/to/suiboard/static /var/www/suiboard/`
    *   Change ownership/permissions of copied files: `sudo chown -R www-data:www-data /var/www/suiboard/static`
    *   Update Nginx configuration: Modify `alias` path to the copied path.
5.  **Restart/Reload Nginx**: After configuration changes, `sudo systemctl reload nginx`.

### 8.5. Log Monitoring and Analysis

Regularly checking and analyzing logs is important for stable operation and quick identification of issues.

-   **FastAPI/Uvicorn Logs**: Application-level logs recorded in standard output/error or specified files (e.g., `~/suiboard/uvicorn.log`) when running `uvicorn`. Includes request processing details, Python errors, debug information, etc.
-   **SUI Integration Logs**: Detailed logs and errors of blockchain-related operations like SUI token distribution/reclamation and Walrus storage recorded in the `sui_integration.log` file.
-   **Nginx Access Logs**: Web server access logs recorded in the `/var/log/nginx/yourdomain.access.log` file. Shows client IP, request time, request URL, response code, User-Agent, etc.
-   **Nginx Error Logs**: Web server error logs recorded in the `/var/log/nginx/yourdomain.error.log` file. Records serious issues like configuration errors, permission problems, backend connection failures, etc.
-   **Database Logs**: Check PostgreSQL server logs to identify database-related issues like slow queries, connection errors, etc.
-   **System Logs**: Check system-level logs like `/var/log/syslog` to identify OS-related issues or resource shortage phenomena.

**Log Analysis Tools**: For large-scale log analysis, consider adopting log collection and visualization tools like the ELK stack (Elasticsearch, Logstash, Kibana) or Grafana Loki, in addition to basic commands like `grep`, `awk`, `tail`.

## 9. Reference Notes

### 9.1. Known Issues

-   **Text Overlap in Profile Edit Screen**: CSS style issue where the 'SUI Wallet Address' input field label and placeholder text overlap in the member information edit screen. (Requires modification of `templates/bootstrap/member/register_form.html` or related CSS)
-   **Walrus Ubuntu 20.04 Compatibility**: The latest Walrus CLI requires GLIBC 2.32 or higher, making it incompatible with Ubuntu 20.04 (GLIBC 2.31). (Requires OS upgrade or Docker usage)
-   **Lack of Token Total Supply Limit**: The current SUIBOARD token contract may not have a total supply limit feature. (See [4.2.3. Token Supply Management](#423-token-supply-management))

### 9.2. Future Improvement Plans

-   Reactivate Walrus functionality (after server environment improvement)
-   Implement token total supply limit feature (contract modification or application level)
-   Enhance admin page functionality (SUI transaction monitoring, user management, etc.)
-   Write test code and build CI/CD pipeline
-   Support SUI Mainnet
-   Support multiple languages

### 9.3. Useful Command Collection

-   **Run FastAPI Server (Development)**: `python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
-   **Test Nginx Configuration**: `sudo nginx -t`
-   **Restart/Reload Nginx**: `sudo systemctl restart nginx` / `sudo systemctl reload nginx`
-   **Check SUI Environment**: `sui client envs`, `sui client active-address`, `sui client gas`
-   **Manual SUI Token Minting**: `sui client call --package <PKG_ID> --module suiboard_token --function mint --args <CAP_ID> <AMOUNT> <ADDR> --gas-budget <BUDGET>`
-   **Manual Walrus Storage**: `walrus store <FILE> --rpc-url <RPC_URL> --json`
-   **Manual Walrus Retrieval**: `walrus read <BLOB_ID> --rpc-url <RPC_URL> --json`
-   **Real-time Log Checking**: `tail -f /path/to/logfile.log`
-   **Process Checking**: `ps aux | grep uvicorn`, `ps aux | grep agent.py`

### 9.4. Reference Materials and Links

-   [Sui Documentation](https://docs.sui.io/)
-   [FastAPI Documentation](https://fastapi.tiangolo.com/)
-   [GNUBOARD6 GitHub](https://github.com/gnuboard/g6)
-   [Walrus Documentation](https://docs.walrus.site/)
-   [zkLogin Documentation](https://docs.sui.io/concepts/cryptography/zklogin)
-   [Let's Encrypt](https://letsencrypt.org/)
-   [Nginx Documentation](https://nginx.org/en/docs/)
-   (Original document links)
    -   fmkorea.com estimated revenue: https://www.fmkorea.com/best/6095883036
    -   Blockchain-based community case (Steemit): https://www.kbfg.com/kbresearch/cmm/fms/FileDown.do?atchFileId=FILE_00000001003693&fileSn=0
    -   Token economy cases: https://it.chosun.com/news/articleView.html?idxno=2018070100371
    -   Ad revenue calculation method: https://newsinitiative.withgoogle.com/ko-kr/resources/trainings/estimate-ad-revenue/
