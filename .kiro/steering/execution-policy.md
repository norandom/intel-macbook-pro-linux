# Execution priorities

The owner explicitly prioritizes speed and practical delivery. This is not a
research project. Reuse the existing source implementation and backport only
what compatibility requires. Work directly on small scoped changes, use targeted
checks, and avoid repeated planning, broad research, speculative abstractions
or process layers. Investigate concrete blockers only. Preserve all explicit
protected-system, hardware, packaging and backlog constraints.

Deployment is owner-run. Prepare code, tests and previews, then explicitly tell
the owner when the reviewed changes are ready to deploy. Do not open terminals,
attempt sudo authentication or apply live changes on the owner's behalf.
Document direct `.venv/bin/pyinfra` commands (or `pyinfra` in the activated venv).
Use uv for environment setup and dependency locking.
