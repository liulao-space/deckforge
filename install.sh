#!/usr/bin/env bash
# DeckForge · one-line installer
#   curl -fsSL https://raw.githubusercontent.com/liulao-space/deckforge/main/install.sh | sh
#
# Installs build.py + templates + examples into ~/.deckforge, adds a
# `deckforge` command to your PATH (via ~/.local/bin symlink), and registers
# the DeckForge agent skill into opencode / claude code skills directories.
set -e

REPO_URL="https://github.com/liulao-space/deckforge.git"
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

# ---- install as agent skill (opencode / claude code) ----
# SKILL.md 里的相对路径（build.py / templates/ / tools/）需要完整引擎，
# 所以把整个仓库（去掉 .git）同步进已存在的 skills 目录。
install_skill() {
  SKILLS_ROOT="$1"
  [ -d "$SKILLS_ROOT" ] || return 0
  DEST_DIR="$SKILLS_ROOT/deckforge"
  echo "==> installing agent skill to $DEST_DIR"
  mkdir -p "$DEST_DIR"
  (cd "$DEST" && tar --exclude .git -cf - .) | (cd "$DEST_DIR" && tar -xf -)
}

install_skill "$HOME/.config/opencode/skills"
install_skill "$HOME/.claude/skills"

echo -e "${GREEN}✔ installed${NC}"
echo "   run:  deckforge --list-presets"
echo "   try:  deckforge ~/.deckforge/examples/orca-herdr.json -o demo.html"
echo "   skill: 重启 opencode / claude code 后即可使用 DeckForge skill"
