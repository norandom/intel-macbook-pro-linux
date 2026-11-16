# Benchmark: Linux vs macOS, not chip vs chip

`tools/benchmark.sh` runs unchanged on Ubuntu and macOS (bash 3.2, stock perl, openssl, dd,
gzip; nothing to install). It measures the machine as it is and never changes turbo,
governors, power profiles or fans. `tools/benchmark-compare.sh` puts two results side by side.

```sh
bash tools/benchmark.sh --runs 10 --json --out benchmarks   # -> benchmarks/linux.json or macos.json
bash tools/benchmark-compare.sh benchmarks/linux.json benchmarks/macos.json
bash tools/benchmark.sh --quick                              # short check run
```

Each JSON file holds the median, min, max and every run per test, the Mac model, the CPU, and
the power state (power source, turbo, governor/EPP and profile on Linux; Low Power Mode on
macOS). Higher is better everywhere.

## How the chip is kept out of the result

1. **Same Mac, both OSes.** The valid comparison is one machine booted into Linux and into
   macOS. `benchmark-compare.sh` checks the CPU model and thread count and refuses to compare
   different CPUs. `--force` shows only the normalized kernel numbers (point 3), with a warning;
   between different chips they are an estimate at best (cache sizes, microcode and the
   kernel's CPU-bug mitigations differ per model).
2. **User-space tests are the baseline, not the verdict.** sha256, the perl loop and gzip run
   almost entirely in user space. On the same chip they mainly show how each OS runs the CPU:
   frequency and turbo policy, power limits, and how many cores stay busy. They also include the
   tool builds (OpenSSL 3.x vs Apple's LibreSSL, different perl and gzip), so treat them as
   "the CPU as each OS delivers it".
3. **Kernel tests, also per CPU cycle.** The kernel tests measure what the OS itself does. Each
   is also reported divided by the single-core perl speed of the same run ("per CPU" in the
   log, `normalized` in the JSON, "B/A cpu" in the comparison). That cancels clock and turbo
   differences: if macOS boosts higher than Linux with turbo off, the raw kernel numbers favor
   macOS, but the normalized ones show whether the kernel code path itself is faster.

## The tests

| Key | Test | Kind | What it exercises |
|---|---|---|---|
| sha1 | sha256, single core (`openssl speed`) | user | integer ALU, clock policy, OpenSSL build |
| shaN | sha256, all threads (`openssl speed -multi`) | user | scheduler placement over 8 cores / 16 threads, sustained power limit |
| perl | perl integer loop | user | interpreter / branchy code, clock policy; also the normalization base |
| gzip | gzip -6, single core | user | compression, clock policy, gzip build |
| syscall | `dd bs=1`: 1-byte read + write | kernel | raw syscall entry/exit cost (incl. Spectre/Meltdown mitigations) |
| stat | `stat("/")` in a loop | kernel | syscall plus path lookup in the VFS |
| pipe | 1-byte ping-pong between two processes | kernel | pipe wakeups and context switches |
| fork | fork, child exits, parent waits | kernel | process creation, address-space copy |
| spawn | fork + exec `/usr/bin/true` | kernel | full program start: exec, dynamic loader, teardown |
| files | create + unlink 5000 empty files | kernel + filesystem | ext4 on LUKS/LVM vs APFS (encrypted); see below |
| fault | fill a fresh 2 GiB buffer | kernel | page faults on new memory, zeroing; partly user-space fill |
| zero | `dd /dev/zero → /dev/null`, 1 MiB blocks | kernel | the kernel's in-kernel zero-fill; not DRAM bandwidth |

Kernel tests are timed inside perl, so interpreter start-up isn't counted. `spawn` includes
the dynamic loader of each OS (glibc `ld.so` vs `dyld`), so it measures "start a program" as a
user sees it. `files` measures the filesystem stack as much as the kernel: ext4 on dm-crypt on
LVM here, APFS with FileVault on macOS. Both are the stock storage setups, so it's still an OS
comparison, just not a pure kernel one.

## What the comparison can and can't tell you

- It **can** tell you which OS gets more from this Mac: the raw numbers on the same machine
  under the same power conditions.
- It **can** tell you which kernel path is leaner per CPU cycle: the normalized kernel numbers.
- It **can't** separate the kernel from its standard library and loader (`spawn`), or from the
  filesystem (`files`); those are measured as each OS ships them.
- It doesn't measure disk throughput, GPU or network.

## Fair runs

1. Plugged in, not in the middle of a heavy charge, lid open, machine idle (close heavy apps;
   a running Claude session costs a few percent in every run).
2. Linux as is (turbo off). For the maximum, once more after `turbo-on` (`turbo-off` after).
3. macOS with Low Power Mode off. macOS has no built-in turbo switch: turbo off there needs
   Turbo Boost Switcher (a kext). The script detects that kext and records `turbo` as `off` or
   `on`; check that line before comparing raw numbers with Linux turbo off. The normalized
   kernel numbers are valid either way.
4. 10 runs each, compare medians; the first run warms caches and the median absorbs that.
5. On macOS, check the log: if LibreSSL doesn't support `-multi`, the all-threads sha256 value
   is a single-core value and shouldn't be compared.
