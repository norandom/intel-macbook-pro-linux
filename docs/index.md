# Docs

A map of everything under `docs/`. Start with the README, then pick the area you care about.

## Use it

| Doc | What's in it |
|---|---|
| [coming-from-macos.md](coming-from-macos.md) | The macOS app or habit you had, and what replaces it here |
| [desktop.md](desktop.md) | Hyprland session, Waybar, keys, display, idle and lock, living next to KDE |
| [power.md](power.md) | Turbo, power profiles, battery charge limit, GPU modes, power tuning |
| [audio.md](audio.md) | EasyEffects headphone presets, music headphones, speaker DSP |
| [developer-tools.md](developer-tools.md) | Shell, compilers, Node, Python, containers, VMs, Nix |
| [apps.md](apps.md) | Office and creative apps, browsers, vendor apps, default apps |
| [remote-access.md](remote-access.md) | Tailscale, SSH with fail2ban, RDP into the Hyprland session |
| [security-keys.md](security-keys.md) | YubiKey (primary + spare) instead of Touch ID for sudo, login and the lock screen |
| [commands.md](commands.md) | Every helper command in one list |
| [known-issues.md](known-issues.md) | Defects we know about, with causes and sources (hibernate on T2) |

## Customize when forking

| Doc | What's in it |
|---|---|
| [configuration.md](configuration.md) | Every `config.toml` key with its default and effect; re-running one task |
| [forking.md](forking.md) | Which file to edit for keyboard layout, keys, apps, bar, themes, tasks |
| [safety.md](safety.md) | What the deploy never touches, the package guard, the one boot exception |
| [nix.md](nix.md) | Nix for the CLI tools: update, add, roll back |

## Performance

| Doc | What's in it |
|---|---|
| [benchmark.md](benchmark.md) | Linux vs macOS on the same Mac: how well each OS is optimized for this hardware |
| [cpu-mitigations.md](cpu-mitigations.md) | CPU security mitigations off (config `cpu_mitigations_off`), and what it costs |

## Owner runbooks

Manual steps that touch protected areas, so the deploy doesn't do them for you.

| Doc | What's in it |
|---|---|
| [hibernate-swap.md](hibernate-swap.md) | Growing the swap LV so suspend to disk can work |
| [verbose-boot.md](verbose-boot.md) | Showing boot and shutdown messages instead of the splash |

## Project internals

| Doc | What's in it |
|---|---|
| [source-port-plan.md](source-port-plan.md) | How the source repository was ported, file by file |
| [backlog.md](backlog.md) | Deferred features and why |
| `.kiro/steering/`, `.kiro/specs/` | Project rules and the per-feature specs |
