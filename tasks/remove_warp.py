"""Owner-requested removal of the exact user-level Warp trial installed by this repo."""
from pathlib import Path
from pyinfra.operations import files
from manage.preflight import validate_local_context

validate_local_context()
home = Path.home()
installation = home / '.local/opt/warp-0.2026.11.11.08.17.stable.01'
launcher = home / '.local/bin/warp-terminal'
if launcher.is_symlink() and launcher.resolve() == installation / 'opt/warpdotdev/warp-terminal/warp':
    files.link(name='Remove managed Warp launcher', path=str(launcher), present=False)
entry = home / '.local/share/applications/t2-warp.desktop'
if entry.exists() and str(installation) in entry.read_text():
    files.file(name='Remove managed Warp desktop entry', path=str(entry), present=False)
files.directory(name='Remove retired Warp trial payload', path=str(installation), present=False)
settings = home / '.config/warp-terminal/settings.toml'
if settings.exists() and 'Managed by t2-mac-kde' in settings.read_text():
    files.file(name='Remove managed Warp settings', path=str(settings), present=False)
for name in ('cobalt', 'navy', 'fixedsys', 'cream', 'petrol', 't2-current'):
    theme = home / '.local/share/warp-terminal/themes' / f'{name}.yaml'
    if theme.exists() and 'Managed by t2-mac-kde' in theme.read_text():
        files.file(name=f'Remove managed Warp palette: {name}', path=str(theme), present=False)
# User-created Warp data and saved pre-t2 settings are intentionally retained.
