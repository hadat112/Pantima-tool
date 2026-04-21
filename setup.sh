#!/usr/bin/env bash
set -e

# Detect Poetry binary path
POETRY_BIN="$HOME/.local/bin/poetry"
if command -v poetry &>/dev/null; then
    POETRY_BIN="$(command -v poetry)"
fi

# Detect shell config file
if [[ "$SHELL" == */zsh ]]; then
    SHELL_RC="$HOME/.zshrc"
else
    SHELL_RC="$HOME/.bashrc"
fi

add_to_path() {
    # Ensure local bin is in current PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! grep -q 'local/bin' "$SHELL_RC" 2>/dev/null; then
        echo "" >> "$SHELL_RC"
        echo '# Poetry' >> "$SHELL_RC"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
        echo "    Added Poetry to $SHELL_RC"
    fi
}

install_poetry() {
    if ! command -v poetry &>/dev/null && [[ ! -f "$POETRY_BIN" ]]; then
        echo "    Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
        POETRY_BIN="$HOME/.local/bin/poetry"
    else
        echo "    Poetry already installed: $($POETRY_BIN --version)"
    fi
}

# ── macOS ──────────────────────────────────────────────────────────────────────
setup_macos() {
    echo "==> Platform: macOS"

    echo ""
    echo "==> Checking Homebrew..."
    if ! command -v brew &>/dev/null; then
        echo "    Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [[ -f /opt/homebrew/bin/brew ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    else
        echo "    Homebrew already installed: $(brew --version | head -1)"
    fi

    echo ""
    echo "==> Checking Python 3.13..."
    if ! command -v python3.13 &>/dev/null; then
        echo "    Installing Python 3.13..."
        brew install python@3.13
    else
        echo "    Python 3.13 đã có: $(python3.13 --version)"
    fi

    echo ""
    echo "==> Checking Poetry..."
    install_poetry
    add_to_path
}

# ── Ubuntu / Debian ────────────────────────────────────────────────────────────
setup_ubuntu() {
    echo "==> Platform: Ubuntu/Debian"

    echo ""
    echo "==> Checking Python 3.13..."
    if ! command -v python3.13 &>/dev/null; then
        echo "    Installing Python 3.13..."
        sudo apt update -q
        sudo apt install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update -q
        sudo apt install -y python3.13 python3.13-venv
    else
        echo "    Python 3.13 đã có: $(python3.13 --version)"
    fi

    echo ""
    echo "==> Checking curl..."
    if ! command -v curl &>/dev/null; then
        sudo apt install -y curl
    fi

    echo ""
    echo "==> Checking Poetry..."
    install_poetry
    add_to_path
}

# ── Detect OS and run ──────────────────────────────────────────────────────────
OS="$(uname -s)"
if [[ "$OS" == "Darwin" ]]; then
    setup_macos
elif [[ "$OS" == "Linux" ]]; then
    if grep -qi "ubuntu\|debian" /etc/os-release 2>/dev/null; then
        setup_ubuntu
    else
        echo "Hệ điều hành Linux này chưa được hỗ trợ tự động. Vui lòng cài Python 3.13 và Poetry thủ công."
        exit 1
    fi
else
    echo "Hệ điều hành không hỗ trợ: $OS"
    exit 1
fi

echo ""
echo "==> Synchronizing lock file..."
"$POETRY_BIN" lock

echo ""
echo "==> Installing project dependencies..."
"$POETRY_BIN" install

echo ""
echo "==> Installing Playwright browser (Chromium)..."
"$POETRY_BIN" run playwright install chromium

echo ""
echo "==> Done. Verifying..."
"$POETRY_BIN" run tc --help

echo ""
echo "Sẵn sàng! Sử dụng lệnh: poetry run tc command"
echo "Ví dụ: poetry run tc note to-png data.csv output/png/"
echo "Lưu ý: Hãy khởi động lại Terminal (hoặc chạy 'source $SHELL_RC') để cập nhật PATH."
