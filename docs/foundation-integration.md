# Foundation integration checks

Run the native disposable integration suite from the locked environment:

```sh
uv run --locked python -m unittest tests.integration.test_foundation -v
```

The test controller runs as the real desktop user. Bubblewrap provides a
read-only Ubuntu filesystem, an isolated network namespace, and writable binds
for temporary home, apt/dpkg state, package payload, logs and receipts. The test
authentication broker launches only a mapped-root namespace with those same
binds; it never invokes host sudo. The real package guard, policy helper, apt,
dpkg and pyinfra operations run against a tiny local repository. Its explicitly
reviewed fixture package contains only an `/opt` text payload and no scripts.
Dummy Snap/Flatpak repository entries exist only to prove rejection; neither is
installed.

The suite checks combined and standalone Node previews, installation, an
unchanged second apply, scoped policy/Bash restoration, authentication/download
failures, installed prohibited runtimes, conflicting effective pins, and direct
and transitive prohibited selections. Authentication failure occurs after a
successful Bash operation, confirming partial success remains visible while the
command exits nonzero. It compares managed configuration, dpkg state and payload
bytes/modes. Native apt inspection caches and planner logs are excluded because
apt may create them during read-only planning; indexes and installed-package
state remain part of the comparison.

Protected boot, storage, login, GPU and hardware support paths remain on the
read-only host mount. The successful workflow checks that enforcement, compares
readable core file digests and artifact metadata before/after, and preserves the
original snapd pin. Unreadable paths are recorded as verification gaps, not read
using host privileges. Existing independent tests cover locked uv bootstrap,
Node configuration conflicts, service-policy interruption recovery and changed
file restoration conflicts.

The integration Node executables and nvm commands are fixtures for an already
installed toolchain; this suite does not download Node or test arbitrary nvm
installer behavior. Actual microphone, camera, touch bar, speaker, Bluetooth and
suspend/resume checks remain live manual acceptance. Passing this suite does not
claim those hardware checks or completion of the broader desktop port.

Bubblewrap and dpkg-deb must already exist. If user namespaces are unavailable,
the tests skip with an explicit message; that is not passing integration evidence.
