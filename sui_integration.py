# Placeholder for SUI blockchain interaction functions
import subprocess
import json
import os

# Constants for deployed package and object IDs (replace with actual IDs)
SUI_BIN_PATH = "/home/ubuntu/sui_bin"
TOKEN_PACKAGE_ID = "0x075d5aa559a29cb77adbc4c7584d55e2c5e2a9e9a2885ae66d0ff26ffb5c5692" # From token publish
TOKEN_TREASURY_CAP_ID = "0xff43bb193ddbd293bc10e55a22c6fa086a09bbf476eacc5cb26721ce7722ce9b" # From token publish
STORAGE_PACKAGE_ID = "0x075d5aa559a29cb77adbc4c7584d55e2c5e2a9e9a2885ae66d0ff26ffb5c5692" # From storage publish
BOARD_STORAGE_ID = "0xf91ebd4806d9ab2de6421785d67c33d1fe9a6c19bc10ac5be4a3ef0bbd7613c1" # From storage publish
CLOCK_ID = "0x6"
GAS_BUDGET = 100000000 # Adjust as needed

# Ensure SUI CLI is in PATH for subprocess calls
def _run_sui_command(command_args):
    env = os.environ.copy()
    env["PATH"] = f"{SUI_BIN_PATH}:{env.get('PATH', '')}"
    try:
        print(f"Running SUI command: sui {' '.join(command_args)}")
        result = subprocess.run(["sui"] + command_args, capture_output=True, text=True, check=True, env=env)
        print(f"SUI command output: {result.stdout}")
        print(f"SUI command error: {result.stderr}")
        # Basic check for transaction success in stderr (may need refinement)
        if "error" in result.stderr.lower() and "status: \"success\"" not in result.stderr.lower():
             raise Exception(f"SUI command failed: {result.stderr}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running SUI command: {e}")
        print(f"Stderr: {e.stderr}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def mint_tokens(recipient_address: str, amount: int):
    """Mints the specified amount of Suiboard tokens to the recipient."""
    print(f"Attempting to mint {amount} tokens for {recipient_address}")
    command = [
        "client", "call",
        "--package", TOKEN_PACKAGE_ID,
        "--module", "suiboard_token",
        "--function", "mint",
        "--args",
        TOKEN_TREASURY_CAP_ID,
        str(amount),
        recipient_address,
        "--gas-budget", str(GAS_BUDGET)
    ]
    try:
        _run_sui_command(command)
        print(f"Successfully minted {amount} tokens for {recipient_address}")
        return True
    except Exception as e:
        print(f"Failed to mint tokens: {e}")
        return False

def store_post_on_sui(title: str, content: str):
    """Stores a post on the SUI blockchain using the suiboard_storage module."""
    print(f"Attempting to store post: Title='{title}'")
    # SUI CLI expects vector<u8> for string args, hex encode them
    title_hex = title.encode('utf-8').hex()
    content_hex = content.encode('utf-8').hex()

    command = [
        "client", "call",
        "--package", STORAGE_PACKAGE_ID,
        "--module", "suiboard_storage",
        "--function", "add_post",
        "--args",
        BOARD_STORAGE_ID,
        f"vector[{title_hex}]", # Pass as hex vector
        f"vector[{content_hex}]", # Pass as hex vector
        CLOCK_ID,
        "--gas-budget", str(GAS_BUDGET)
    ]
    try:
        _run_sui_command(command)
        print(f"Successfully stored post '{title}' on SUI")
        return True
    except Exception as e:
        print(f"Failed to store post on SUI: {e}")
        return False

# Example usage (for testing)
if __name__ == "__main__":
    # Replace with a valid testnet address that you control
    test_address = "0x7c723bbc6d8651376cd49b7bf0fbbb09312492ba23f4e545908f6b6b1ef2f951"

    print("Testing mint_tokens...")
    mint_success = mint_tokens(test_address, 10)
    print(f"Minting test result: {mint_success}\n")

    print("Testing store_post_on_sui...")
    store_success = store_post_on_sui("My First SUI Post", "This post is stored on the SUI blockchain!")
    print(f"Storing post test result: {store_success}")

