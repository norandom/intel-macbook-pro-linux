"""Desktop-independent command-line tools selected from the worker VM."""
from pyinfra import local
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context

validate_local_context()
local.include('tasks/package_policy.py')
install_packages(PackageRequest(
    packages=(
        "curl", "ca-certificates", "git", "jq", "unzip", "7zip", "7zip-rar", "htop", "btop",
        "neovim", "ripgrep", "fd-find", "fzf", "gcc", "make", "bat", "tree",
        "clang",  # clang/clang++ on request; GCC stays the default compiler (manage/shell_tools.py)
    ),
    source='ubuntu',
))

# Per-user settings live in ~/.config/t2-mac-kde/config.toml (manage/userconfig.py); keep a
# current, fully commented example next to it. The user's own config.toml is never written.
from pathlib import Path
from pyinfra.operations import files
from manage.userconfig import config_path
files.put(name="Settings reference: ~/.config/t2-mac-kde/config.example.toml",
          src=str(Path(__file__).resolve().parents[1] / "files/config.example.toml"),
          dest=str(config_path().with_name("config.example.toml")), mode="644", create_remote_dir=True)
