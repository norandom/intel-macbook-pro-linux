# How well each OS is optimized for this Mac

Same 2019 MacBook Pro, booted once into Linux and once into macOS, same settings. The CPU
does its own work equally fast under both. Anything that goes through the operating system
(system calls, starting programs, files) runs 2 to 4 times faster on Linux, and creating
files about 23 times faster.

This isn't a "which OS is better" test. It measures how much effort each OS still puts into
running this particular hardware well, in the setting it's used in every day: quiet and cool,
turbo off, fans at their minimum.

## Why this matters for a 2019 machine

The i9-9980HK in this Mac has 8 cores and 16 threads, and the machine has 64 GB of RAM and a
2 TB SSD. That's still a capable workstation for professional work by today's standards. But
Apple has moved on: its engineering goes into Apple Silicon, and Apple said at WWDC 2025 that
macOS Tahoe (26) is the last release for Intel Macs. The owner's experience is that each recent
macOS release ran this machine a little worse.

The numbers below can't prove a trend (they're one macOS release). What they do show is that
the hardware isn't the bottleneck. The same chip delivers the same raw speed under both
systems, and the gap opens wherever the OS itself does the work.

![Linux vs macOS on the same Mac, per test](img/bench-os.svg)

\* perl: the two systems ship different perl builds (5.40 vs 5.44), so this row measures the
build as much as the OS.
\*\* Files: includes the storage stack, ext4 on LUKS/LVM on Linux vs APFS with FileVault on
macOS. Both are the stock encrypted setups.

## The machine

| | |
|---|---|
| Model | MacBook Pro 16" 2019, MacBookPro16,1, T2 chip |
| CPU | Intel Core i9-9980HK, 8 cores / 16 threads, 2.4 GHz base, 5.0 GHz turbo, 16 MiB L3 |
| Memory | 64 GB DDR4-2667 |
| Storage | 2 TB Apple SSD (AP2048N), encrypted on both systems |
| GPU | Intel UHD 630 + AMD Radeon Pro 5300M/5500M (Navi 14; not tested here) |
| Linux | Ubuntu 26.04.1, kernel 7.3.4-3-t2, balanced profile, OpenSSL 3.5.5, perl 5.40.1 |
| macOS | macOS 26.7.3 Tahoe (Darwin 25.6.0), Low Power Mode off, OpenSSL 3.5.9, perl 5.44.0 |
| Both | on AC, turbo off (Linux: intel_pstate; macOS: Turbo Boost Switcher), idle, 10 runs each |

Turbo was off on both, so both ran at the same 2.4 GHz clock. That's what makes the raw
numbers comparable.

Turbo off isn't a handicap set up for the test. It's how this machine is meant to be used: a
quiet, cool, low-power tool for focused work, fans at their minimum, nothing to listen to while
you think. The benchmark measures that everyday situation, not the machine flat out. With turbo
on the i9 is faster in short bursts, but it gets hot and loud quickly, and you'd lose exactly
the calm this setup is for.

## The numbers

Medians of 10 runs, higher is better. "Linux / macOS" compares the two systems with their
standard CPU security mitigations on.

| Test | Linux | macOS | Linux / macOS | Linux, mitigations off |
|---|---|---|---|---|
| sha256, one core (MB/s) | 308 | 302 | 1.02 | 308 |
| sha256, 16 threads (MB/s) | 2,616 | 2,526 | 1.04 | 2,605 |
| gzip -6 (MB/s) | 20.1 | 18.4 | 1.10 | 20.1 |
| perl integer loop (M iter/s) | 9.91 | 7.78 | 1.27 | 9.89 |
| tiny system calls (k/s) | 3,141 | 741 | 4.24 | 4,002 |
| stat() file lookup (k/s) | 872 | 239 | 3.66 | 949 |
| start a program (per s) | 651 | 209 | 3.12 | 679 |
| fork a process (per s) | 1,685 | 850 | 1.98 | 1,704 |
| pipe ping-pong (k round trips/s) | 137 | 81 | 1.69 | 146 |
| fresh memory (GiB/s) | 1.8 | 1.4 | 1.29 | 1.8 |
| kernel zero-fill, dd (GiB/s) | 12.85 | 18.09 | 0.71 | 12.91 |
| create + delete files (k/s) | 89.5 | 3.9 | 22.95 | 99.1 |

Raw data: `benchmarks/linux.json`, `benchmarks/macos.json`,
`benchmarks/mitigations-off/linux.json`, each with all 10 values per test and the full log.

What stands out:

- The chip is the same. sha256 is within 2-4 % on both systems. Clock and cores deliver
  the same speed, so the differences further down come from the OS.
- Kernel paths are where macOS loses. A system call takes about 0.3 µs on Linux and about
  1.3 µs on macOS. Starting a program takes 1.5 ms on Linux and 4.8 ms on macOS. You feel this
  in terminals, builds, git and scripts, which do these things thousands of times.
- Files are the biggest gap. 23× is mostly APFS and its security checks against ext4, not
  the kernel alone. Anything that touches many small files (`node_modules`, git checkouts,
  compilers) feels it.
- macOS wins one test: zeroing large memory blocks in the kernel is 1.4× faster there.
- fork is noisy on Linux (48 % spread across runs; see the end of this page). Only the 2×
  gap is solid; the exact number isn't.

## Turning the CPU mitigations off

The kernel's protections against Spectre/Meltdown-type CPU flaws cost time on every kernel
entry and exit. This Mac now runs Linux with `mitigations=off` (config flag
`cpu_mitigations_off`, see `docs/cpu-mitigations.md`). Before and after, same machine and
settings:

![Mitigations off vs on, change per test](img/bench-mitigations.svg)

- System calls got 27 % faster, files 11 %, stat() 9 %, pipes 7 %. That's the work
  builds, shells and containers do all the time.
- CPU work didn't change at all, as expected: the mitigations only cost time at the
  kernel boundary.
- Program start and fork moved less than their run-to-run noise. Their cost is dominated
  by other things (see below).
- With mitigations off, Linux's lead over macOS on system calls grows from 4.2× to 5.4×.

### Decision: keep them off

For this machine, as used (one person, own code, no untrusted guests), the 7-27 % on kernel
paths is worth it. What's exposed is code running on this machine reading memory it shouldn't:
JavaScript in browsers (which keep their own protections), packages you install, and VM guests.
Nothing becomes reachable from the network.

We're wrong if one of these becomes true: the machine runs VMs with guests you don't control,
runs code you can't vet (other people's CI jobs, unknown binaries), or gets a second user.
Then set `cpu_mitigations_off = false`, run `tasks/cpu_mitigations.py` and reboot. For
adopters the default is off, meaning the mitigations stay on.

## Running it yourself

```sh
bash tools/benchmark.sh --runs 10 --json --out benchmarks            # -> linux.json or macos.json
bash tools/benchmark-compare.sh benchmarks/linux.json benchmarks/macos.json
python3 tools/benchmark-charts.py                                    # redraw docs/img/bench-*.svg
```

The script runs unchanged on Linux and macOS (bash 3.2, stock perl, openssl, dd, gzip; nothing
to install). It never changes turbo, governors, power profiles or fans, and it records them,
so you can check two runs were made under the same conditions. Each JSON file holds the
median, min, max and every run per test, plus the Mac model, CPU and power state.

For a fair comparison:

1. Use the same Mac for both systems. `benchmark-compare.sh` refuses to compare different
   CPUs; between different chips you'd measure the chip, not the OS.
2. Plug in, close heavy apps, leave the machine idle.
3. Match turbo. Linux here runs with turbo off by default. macOS has no built-in switch, so
   turbo off there needs Turbo Boost Switcher; the script detects its kernel extension and
   records `turbo=off`. Check that line in the log.
4. macOS: Low Power Mode off.
5. 10 runs each; compare medians.

Re-running on each macOS update is the only way to see whether the gap actually grows from
release to release.

## What each test measures

| Test | Kind | What it exercises |
|---|---|---|
| sha256, one core (`openssl speed`) | CPU | integer units and clock; no AES-NI or SHA extensions involved |
| sha256, all threads (`-multi`) | CPU | the scheduler spreading 16 threads over 8 cores, sustained power limit |
| gzip -6 | CPU | compression; also the gzip build |
| perl integer loop | CPU | branchy interpreter code; also the per-cycle baseline below |
| tiny system calls (`dd bs=1`) | kernel | raw kernel entry and exit, including mitigations |
| stat() | kernel | a system call plus a path lookup |
| pipe ping-pong | kernel | waking another process, context switches |
| fork | kernel | creating a process |
| start a program (fork + exec `/usr/bin/true`) | kernel | exec, the dynamic loader (glibc vs dyld), teardown |
| fresh memory | kernel | page faults on new memory, partly the fill itself |
| kernel zero-fill (`dd /dev/zero`, 1 MiB) | kernel | the kernel filling memory; not DRAM bandwidth |
| create + delete files | kernel + filesystem | the whole storage stack as each OS ships it |

Kernel tests are timed inside perl, so interpreter start-up isn't counted. The compare script
also shows each kernel result divided by the single-core perl speed ("per CPU"). That cancels
clock differences, which matters when turbo differs between two runs.

The tests can't separate the kernel from its loader (program start) or from the filesystem
(files); those are measured as each OS ships them. Disk throughput, GPU and network aren't
measured.

## Why fork is slow on Linux here

About 1,700 forks per second (0.6 ms each) with a 48 % spread is slow for Linux. Measured
apart, with mitigations on:

| Measurement | forks/s | `fork()` call | wait for the child |
|---|---|---|---|
| perl (the benchmark) | 1,800 | 190 µs | 350 µs |
| perl, parent and child on one core (`taskset`) | 2,860 | 130 µs | 213 µs |
| minimal C program | 3,100-5,600 | 60-110 µs | 115-215 µs |
| minimal C, one core | 7,590 | 52 µs | 80 µs |

1. The child wakes a sleeping core. That's the biggest share, and the cause of the spread.
   Linux starts the child on another idle core, and idle cores on this i9 sit in deep sleep
   states that take long to leave (C8: 200 µs, C10: 890 µs). Keeping both on one core makes the
   minimal case 2.5× faster and nearly removes the variation.
2. Turbo is off, so the CPU runs at 2.4 GHz instead of up to 5 GHz.
3. perl is a heavier process than minimal C, roughly double the cost. Memory size barely
   matters: 0, 64 and 512 MiB touched cost the same.

That's also why turning the mitigations off barely moved fork: the time goes into waking
cores, not into the kernel boundary. Turbo on or the performance profile would help more.
