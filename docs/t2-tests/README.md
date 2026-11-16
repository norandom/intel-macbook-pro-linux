# Hardware tests (MacBookPro16,1)

Small scripts that answer one hardware question each on a T2 Mac. Each one restores what it
changes, writes a log next to itself, and asks for sudo once. The `.log` files here are the
results from the owner's machine (2026-11-16, Ubuntu 26.04, kernel 7.3.4-3-t2).

| Script | Question | Result here | Used for |
|---|---|---|---|
| [test1.sh](test1.sh) | Does the SMC accept a battery charge limit? | Yes: 60/80/100 accepted, 0 refused (100 = no limit) | `battery_charge_limit`, `t2-battery` ([power.md](../power.md)) |
| [test2.sh](test2.sh) | Can Linux set the fan speed? | No: `fan*_target` writes are refused (EOPNOTSUPP); the SMC keeps control | Fan curves stay in the backlog; Waybar only shows the speeds |
| [test3.sh](test3.sh) | Where does hibernation hang? | `freezer` and `devices` pass, `platform` (ACPI S4 firmware call) hangs; with disk mode `shutdown` all five stages pass | `HibernateMode=shutdown` via `hibernate = true` ([known-issues.md](../known-issues.md)) |

```sh
bash docs/t2-tests/test1.sh             # ~30 s
bash docs/t2-tests/test2.sh             # ~30 s, fans audible if writes work
bash docs/t2-tests/test3.sh             # hibernate stages, default disk mode
bash docs/t2-tests/test3.sh nowifi      # same with the Wi-Fi driver unloaded
bash docs/t2-tests/test3.sh shutdown    # same with disk mode "shutdown"
```

test3 uses the kernel's `pm_test`: each stage runs hibernation up to that point and comes back
after 5 seconds without powering off. Save your work anyway. If a stage hangs, power off with
the button, boot, and add the kernel log of the hung boot:

```sh
journalctl -b -1 -k | grep -E 'PM:|Freezing|suspend|t2bce|brcmf|amdgpu' | tail -40 >> docs/t2-tests/test3.log
```

Rerun them after a kernel update: a newer t2 kernel may allow fan control, or change how
hibernation behaves.
