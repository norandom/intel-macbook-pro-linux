"""Heavy jobs leave the desktop a free core (owner request 2026-11-25).

A Dagger fuzz run (Go tests on all 16 threads) made typing lag in Deckle: the desktop still had
its fair share, but every key press waited for a busy core. So:
- Terminal shells (and everything they start: go test, cargo/nextest, pytest-xdist, make, cmake,
  the Claude/Codex agents) run with a CPU affinity that leaves the first core(s), both SMT
  threads, to the desktop. Tools that size themselves from the CPUs they may use (nproc, Go,
  Rust's available_parallelism) follow it; the job variables below pin the rest.
- Docker containers run in containers.slice: the same CPUs and a low CPU weight.
Config: reserved_cores (default 1, 0 = off), build_jobs (default 0 = all allowed threads).
`allcores <command>` runs one command on every CPU without the job limits.
"""
from pathlib import Path

CPU_SYS = Path("/sys/devices/system/cpu")
SLICE = "containers.slice"   # top level: a dash would nest it (t2-x.slice sits in t2.slice)
SLICE_WEIGHT = 20   # systemd default 100: containers give way to the desktop under contention
# Variables that size parallel builds/tests (each tool's own name).
JOB_VARS = ("GOMAXPROCS",                       # Go; also `go test -p` (packages in parallel)
            "CARGO_BUILD_JOBS", "RUST_TEST_THREADS", "NEXTEST_TEST_THREADS",
            "PYTEST_XDIST_AUTO_NUM_WORKERS",    # pytest -n auto
            "CMAKE_BUILD_PARALLEL_LEVEL", "CTEST_PARALLEL_LEVEL")
MARKER = "# {mark} t2-mac-kde: free desktop core, build/test job limits"


def parse_list(text: str) -> list[int]:
    """'0-3,8,10-11' -> [0, 1, 2, 3, 8, 10, 11]"""
    cpus = []
    for part in text.strip().split(","):
        if part:
            a, _, b = part.partition("-")
            cpus += range(int(a), int(b or a) + 1)
    return cpus


def fmt_list(cpus) -> str:
    """[0, 1, 2, 3, 8] -> '0-3,8'"""
    out, run = [], []
    for c in sorted(set(cpus)):
        if run and c == run[-1] + 1:
            run.append(c)
            continue
        if run:
            out.append(f"{run[0]}-{run[-1]}" if len(run) > 1 else str(run[0]))
        run = [c]
    if run:
        out.append(f"{run[0]}-{run[-1]}" if len(run) > 1 else str(run[0]))
    return ",".join(out)


def topology(root: Path = CPU_SYS) -> tuple[list[int], list[list[int]]]:
    """(online CPUs, sibling groups ordered by their lowest CPU)."""
    online = parse_list((root / "online").read_text())
    groups = []
    for c in online:
        sib = parse_list((root / f"cpu{c}/topology/thread_siblings_list").read_text())
        if sib not in groups:
            groups.append(sib)
    return online, sorted(groups, key=min)


def allowed(online: list[int], groups: list[list[int]], reserved_cores: int) -> list[int]:
    """CPUs for heavy jobs: all but the first reserved_cores cores (with their SMT siblings).
    At least one core always stays allowed."""
    keep = max(0, min(int(reserved_cores), len(groups) - 1))
    taken = {c for g in groups[:keep] for c in g}
    return [c for c in online if c not in taken]


def jobs(cpus: list[int], build_jobs: int) -> int:
    return int(build_jobs) if int(build_jobs) > 0 else len(cpus)


def bash_block(cpus: list[int], all_cpus: list[int], n: int) -> str:
    """Interactive bash: affinity for this shell (inherited by its children) + job variables."""
    lst, full = fmt_list(cpus), fmt_list(all_cpus)
    unset = " ".join(f"-u {v}" for v in JOB_VARS)
    lines = ['if [[ $- == *i* ]]; then']
    if lst != full:
        lines.append(f'  command -v taskset >/dev/null && taskset -cp {lst} $$ >/dev/null 2>&1')
    lines += [f'  export {v}="${{{v}:-{n}}}"' for v in JOB_VARS]
    lines += [f'  allcores() {{ taskset -c {full} env {unset} "$@"; }}', 'fi']
    return "\n".join(lines)


def fish_conf(cpus: list[int], all_cpus: list[int], n: int) -> str:
    lst, full = fmt_list(cpus), fmt_list(all_cpus)
    unset = " ".join(f"-u {v}" for v in JOB_VARS)
    lines = ["# Managed by t2-mac-kde (manage/build_limits.py): heavy jobs leave the desktop a free core.",
             "# Config: reserved_cores, build_jobs. `allcores <command>` runs one command on every CPU.",
             "status is-interactive; or exit"]
    if lst != full:
        lines.append(f"command -q taskset; and taskset -cp {lst} $fish_pid >/dev/null 2>&1")
    lines += [f"set -q {v}; or set -gx {v} {n}" for v in JOB_VARS]
    lines += ["function allcores --description 'run one command on every CPU, without the job limits'",
              f"    taskset -c {full} env {unset} $argv", "end"]
    return "\n".join(lines) + "\n"


def slice_unit(cpus: list[int]) -> str:
    return ("# Managed by t2-mac-kde (manage/build_limits.py): Docker containers (daemon.json cgroup-parent)\n"
            "# leave the desktop its free core and give way to it under contention.\n"
            "[Unit]\nDescription=t2-mac-kde: containers, desktop core kept free\n\n"
            f"[Slice]\nCPUWeight={SLICE_WEIGHT}\nAllowedCPUs={fmt_list(cpus)}\n")
