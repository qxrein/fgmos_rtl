#!/usr/bin/env bash
# Source before make magic / magic-extract (add to ~/.bashrc if desired)
export PDK_ROOT="${PDK_ROOT:-$HOME/share/pdk}"
export PDK="${PDK:-sky130A}"
export STD_CELL_LIBRARY="${STD_CELL_LIBRARY:-sky130_fd_sc_hd}"

if [[ ! -d "$PDK_ROOT/$PDK/libs.tech/magic" ]]; then
  echo "Sky130 PDK not enabled at PDK_ROOT=$PDK_ROOT" >&2
  echo "  venv/bin/volare fetch 8afc8346a57fe1ab7934ba5a6056ea8b43078e71 --pdk sky130 --pdk-root \"\$PDK_ROOT\"" >&2
  echo "  venv/bin/volare enable 8afc8346a57fe1ab7934ba5a6056ea8b43078e71 --pdk sky130 --pdk-root \"\$PDK_ROOT\"" >&2
  return 1 2>/dev/null || exit 1
fi

# Prefer locally built Magic (>= 8.3.411) over distro 8.3.105
if [[ -x "$HOME/local/bin/magic" ]]; then
  export PATH="$HOME/local/bin:$PATH"
fi

echo "PDK_ROOT=$PDK_ROOT  PDK=$PDK  magic=$(command -v magic 2>/dev/null || echo missing) $(magic --version 2>/dev/null | head -1 || true)"
