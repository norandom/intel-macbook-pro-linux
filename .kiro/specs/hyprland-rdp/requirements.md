# Requirements Document

## Introduction
The owner needs the source remote desktop capability on the separate native Ubuntu T2 Hyprland session. This port uses the maintainer release package and preserves local laptop use. Source audit revision is a1c09ec3f02a98b7c6a4641f907108a2ad080993; backlog coverage is P21–P23.

## Boundary Context
In scope: upstream release verification, authenticated remote access, supported session hooks, remote input/display/audio/clipboard handling and the final assembled validation checklist. The desktop remains Ubuntu Hyprland0.53.3; support is unverified because upstream documents0.54+. Out of scope: compositor/RDP builds or fork patches, VM console policy, global authentication policy, other feature implementations and GPU-policy reconstruction. Desktop supplies a selected live session; themes and containers supply their own acceptance evidence.

## Requirements

### Requirement 1: Verified upstream package
**Objective:** As the owner, I want a verified maintainer package, so that installation has reviewable provenance and compatibility.

#### Acceptance Criteria
1. When provisioning is requested, the RDP port shall select the pinned maintainer release archive and verify its provenance, checksum, archive safety and target runtime dependencies before installing it.
2. If the archive, runtime dependencies or selected compositor capabilities cannot be validated, the RDP port shall report the precise pending or incompatible capability and keep normal listener activation unavailable.
3. The RDP port shall retain the selected native compositor and shall not substitute a fork package, build RDP locally or upgrade/build the compositor to bypass compatibility failure.

### Requirement 2: Explicit authenticated access
**Objective:** As the owner, I want remote access only under a valid configuration, so that provisioning does not expose an unauthenticated desktop.

#### Acceptance Criteria
1. While authenticated credentials, explicit network exposure and TLS identity configuration are absent or invalid, the RDP port shall keep its listener disabled and report the missing configuration without printing secrets.
2. When access is enabled for a validated selected session, the RDP port shall reject missing or incorrect credentials and permit only the intended desktop user context.
3. When provisioning, diagnosing or restoring RDP, the RDP port shall preserve login-manager behavior and system authentication policy and shall not apply source away-mode sudo or ptrace changes.

### Requirement 3: Selected-session lifecycle
**Objective:** As the owner, I want RDP attached only to my chosen Hyprland session, so that KDE and unrelated sessions remain unaffected.

#### Acceptance Criteria
1. When starting RDP, the RDP port shall require an unambiguous live ready Hyprland session belonging to the invoking user and shall reject stale, wrong-user or ambiguous selection.
2. When an authenticated remote session connects or disconnects, the RDP port shall use supported upstream session hooks with repeatable cleanup rather than infer events from journal text.
3. When the selected compositor stops or the RDP service fails, the RDP port shall stop its session activity and reconcile its owned remote state without modifying another session.
4. While KDE or an unrelated graphical session runs, the RDP port shall remain inactive unless the owner explicitly starts it for a validated separate Hyprland session.

### Requirement 4: Preserve local laptop behavior
**Objective:** As the owner, I want remote access without sacrificing local T2 use, so that connecting and disconnecting are recoverable.

#### Acceptance Criteria
1. When a remote client attaches, resizes, disconnects or reconnects, the RDP port shall preserve physical outputs, local input devices and the existing lock state without blanking the console, disabling input or unlocking the desktop.
2. While remote audio is enabled, the RDP port shall mirror local audio or leave remote audio off and shall preserve the local T2 speaker, microphone, Bluetooth and routing policy after disconnect or failure.
3. When remote keyboard input is used, the RDP port shall preserve the source German Mac compositor keymap, Option+L=@, de/us switching and source Super shortcuts without modifying console or encrypted-boot keyboard configuration.
4. Where remote clipboard and file transfer are enabled, the RDP port shall validate supported text/image and file directions and report unavailable optional capabilities without altering kernel modules or deleting transferred source files.
5. When remote capture or encoding is selected, the RDP port shall validate the selected mode on native GPU output without forcing compositor software rendering or importing VM GPU workarounds.

### Requirement 5: Protected provisioning and recovery
**Objective:** As the owner, I want a bounded repeatable port, so that the working T2 system survives installation and restoration.

#### Acceptance Criteria
1. When dependencies or feature files are applied or restored, the RDP port shall reject forbidden packaging routes and any transaction or hook affecting protected storage, kernel, boot, initramfs or T2 support state, including autoremove.
2. When existing user files conflict with proposed managed files, the RDP port shall report the conflict or preserve a reviewed backup before adoption and restore only its own unchanged managed state.
3. When configuration changes affect an active client, the RDP port shall report that reconnect is required and defer disruptive restart until explicitly requested.

### Requirement 6: Honest assembled acceptance
**Objective:** As the owner, I want evidence for the assembled port, so that document or inventory checks are not mistaken for a working laptop.

#### Acceptance Criteria
1. When assembled validation is requested, the RDP port shall produce a P23 checklist consuming feature-owned checks for desktop/decorations, themes, applications, fonts, shell/resource controls, containers and RDP without implementing those features itself.
2. If GPU-unit evidence, a live T2 session, a remote client or other prerequisite is unavailable, the RDP port shall mark affected GPU transition, RDP attach/detach and hardware checks pending with their exact missing evidence.
3. When reporting completion, the RDP port shall distinguish static checks, artifact verification, native session tests and live hardware/client acceptance and shall report remaining compatibility blockers without claiming runtime success.
