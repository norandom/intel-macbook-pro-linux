# Package installation policy

Strict user rule: no Snap/snapd and no Flatpak. This applies to all specs,
provisioning, application ports, dependencies, and fallback installation paths.
Do not install their runtimes, enable their services, add their stores/remotes,
or install applications through either packaging system. Do not bypass the
rule by choosing an apt package that installs an application through Snap.

Preserve the existing snapd apt block. Read-only inspection found
`/etc/apt/preferences.d/nosnap.pref` containing:

```text
Package: snapd
Pin: release a=*
Pin-Priority: -10
```

The foundation spec should capture reproducible enforcement for both snapd
and Flatpak, including dependency resolution checks. The observed pin above
is evidence of existing snapd policy; a Flatpak apt block has not yet been
verified. Never weaken the existing block during provisioning.

Enforcement is automatic in `manage/packages.py`: requested and transitive
packages are name-filtered, removals are blocked, and before apt runs as root
every planned archive's payload paths and maintainer scripts are scanned for the
protected boundary. No per-package human review manifest is required.

Use native distro packages where appropriate, or reviewed upstream release
artifacts/source builds. Python environments use uv and Node/npm use nvm.
If an application has no permitted installation path, report that constraint
and leave its installation unresolved.
