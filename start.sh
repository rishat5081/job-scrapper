#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"
RUN_MODE="run"
SKIP_SYSTEM_PACKAGES=0
VERIFY_INSTALL=0

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$1"
}

warn() {
  printf '\n[warn] %s\n' "$1"
}

die() {
  printf '\n[error] %s\n' "$1" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

is_macos() {
  [[ "$(uname -s)" == "Darwin" ]]
}

is_linux() {
  [[ "$(uname -s)" == "Linux" ]]
}

is_windows_shell() {
  case "${OSTYPE:-}" in
    msys*|cygwin*|win32*) return 0 ;;
    *) return 1 ;;
  esac
}

run_elevated() {
  if is_windows_shell; then
    "$@"
    return
  fi

  if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
    "$@"
  elif command_exists sudo; then
    sudo "$@"
  else
    die "Administrative privileges are required to install system packages."
  fi
}

detect_python() {
  if is_windows_shell && command_exists py; then
    if py -3.11 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1; then
      PYTHON_BIN=(py -3.11)
      return
    fi
    if py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1; then
      PYTHON_BIN=(py -3)
      return
    fi
  fi

  for candidate in python3 python; do
    if command_exists "$candidate" && "$candidate" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >/dev/null 2>&1; then
      PYTHON_BIN=("$candidate")
      return
    fi
  done

  PYTHON_BIN=()
}

ensure_homebrew() {
  if command_exists brew; then
    return
  fi

  log "Installing Homebrew from the official source..."
  NONINTERACTIVE=1 /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x /usr/local/bin/brew ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi

  command_exists brew || die "Homebrew installation failed."
}

install_system_packages_macos() {
  ensure_homebrew
  log "Installing macOS system dependencies via Homebrew..."
  brew install python@3.11 tesseract || true

  if [[ ! -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]] && ! command_exists chromium; then
    brew install --cask google-chrome || brew install --cask chromium || true
  fi
}

install_system_packages_debian() {
  log "Installing Debian/Ubuntu system dependencies..."
  run_elevated apt-get update
  run_elevated apt-get install -y python3 python3-venv python3-pip python3-dev build-essential curl tesseract-ocr
  run_elevated apt-get install -y chromium-browser || run_elevated apt-get install -y chromium || true
}

install_system_packages_fedora() {
  log "Installing Fedora/RHEL system dependencies..."
  if command_exists dnf; then
    run_elevated dnf install -y python3 python3-pip python3-devel gcc gcc-c++ make curl tesseract chromium
  else
    run_elevated yum install -y python3 python3-pip gcc gcc-c++ make curl tesseract
  fi
}

install_system_packages_arch() {
  log "Installing Arch system dependencies..."
  run_elevated pacman -Sy --noconfirm python python-pip tesseract chromium curl base-devel
}

install_system_packages_windows() {
  log "Installing Windows dependencies through official package managers..."

  if command_exists winget.exe || command_exists winget; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
      "winget install --accept-source-agreements --accept-package-agreements -e --id Python.Python.3.11 --scope machine"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
      "winget install --accept-source-agreements --accept-package-agreements -e --id Google.Chrome --scope machine"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \
      "winget install --accept-source-agreements --accept-package-agreements -e --id UB-Mannheim.TesseractOCR --scope machine" || true
    return
  fi

  if command_exists choco; then
    choco install -y python googlechrome tesseract
    return
  fi

  die "Windows bootstrap needs winget or Chocolatey available in the current shell."
}

install_system_packages() {
  if [[ "$SKIP_SYSTEM_PACKAGES" -eq 1 ]]; then
    warn "Skipping system package installation by request."
    return
  fi

  if is_macos; then
    install_system_packages_macos
    return
  fi

  if is_windows_shell; then
    install_system_packages_windows
    return
  fi

  if is_linux; then
    if command_exists apt-get; then
      install_system_packages_debian
      return
    fi
    if command_exists dnf || command_exists yum; then
      install_system_packages_fedora
      return
    fi
    if command_exists pacman; then
      install_system_packages_arch
      return
    fi
  fi

  warn "Unsupported package manager. Continuing with Python-only setup."
}

activate_venv() {
  if [[ -f "$VENV_DIR/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
    return
  fi

  if [[ -f "$VENV_DIR/Scripts/activate" ]]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
    return
  fi

  die "Could not locate the virtualenv activation script."
}

install_python_dependencies() {
  detect_python
  if [[ "${#PYTHON_BIN[@]}" -eq 0 ]]; then
    die "Python 3.11+ was not found after installation."
  fi

  log "Using Python interpreter: ${PYTHON_BIN[*]}"

  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment..."
    "${PYTHON_BIN[@]}" -m venv "$VENV_DIR"
  else
    log "Virtual environment already exists."
  fi

  activate_venv

  log "Upgrading pip tooling..."
  python -m pip install --upgrade pip setuptools wheel

  log "Installing Python dependencies..."
  python -m pip install -r "$PROJECT_ROOT/requirements.txt"
  python -m pip install -e "$PROJECT_ROOT"
}

verify_install() {
  log "Running installation verification..."
  python -c "import jobintel, flask, requests, bs4" >/dev/null
  PYTHONPATH="$PROJECT_ROOT/src" python -m pytest -q
}

start_application() {
  activate_venv
  export PYTHONPATH="$PROJECT_ROOT/src"
  log "Starting JobIntel on http://localhost:8080"
  exec python -m jobintel.api_server
}

usage() {
  cat <<'EOF'
Usage: ./start.sh [options]

Options:
  --install-only          Install everything but do not start the server.
  --skip-system-packages  Skip OS-level package installation.
  --verify                Run the test suite after installation.
  -h, --help              Show this help.

Notes:
  - On Windows, run this from Git Bash or another POSIX-compatible shell.
  - System package installation uses official package managers where possible:
    Homebrew, apt, dnf/yum, pacman, winget, or Chocolatey.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-only)
      RUN_MODE="install-only"
      ;;
    --skip-system-packages)
      SKIP_SYSTEM_PACKAGES=1
      ;;
    --verify)
      VERIFY_INSTALL=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
  shift
done

cd "$PROJECT_ROOT"

log "Bootstrapping JobIntel from $PROJECT_ROOT"
install_system_packages
install_python_dependencies

if [[ "$VERIFY_INSTALL" -eq 1 ]]; then
  verify_install
fi

if [[ "$RUN_MODE" == "install-only" ]]; then
  log "Installation completed. Start later with: ./start.sh"
  exit 0
fi

start_application
