"""User-only Screen-style bindings for Zellij and Byobu (tmux backend)."""
import os
from pathlib import Path
from pyinfra.operations import files
from manage.preflight import validate_local_context

validate_local_context()
home = Path.home()
src = Path(__file__).resolve().parents[1] / "files/shell"
config = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))
byobu = Path(os.environ.get("BYOBU_CONFIG_DIR", str(home / ".byobu" if (home / ".byobu").is_dir() else config / "byobu")))
for directory in (config / "zellij", byobu):
    files.directory(name=f"Multiplexer config: {directory}", path=str(directory))
# Zellij reads the FIRST keybinds node. Prepend our block before any existing one;
# preserve the old node and other preferences for rollback.
files.block(name="Zellij: Screen Ctrl+A bindings", path=str(config / "zellij/config.kdl"),
            marker="// {mark} t2-mac-kde: Screen keys", content=(src / "zellij-screen.kdl").read_text(),
            before=True, line=r"^\s*keybinds", backup=True, try_prevent_shell_expansion=True)
files.block(name="Byobu: tmux backend", path=str(byobu / "backend"),
            marker="# {mark} t2-mac-kde: backend", content="BYOBU_BACKEND=tmux",
            backup=True, try_prevent_shell_expansion=True)
files.block(name="Byobu: Screen keys with Emacs copy mode", path=str(byobu / ".tmux.conf"),
            marker="# {mark} t2-mac-kde: Screen keys", content=(src / "byobu-screen.tmux").read_text(),
            backup=True, try_prevent_shell_expansion=True)
