# SUIBOARD Project Integrated Documentation

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Project Structure](#2-project-structure)
3. [Main Execution Flow](#3-main-execution-flow)
4. [Environment Setup](#4-environment-setup)
   - [4.1. Installation Methods](#41-installation-methods)
   - [4.2. Database Configuration](#42-database-configuration)
   - [4.3. Local Environment Setup](#43-local-environment-setup)
5. [SUI Blockchain Integration](#5-sui-blockchain-integration)
   - [5.1. Installing Sui Client on Windows PC](#51-installing-sui-client-on-windows-pc)
   - [5.2. Sui Client Testnet Environment Setup](#52-sui-client-testnet-environment-setup)
   - [5.3. Installing SUI CLI on Ubuntu Server](#53-installing-sui-cli-on-ubuntu-server)
   - [5.4. Sui Token Operations](#54-sui-token-operations)
6. [Main Feature Implementation](#6-main-feature-implementation)
   - [6.1. SUI Wallet Address Integration](#61-sui-wallet-address-integration)
   - [6.2. zkLogin Google Integration](#62-zklogin-google-integration)
   - [6.3. Token Rewards for Post Creation](#63-token-rewards-for-post-creation)
   - [6.4. Token Reclamation on Post Deletion](#64-token-reclamation-on-post-deletion)
   - [6.5. Token Rewards for Login](#65-token-rewards-for-login)
7. [Agent Features](#7-agent-features)
   - [7.1. Naver Stock News Agent](#71-naver-stock-news-agent)
   - [7.2. Coindesk RSS Agent](#72-coindesk-rss-agent)
8. [Reference Notes](#8-reference-notes)

## 1. Project Overview

SUIBOARD is an online community bulletin board platform with SUI blockchain integration features. This project is based on GNUBOARD6 and implements a token reward system for user participation by integrating SUI blockchain functionality.

**Application Purpose**: 
- An online community bulletin board platform with SUI blockchain integration features
- Users can create posts and comments, and interact with a SUI token-based reward system

**Key Features**:
- User registration, login (standard and zkLogin), profile management
- Post creation, viewing, editing, deletion
- Comment creation, viewing, editing, deletion
- SUI wallet address registration and related features (token rewards/reclamation)
- Automated post generation agents

**Technology Stack**:
- Backend: Python, FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Template Engine: Jinja2
- Frontend: HTML, CSS (Bootstrap-based), JavaScript (jQuery)
- Blockchain: SUI (Testnet)

## 2. Project Structure

The project is located in the `/home/ubuntu/suiboard/` directory, with the following key folders and files:

**Root Directory**
- `main.py`: Main entry point for the FastAPI application
- `.env`: Defines key environment variables including database connection info and table prefixes
- `sui_integration.log`: Log file for SUI-related functionality and other key events
- `requirements.txt`: Python package dependencies list

**core/**
- `database.py`: SQLAlchemy engine creation, session management, and database connection setup
- `models.py`: SQLAlchemy database table mapping model classes
- `template.py`: Jinja2 template engine setup, custom filters, and global function registration
- `routers.py`: Main application router registration
- `formclass.py`: Pydantic models for FastAPI Form data processing
- `exception.py`: Custom exception classes and exception handlers
- `middleware.py`: FastAPI middleware definition and registration

**bbs/**
- `index.py`: Website main page routes
- `member_profile.py`: Member profile editing routes
- `board.py`: Core bulletin board functionality routes and logic
- `login.py`: Login/logout related routes
- `register.py`: User registration related routes
- `zklogin.py`: Google zkLogin authentication related routes

**templates/**
- `bootstrap/`: Currently used default theme folder
  - `base.html`: Base layout for all pages
  - `index.html`: Main page layout
  - `member/`: Member-related templates
  - `board/`: Board-related templates
  - `social/`: Social login related templates
  - `static/js/zklogin_handler.js`: zkLogin handling JavaScript

**lib/**
- `common.py`: Globally used utility functions
- `sui_service.py`: SUI blockchain integration functions
- `dependency/`: FastAPI dependency injection related functions
- `template_filters.py`, `template_functions.py`: Jinja2 template custom filters/functions

**service/**
- `agent_service.py`: Automated post generation agent service
- `board/`: Board-related services (post creation, deletion, etc.)
- `sui_transaction_log_service.py`: SUI transaction logging service

**agent/**
- `naver_stock_agent.py`: Naver stock news collection agent
- `rss_coindesk_agent.py`: Coindesk RSS feed collection agent

**suiboard_token/**
- `sources/suiboard_token.move`: SUIBOARD token Move contract

**data/**
- Image and file storage directory (automatically created during installation)

## 3. Main Execution Flow

1. **Request Reception**: User HTTP requests enter the FastAPI application.
2. **Middleware Processing**: Middlewares registered in `main.py` are executed sequentially.
3. **Routing**: Route functions are matched according to the requested URL path.
4. **Dependency Injection**: Dependencies defined in route functions are executed and necessary objects or data are passed to the function.
5. **Business Logic Processing**: Core business logic is performed within the route function.
6. **Template Rendering**: When needed, the Jinja2 template engine is used to generate HTML responses.
7. **Response Return**: Generated HTML, JSON, or redirect responses are returned to the user.

**User Authentication**:
- Session-based processing, with user ID stored in the session upon login.
- The `get_login_member` dependency is used to retrieve the currently logged-in user information.
- Google authentication via zkLogin is also supported.

**Post Creation Process**:
1. Post creation request processing (`/api/v1/boards/{bo_table}/writes` POST)
2. Validation (secret posts, content, writing permissions, etc.)
3. Data preparation
4. Post saving (`g6_write_{bo_table}` table)
5. Addition to latest posts table (`g6_board_new`)
6. Point addition (`g6_point`)
7. SUI token reward (if configured)
8. Email sending (if configured)
9. Notice post setting (if configured)
10. Cache deletion and transaction commit

## 4. Environment Setup

### 4.1. Installation Methods

**Git-based Installation**:
```bash
# Clone suiboard from Github
git clone https://github.com/gnuboard/g6.git

# Change directory to suiboard
cd suiboard

# Create virtual environment (optional)
python -m venv venv

# Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
# or
source venv\Scripts\activate

# Install required packages
python -m pip install -r requirements.txt

# Run server
# Linux
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
# or background execution
nohup uvicorn main:app --reload --host 0.0.0.0 > ~/suiboard/uvicorn.log 2>&1 &

# Windows
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

**Windows PC Development Environment Setup**:
```bash
cd C:\suiboard
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4.2. Database Configuration

The `.env` file is located in the project root, with the following key settings:

```
# Table name prefix setting
DB_TABLE_PREFIX='****************'
'****************'
DB_ENGINE='****************'
DB_USER='****************'
DB_PASSWORD='****************'
DB_HOST='****************'
DB_PORT='****************'
DB_NAME='****************'
DB_CHARSET='****************'

# Email sending settings
SMTP_SERVER="localhost"
SMTP_PORT=25
SMTP_USERNAME="account@your-domain.com"
SMTP_PASSWORD=""

# Admin theme setting
ADMIN_THEME = "basic"

# Image settings
UPLOAD_IMAGE_RESIZE = "False"
UPLOAD_IMAGE_SIZE_LIMIT = 20
UPLOAD_IMAGE_QUALITY = 80
UPLOAD_IMAGE_RESIZE_WIDTH = 1200
UPLOAD_IMAGE_RESIZE_HEIGHT = 2800

# Debug mode setting
APP_IS_DEBUG = "False"

# Website display method (responsive/adaptive)
IS_RESPONSIVE = "True"

# Cookie domain setting
COOKIE_DOMAIN = "marketmaker.store"
```

### 4.3. Local Environment Setup

To test the suiboard project in a local environment (http://localhost), the following key configuration points need to be modified or verified:

**1. Google Cloud Console OAuth 2.0 Client ID Setup**
- Authorized JavaScript origins: Add `http://localhost` and `http://localhost:port_number` for local testing in addition to existing server domains
- Authorized redirect URIs: Add `http://localhost:port_number/auth/zklogin/callback` for local testing in addition to existing server URIs

**2. Frontend JavaScript File Modification (`templates/bootstrap/static/js/zklogin_handler.js`)**
- `GOOGLE_CLIENT_ID`: Must match the OAuth 2.0 client ID set in Google Cloud Console
- `REDIRECT_URI`: Currently set to `window.location.origin + "/auth/zklogin/callback"`, which applies automatically

**3. Backend Python File Modification (`bbs/zklogin.py`)**
- `GOOGLE_CLIENT_ID`: Set environment variable (`GOOGLE_CLIENT_ID_ZKLOGIN`) or modify the placeholder in the code

**4. Database Connection Settings (`.env` file)**
- For local DB usage, modify `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, etc. to match your local environment

**5. FastAPI Application Execution**
- The port number used when running FastAPI locally must match the URI settings

## 5. SUI Blockchain Integration

### 5.1. Installing Sui Client on Windows PC

**Method 1: Using Chocolatey (Recommended, Simple)**
1. Install Chocolatey (PowerShell with administrator privileges):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force;
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. Install Sui:
   ```powershell
   choco install sui
   ```

3. Verify installation:
   ```powershell
   sui --version
   ```

**Method 2: Direct Binary Download from GitHub**
1. Access the Sui GitHub releases page
2. Select the latest release
3. Download the Windows binary (e.g., `sui-testnet-windows-amd64-vX.Y.Z.tgz`)
4. Extract the archive (e.g., to `C:\sui`)
5. Set up the PATH environment variable (add the folder path containing the sui.exe file)
6. Verify installation: `sui --version`

### 5.2. Sui Client Testnet Environment Setup

1. Check and switch network environment:
   ```bash
   sui client envs
   sui client switch --env testnet
   ```

2. Create or recover wallet:
   - Create new wallet:
     ```bash
     sui client new-address ed25519
     ```
   - Recover existing wallet (requires mnemonic):
     ```bash
     sui keytool import <INPUT_STRING> <KEY_SCHEME> [DERIVATION_PATH]
     ```

3. Check active address:
   ```bash
   sui client active-address
   ```

4. Request Testnet SUI tokens (for gas fees):
   - Use the #testnet-faucet channel on the Sui Discord server
   - Or use the Sui web Faucet: https://faucet.testnet.sui.io/

5. Check balance:
   ```bash
   sui client gas
   ```
6. Deployed package and object ID constants
   SUI_BIN_PATH = "/home/linuxbrew/.linuxbrew/bin/sui"  # SUI binary executable path
   TOKEN_PACKAGE_ID = "0x7ded54267def06202efa3e9ffb8df024d03b43f9741a9348332eee2ed63ef165"  # Token contract package ID (updated 2023-05-10)
   TOKEN_TREASURY_CAP_ID = "0x3fe97fd206b14a8fc560aeb926eebc36afd68687fbece8df50f8de1012b28e59"  # Token management authority object ID (updated 2023-05-10)
   STORAGE_PACKAGE_ID = "0x1fad2576bf6359f0fafc8c089723c80fed4784f5e3ee508b037c5280f91e543f"  # Storage contract package ID (updated 2023-05-10)
   BOARD_STORAGE_ID = "0xb07d7417fed89e22255fada05fa0e63b07465f9a05a0cb25ca66ffb71bc95902"  # Board storage object ID (updated 2023-05-10)
   CLOCK_ID = "0x6"  # SUI's time-related system object ID
   GAS_BUDGET = 100000000  # Gas budget required for transaction execution (adjust as needed)

### 5.3. Installing SUI CLI on Ubuntu Server

1. Download SUI binary:
   ```bash
   wget https://github.com/MystenLabs/sui/releases/download/testnet-v1.20.0/sui-testnet-linux-amd64-v1.20.0.tgz -O sui-binaries.tgz
   ```

2. Extract binary and move:
   ```bash
   tar -xzf sui-binaries.tgz
   mkdir -p /home/ubuntu/sui_bin
   cp sui-testnet-linux-amd64-v1.20.0/sui /home/ubuntu/sui_bin/
   chmod +x /home/ubuntu/sui_bin/sui
   ```

3. Configure SUI Client environment:
   ```bash
   /home/ubuntu/sui_bin/sui client envs
   /home/ubuntu/sui_bin/sui client switch --env testnet
   /home/ubuntu/sui_bin/sui client active-address
   ```

4. Verify application script:
   - Check that the following constants in the `/home/ubuntu/suiboard/lib/sui_service.py` file match the current SUI environment and deployed package information:
     - `SUI_BIN_PATH = "/home/ubuntu/sui_bin"`
     - `TOKEN_PACKAGE_ID`: Actual ID of the SUIBOARD token package
     - `TOKEN_TREASURY_CAP_ID`: Object ID of the SUIBOARD token's TreasuryCap
     - `GAS_BUDGET`: Appropriate gas budget

### 5.4. Sui Token Operations

**Token Issuance (Mint)**:
```bash
sui client call --package <PACKAGE_ID> --module suiboard_token --function mint --args <TREASURY_CAP_ID> <AMOUNT> <RECIPIENT_ADDRESS> --gas-budget 10000000
```

**Token Burning**:
```bash
sui client call --package <PACKAGE_ID> --module suiboard_token --function burn --args <TREASURY_CAP_ID> <COIN_OBJECT_ID> --gas-budget 10000000
```

**Token Transfer**:
```bash
sui client transfer-sui --amount <AMOUNT> --to <RECIPIENT_ADDRESS> --gas-budget 10000000
```

**Check Token Balance**:
```bash
sui client gas
```

## 6. Main Feature Implementation

### 6.1. SUI Wallet Address Integration

**Objective**: Implement functionality allowing users to input and save their SUI blockchain wallet address on the profile editing page.

**Implementation Details**:
1. **Add UI Field**: Add SUI wallet address input field to the `templates/bootstrap/member/register_form.html` template file
2. **Modify Data Model**: Add `mb_sui_address` field to the `Member` class in `core/models.py`
3. **Change Database Schema**: Add `mb_sui_address` column to the `g6_member` table
4. **Backend Save Logic**: Process in the `member_profile_save` function in `bbs/member_profile.py`

### 6.2. zkLogin Google Integration

**Objective**: Implement functionality allowing users to log in using Sui zkLogin through their Google account.

**Implementation Details**:
1. **Modify Login UI**: Add "Login with Google (zkLogin)" button to `templates/bootstrap/social/social_login.html`
2. **Frontend zkLogin Handler**: Create `templates/bootstrap/static/js/zklogin_handler.js` file
   - Import Sui SDK functions via CDN ESM modules
   - Handle Google OAuth 2.0 authentication flow
   - Configure Sui Testnet network
3. **Backend zkLogin Router**: Create `bbs/zklogin.py` file
   - Define `/api/zklogin/authenticate` endpoint
   - Verify JWT and retrieve Salt information
   - Implement automatic registration for new users and account linking
4. **Modify Data Model**: Add `mb_google_sub` field to the `Member` model

**Configuration Requirements**:
- Obtain OAuth 2.0 client ID from Google Cloud Console
- Set up authorized JavaScript origins and redirect URIs
- Add `mb_google_sub` column to the `g6_member` table

### 6.3. Token Rewards for Post Creation

**Objective**: Reward users with SUIBOARD tokens on the SUI blockchain when they create posts.

**Implementation Details**:
1. **SUI Integration Module**: Implement token issuance function in `lib/sui_service.py` file
   ```python
   def mint_suiboard_token(recipient_address: str, amount: int, sui_config: dict = None) -> str:
       """
       Issue SUIBOARD tokens to the specified address.
       
       Args:
           recipient_address: SUI address to receive tokens
           amount: Amount of tokens to issue
           sui_config: SUI settings (package ID, treasury cap ID, etc.)
           
       Returns:
           Transaction digest (hash)
       """
   ```

2. **Post Creation Service Integration**: Add token reward logic to `service/agent_service.py`
   - Execute token reward after successful DB save of post
   - Verify and validate user's `mb_sui_address`
   - Log transaction results

3. **Transaction Log Service**: Implement `service/sui_transaction_log_service.py`
   ```python
   def log_sui_transaction(db: Session, mb_id: str, wr_id: int, bo_table: str, amount: int, 
                          tx_hash: str, status: str, reason: str, error_message: str = None):
       """
       Record SUI transaction details in the DB.
       """
   ```

4. **Add Data Model**: Add `SuiTransactionlog` model to `core/models.py`
   ```python
   class SuiTransactionlog(Base):
       __tablename__ = f"{TABLE_PREFIX}sui_transaction_log"
       
       stl_id = Column(Integer, primary_key=True, autoincrement=True)
       mb_id = Column(String(20), nullable=False, index=True)
       wr_id = Column(Integer, nullable=True)
       bo_table = Column(String(20), nullable=True)
       stl_amount = Column(Integer, nullable=False, default=0)
       stl_tx_hash = Column(String(255), nullable=True)
       stl_status = Column(String(20), nullable=False, default='pending')
       stl_reason = Column(String(255), nullable=True)
       stl_error = Column(Text, nullable=True)
       stl_datetime = Column(DateTime, nullable=False, default=datetime.now)
   ```

### 6.4. Token Reclamation on Post Deletion

**Objective**: Reclaim (burn) SUIBOARD tokens that were rewarded for post creation when the post is deleted.

**Implementation Details**:
1. **Token Reclamation Workflow**:
   - When a post is deleted, check the amount of tokens rewarded for that post (query `g6_sui_transaction_log`)
   - Execute a 2-step procedure for the system to burn that amount of tokens:
     1. `mint` the amount of tokens to be burned to the system management address (create new Coin object)
     2. `burn` the created Coin object using the burn function

2. **Modify SUI Integration Module**: Implement token reclamation function in `lib/sui_service.py`
   ```python
   def reclaim_suiboard_token(amount_to_reclaim: int, sui_config: dict = None) -> str:
       """
       Reclaim (burn) the specified amount of SUIBOARD tokens.
       
       Args:
           amount_to_reclaim: Amount of tokens to reclaim
           sui_config: SUI settings (package ID, treasury cap ID, etc.)
           
       Returns:
           Burn transaction digest (hash)
       """
   ```

3. **Integrate with Post Deletion Logic**: Modify `service/board/delete_post.py`
   - Query the amount of tokens rewarded for the post to be deleted
   - If the amount is greater than 0, execute token reclamation
   - Record reclamation log in DB based on transaction result (success/failure)

4. **Transaction Log Recording**: Record reclamation details in the `g6_sui_transaction_log` table
   - `stl_reason`: "Token reclamation due to post deletion"
   - `stl_amount`: Recorded as a negative value

### 6.5. Token Rewards for Login

**Objective**: Automatically reward users with SUIBOARD tokens once per day when they log in.

**Implementation Details**:
1. **Modify Login Processing Logic**: Add token reward logic to the login success processing part of `bbs/login.py`
   - Check user's last login token reward time
   - Only reward tokens if 24 hours or more have passed
   - Record reward details in DB

2. **Token Reward Function Call**:
   ```python
   # Token reward on successful login (once per day)
   if member.mb_sui_address and (member.mb_today_login is None or 
      (datetime.now() - member.mb_today_login).total_seconds() > 86400):
       try:
           # Reward 2 tokens
           tx_hash = mint_suiboard_token(member.mb_sui_address, 2)
           # Record log
           log_sui_transaction(db, member.mb_id, None, None, 2, tx_hash, 
                              'success', 'Login reward token issuance')
           # Update last reward time
           member.mb_today_login = datetime.now()
           db.commit()
       except Exception as e:
           logger.error(f"Login token reward failed: {str(e)}")
   ```

## 7. Agent Features

### 7.1. Naver Stock News Agent

**Objective**: Automatically collect stock-related news from the Naver Finance site and post them to the bulletin board.

**Implementation Details**:
1. **Agent Script**: `agent/naver_stock_agent.py`
   - Crawl Naver Finance news pages
   - Process collected news data
   - Call post registration API

2. **Post Registration Processing**:
   - Category: Stock (stock)
   - Table: `g6_board_stock`
   - Points: Add 2 points to `g6_point` table
   - Latest Posts: Register new post in `g6_board_new` table

3. **Execution Method**:
   ```bash
   screen -S naver_stock
   python agent/naver_stock_agent.py
   # Press Ctrl+A+D to switch session to background
   ```

### 7.2. Coindesk RSS Agent

**Objective**: Automatically collect blockchain-related news from Coindesk RSS feed and post them to the bulletin board.

**Implementation Details**:
1. **Agent Script**: `agent/rss_coindesk_agent.py`
   - Parse RSS feed using feedparser library
   - Process collected news data
   - Call post registration API

2. **Post Registration Processing**:
   - Category: Blockchain (blockchain)
   - Table: `g6_board_blockchain`
   - Points: Add 2 points to `g6_point` table
   - Latest Posts: Register new post in `g6_board_new` table

3. **Execution Method**:
   ```bash
   screen -S coindesk_agent
   python agent/rss_coindesk_agent.py
   # Press Ctrl+A+D to switch session to background
   ```

## 8. Reference Notes

1. **Profile Edit Screen Text Overlap Issue**: There is a CSS style issue where the 'SUI Wallet Address' input field label and placeholder text overlap in the profile edit screen. This should be resolved by adjusting the style of the element in `templates/bootstrap/member/register_form.html` or related CSS files.

2. **Profile Edit Screen SUI Address Not Displayed (Intermittent)**: Despite the address being correctly saved in the database, there is an occasional issue where the SUI wallet address is not displayed in the input field when revisiting the profile edit screen. Browser/server cache, data loading timing/omission, form data class, etc. should be checked.

3. **DB Migration Tool**: Currently, database schema changes are managed by manual scripts. If the project scale grows or collaboration is needed in the future, it is recommended to introduce a SQLAlchemy-based database migration tool like Alembic to systematically manage schema change history.

4. **Enhanced Logging**: In addition to `sui_integration.log`, strengthening logging for major events and errors across the application can improve debugging and maintenance efficiency.

5. **SUI-Related Settings**: To use token issuance and reclamation features, the `package_id` and `treasury_cap_id` in `DEFAULT_SUI_CONFIG` in `lib/sui_service.py` must be modified to match the information of the actually deployed `suiboard_token` contract. The SUI CLI path (`sui_bin_path`) must also be configured to match the server environment.

6. **Network Consistency**: The network that the SUI CLI is connected to, `TOKEN_PACKAGE_ID`, and `TOKEN_TREASURY_CAP_ID` must all be based on the same SUI network (mainnet, testnet, or devnet) where the SUIBOARD token is actually deployed and operated.

7. **Gas Fees**: Token issuance and burning transactions consume gas fees (SUI tokens). The active address connected to the SUI CLI must have sufficient SUI tokens.
