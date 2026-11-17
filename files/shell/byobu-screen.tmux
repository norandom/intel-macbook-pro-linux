# Managed by t2-mac-kde: Screen prefix and Emacs copy-mode navigation.
set -g prefix C-a
set -g prefix2 F12
unbind-key -n C-a
bind-key a send-prefix
bind-key C-a send-prefix
set -g status-keys emacs
setw -g mode-keys emacs
bind-key c new-window
bind-key n next-window
bind-key p previous-window
bind-key d detach-client
bind-key [ copy-mode
bind-key s split-window -v
bind-key v split-window -h
bind-key Tab select-pane -t :.+
