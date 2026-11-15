"""Local developer tools; run as the desktop user, with sudo for apt only."""
from pyinfra import local
from manage.preflight import validate_local_context

validate_local_context()
local.include("tasks/node.py")
local.include("tasks/tools.py")
