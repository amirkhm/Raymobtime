set -euo pipefail

# ---------- 
PROJECT_DIR="$(pwd)"
CONFIG_SRC="$PROJECT_DIR/data/rosslyn_QS/out/sim_default/config.yaml"  
BLENSOR_URL="https://www.blensor.org/dload/Blensor-x64.AppImage"
ROSSLYN_URL="https://nextcloud.lasseufpa.org/s/kC3pkb2AmjWDNpo/download/rosslyn_QS.zip"
# -----------

# installing UV
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Blensor download
mkdir -p "$PROJECT_DIR/softwares"
cd "$PROJECT_DIR/softwares"
wget -q --show-progress -O Blensor-x64.AppImage "$BLENSOR_URL"
chmod +x Blensor-x64.AppImage 
cd "$PROJECT_DIR"

# download rosslyn base with rt simulation
mkdir -p "$PROJECT_DIR/data"
cd "$PROJECT_DIR/data"
wget -q --show-progress -O rosslyn_QS.zip "$ROSSLYN_URL"
unzip -q rosslyn_QS.zip
rm rosslyn_QS.zip
cd "$PROJECT_DIR"

# remove yaml
rm -f "$PROJECT_DIR/config.yaml"

# copy yaml file
cp "$CONFIG_SRC" "$PROJECT_DIR/config.yaml"

# uv sync
uv sync

# activate uv venv
source "$PROJECT_DIR/.venv/bin/activate"

cd "$PROJECT_DIR"