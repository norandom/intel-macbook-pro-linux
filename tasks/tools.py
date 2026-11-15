"""Desktop-independent command-line tools selected from the worker VM."""
from pyinfra.operations import apt

apt.packages(
    name="Install CLI tools and Neovim",
    packages=[
        "curl", "ca-certificates", "git", "jq", "unzip", "htop", "btop",
        "neovim", "ripgrep", "fd-find", "fzf", "gcc", "make", "bat", "tree",
    ],
    update=True,
    cache_time=3600,
    no_recommends=True,
    _sudo=True,
)
