# Task Plan Review

Result: PASS. Mode: independent task-graph sanity review.

Draft reviewed directly against requirements.md/design.md and task-generation
rules by fresh agent `/root/port_desktop/desktop_task_sanity`. First verdict:
NEEDS_FIXES. Bounded repair separated IPC/effect controls, monitor/night/lock,
launcher/bar/menu/visual seeds; clarified persistent US/DE selection across new
sessions and explicit launch dependencies. Second verdict: PASS, with no further
prerequisite/ordering/boundary findings. No third planning cycle was run.

Controller checks: every one of44criteria is mapped, seven major groups and
27executable subtasks have deliverables/observable done bullets. Parallel marker
is limited to5.6, whose desktop-utility paths are distinct from UI work and whose
prerequisites are explicit. No source build/rootless builder/newer library
prerequisite remains. Task numbers progress setup→original decorations→input→
window behavior→UI/utilities→session integration→native validation.

Themes producer contract was synchronized without changing task graph: exact
CLI/state/cycle/error semantics and scoped tab-CSS ownership. Task5.4 owns GTK
settings seeds, not the theme-owned tab stylesheet/import. The read-only session
status contract identifies native0.53; upstream RDP release compatibility remains
outside desktop ownership. Runtime acceptance, protected-hook inspection and
T2 checks are required future work, not evidence obtained by this spec review.
