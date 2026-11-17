"""Pinned command entry for fish; native terminal input while a command is running."""
import weakref
import gi
gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk
from terminatorlib.plugin import Plugin
from terminatorlib.terminator import Terminator

AVAILABLE = ['CommandHeader']


class CommandHeader(Plugin):
    capabilities = []

    def __init__(self):
        self.panes = weakref.WeakKeyDictionary()
        self.timer = GLib.timeout_add_seconds(1, self.refresh)
        self.refresh()

    def attach(self, terminal):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        entry = Gtk.Entry()
        entry.set_has_frame(False)
        entry.set_hexpand(True)
        entry.set_placeholder_text('Waiting for fish…')
        entry.set_sensitive(False)
        native = Gtk.ToggleButton(label='Native')
        native.set_tooltip_text('Use fish completion, Atuin and native line editing below')
        row.pack_start(entry, True, True, 0)
        row.pack_end(native, False, False, 0)
        box.pack_start(row, False, False, 0)
        box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
        terminal.pack_start(box, False, False, 0)
        terminal.reorder_child(box, 0)
        box.show_all()
        state = dict(box=box, entry=entry, native=native, ready=False, history=[], index=0, draft='')
        self.panes[terminal] = state

        def focus_entry(*_):
            if state['ready'] and not native.get_active():
                entry.grab_focus()
            return False

        def changed(vte):
            title = vte.get_window_title() or ''
            if title.startswith('T2READY:'):
                was_ready = state['ready']
                state['ready'] = True
                vte.set_input_enabled(native.get_active())
                entry.set_sensitive(not native.get_active())
                entry.set_placeholder_text(title[8:] + '  $')
                if not was_ready and not native.get_active():
                    entry.set_text('')
                    if vte.has_focus():
                        GLib.idle_add(focus_entry)
            elif title.startswith('T2CMD:'):
                state['ready'] = False
                vte.set_input_enabled(True)
                entry.set_text(title[6:])
                entry.set_sensitive(False)

        def submit(_):
            command = entry.get_text()
            if not state['ready'] or native.get_active() or not command.strip():
                return
            state['ready'] = False
            state['history'].append(command)
            state['index'] = len(state['history'])
            entry.set_sensitive(False)
            terminal.vte.set_input_enabled(True)
            terminal.vte.grab_focus()
            # Clear any native draft before delivering this explicitly submitted command.
            terminal.vte.feed_child(('\x01\x0b' + command + '\r').encode())

        def entry_key(_, event):
            if event.keyval in (Gdk.KEY_Up, Gdk.KEY_Down):
                history = state['history']
                if state['index'] == len(history):
                    state['draft'] = entry.get_text()
                delta = -1 if event.keyval == Gdk.KEY_Up else 1
                state['index'] = max(0, min(len(history), state['index'] + delta))
                entry.set_text(history[state['index']] if state['index'] < len(history) else state['draft'])
                entry.set_position(-1)
                return True
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                if event.keyval in (Gdk.KEY_a, Gdk.KEY_e):
                    entry.set_position(0 if event.keyval == Gdk.KEY_a else -1)
                    return True
                if event.keyval == Gdk.KEY_u:
                    entry.delete_text(0, entry.get_position())
                    return True
            return False

        def vte_key(_, event):
            if state['ready'] and not native.get_active():
                # Keep copy shortcuts available in the output area.
                if event.state & Gdk.ModifierType.CONTROL_MASK and event.state & Gdk.ModifierType.SHIFT_MASK:
                    return False
                entry.grab_focus()
                entry.event(event)
                return True
            return False

        def toggle(_):
            terminal.vte.set_input_enabled(native.get_active() or not state['ready'])
            entry.set_sensitive(state['ready'] and not native.get_active())
            if native.get_active():
                terminal.vte.grab_focus()
            elif state['ready']:
                entry.grab_focus()

        entry.connect('activate', submit)
        entry.connect('key-press-event', entry_key)
        native.connect('toggled', toggle)
        state['handlers'] = [
            terminal.vte.connect('window-title-changed', changed),
            terminal.vte.connect('key-press-event', vte_key),
        ]
        changed(terminal.vte)

    def refresh(self):
        for terminal in Terminator().terminals:
            if terminal not in self.panes:
                self.attach(terminal)
            state = self.panes[terminal]
            state['entry'].override_font(terminal.vte.get_font())
            for key, setter in (('background_color', 'override_background_color'),
                                ('foreground_color', 'override_color')):
                color = Gdk.RGBA()
                if color.parse(terminal.config[key]):
                    for flag in (Gtk.StateFlags.NORMAL, Gtk.StateFlags.INSENSITIVE):
                        getattr(state['entry'], setter)(flag, color)
        return True

    def unload(self):
        GLib.source_remove(self.timer)
        for terminal, state in list(self.panes.items()):
            terminal.vte.set_input_enabled(True)
            for handler in state['handlers']:
                terminal.vte.disconnect(handler)
            terminal.remove(state['box'])
            state['box'].destroy()
        self.panes.clear()
