import subprocess
import sys
import re


def install_package(package):
    try:
        # 먼저 requirements.txt에 명시된 버전으로 설치 시도
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"Successfully installed {package}")
    except subprocess.CalledProcessError:
        try:
            # 실패하면 최신 버전으로 설치
            package_name = re.split(r"[=<>]", package)[0]
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "--upgrade", package_name]
            )
            print(f"Successfully installed latest version of {package_name}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {e}")


def main():
    with open("requirements.txt", "r") as f:
        requirements = f.readlines()

    for req in requirements:
        req = req.strip()
        if req and not req.startswith("#"):
            install_package(req)


if __name__ == "__main__":
    main()
