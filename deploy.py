"""Local developer tools; run as the desktop user, with sudo for apt only."""
from pyinfra import local

local.include("tasks/node.py")
local.include("tasks/tools.py")
