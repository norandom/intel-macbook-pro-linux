"""Desktop-independent command-line tools selected from the worker VM."""
from pyinfra import local
from manage.packages import PackageRequest, install_packages
from manage.preflight import validate_local_context

validate_local_context()
local.include('tasks/package_policy.py')
install_packages(PackageRequest(
    packages=(
        "curl", "ca-certificates", "git", "jq", "unzip", "htop", "btop",
        "neovim", "ripgrep", "fd-find", "fzf", "gcc", "make", "bat", "tree",
    ),
    source='ubuntu',
))
