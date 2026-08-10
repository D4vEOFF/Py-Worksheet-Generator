#!/usr/bin/env bash
#
# Removes the "wsg" command of the current user.
#
# Deletes the launcher and the block added to the shell start-up files. The
# folder with the program itself is kept.
#
# Usage: bash uninstall.sh [bin-folder]
#
set -euo pipefail

BIN_DIR="${1:-$HOME/.local/bin}"
LAUNCHER="$BIN_DIR/wsg"

MARK_START="# >>> wsg >>>"
MARK_END="# <<< wsg <<<"

# --- launcher ----------------------------------------------------------------
if [ -f "$LAUNCHER" ]; then
    rm -f "$LAUNCHER"
    echo "[wsg] launcher removed: $LAUNCHER"
else
    echo "[wsg] launcher not found: $LAUNCHER"
fi

# --- shell start-up files ----------------------------------------------------
for rc in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    [ -e "$rc" ] || continue
    if grep -qF "$MARK_START" "$rc"; then
        sed -i.wsgbak "\|$MARK_START|,\|$MARK_END|d" "$rc"
        rm -f "$rc.wsgbak"
        echo "[wsg] cleaned up      : $rc"
    fi
done

echo
echo "[wsg] done. Open a new terminal for the change to take effect everywhere."
