# German Mac graphical keyboard policy

Owner requires German Mac keyboard behavior, including Option+L producing @.
The source Hyprland repository already defines the desired Super-key mapping;
preserve it rather than invent a new Command/Option/Super remap.

Pinned source group_data/all.py declares:

```text
keyboard_layout = de,us
keyboard_variant = mac_nodeadkeys,
keyboard_options = compose:caps,shift:both_capslock_cancel,altwin:swap_ralt_rwin,lv3:lalt_switch
```

Treat that complete source configuration and bindings as the port baseline.
Do not replace it with generic German PC layout or blindly apply both-Alt
level3 options that would override the source's Super arrangement.

Read-only installed XKB inspection confirms de(mac) maps key AC09 (L) level3
to at, and de(mac_nodeadkeys) includes that mapping. level3(lalt_switch) maps
left Alt/Option to ISO_Level3_Shift. This supports the proposed mapping but does
not prove the current KDE or future Hyprland session is using it.

Acceptance checks include Option+L=@ and source Super shortcuts alongside de/us
switching, brackets/braces/bar/backslash/Euro/tilde combinations from source.
Test actual physical key events in the intended session. A keymap compiling
successfully is not a substitute for interactive validation.

Scope is graphical-session input only. No changes to /etc/default/keyboard,
console keymaps, login keyboard policy, initramfs/mkinitcpio, cryptsetup/LUKS
unlock input or the owner's keyboard-presence boot customizations. Current KDE
layout repair, if separately requested, must be user-session scoped too.
