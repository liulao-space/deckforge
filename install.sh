#!/usr/bin/env bash
# DeckForge · one-line installer
#   curl -fsSL https://raw.githubusercontent.com/<you>/deckforge/main/install.sh | sh
#
# Installs build.py + templates + examples into ~/.deckforge and adds a
# `deckforge` command to your PATH (via ~/.local/bin symlink).
set -e

REPO_URL="https://github.com/<you>/deckforge.git"
DEST="$HOME/.deckforge"
BIN="$HOME/.local/bin"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo "==> DeckForge install starting"

command -v git >/dev/null 2>&1 || { echo "❌ git is required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ python3 is required"; exit 1; }

if [ -d "$DEST/.git" ]; then
  echo "==> updating existing install in $DEST"
  git -C "$DEST" pull --ff-only
else
  echo "==> cloning to $DEST"
  git clone --depth 1 "$REPO_URL" "$DEST"
fi

mkdir -p "$BIN"
cat > "$BIN/deckforge" <<'EOF'
#!/usr/bin/env bash
exec python3 "$HOME/.deckforge/build.py" "$@"
EOF
chmod +x "$BIN/deckforge"

# refresh PATH if needed
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo -e "${YELLOW}==> add to your shell: export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}" ;;
esac

echo -e "${GREEN}✔ installed${NC}"
echo "   run:  deckforge --list-presets"
echo "   try:  deckforge ~/.deckforge/examples/orca-herdr.json -o demo.html"
