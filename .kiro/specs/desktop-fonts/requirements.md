# Requirements Document

## Introduction
The laptop owner currently has a working Ubuntu KDE T2 Mac and an existing uv/pyinfra baseline, but lacks the source project's public font integration. Port backlog P08 from source revision `a1c09ec3f02a98b7c6a4641f907108a2ad080993` so terminals, desktop widgets and Xwayland applications can use the intended families and glyphs.

## Boundary Context
- In scope: public JetBrainsMono/FiraCode Nerd Fonts, Fixedsys Core/Excelsior, emoji/symbol fallback, fontconfig integration, core-font directory and its session helper.
- Out of scope: compositor startup configuration, terminal/widget configuration, themes, private licensed font acquisition, source encrypted assets, KDE/login/GPU/boot changes, Snap/snapd and Flatpak.
- Adjacent expectations: foundation supplies locked local execution and package-policy enforcement; desktop invokes the font helper and configures widgets; applications/shell/themes select installed family names. Existing user font preferences remain authoritative.

## Requirements

### Requirement 1: Public font availability
**Objective:** As the laptop owner, I want the source's public fonts available so applications render text and icons consistently.

#### Acceptance Criteria
1. When public fonts are provisioned, the Font Port shall make the source-pinned JetBrainsMono and FiraCode Nerd Font styles available to the desktop user.
2. When public fonts are provisioned, the Font Port shall make public Fixedsys Core and Fixedsys Excelsior available without deleting existing fonts.
3. When an application requests emoji or remaining Unicode symbols, the Font Port shall provide the source's Noto Color Emoji and Symbola fallback families.
4. If a font artifact fails integrity validation or is unavailable, the Font Port shall report failure and preserve the previously working installed family.

### Requirement 2: Preserve user rendering preferences
**Objective:** As the laptop owner, I want additive rendering integration so existing KDE and application font preferences remain usable.

#### Acceptance Criteria
1. When font settings are provisioned, the Font Port shall preserve existing user font configuration and unrelated system font settings.
2. When no conflicting user preference exists, the Font Port shall offer the source monospace preference for JetBrainsMono Nerd Font, slight hinting, antialiasing and emoji/symbol fallback.
3. Where the owner selects RGB or grayscale rendering, the Font Port shall apply that selected mode and retain color emoji support.
4. If existing settings prevent the requested effective rendering or family preference, the Font Port shall report the conflict without replacing the user's settings or claiming that preference was applied.

### Requirement 3: Xwayland core-font access
**Objective:** As a user of X11 applications, I want Fixedsys accessible through core-font lookup so legacy applications can render the source font.

#### Acceptance Criteria
1. When public Fixedsys fonts are provisioned, the Font Port shall expose both through a dedicated indexed X11 core-font directory.
2. When the desktop session invokes the font helper with an accessible Xwayland display, the Font Port shall add its core-font directory once and refresh that display's font index without replacing other font paths.
3. If the session display is unavailable, the Font Port shall terminate the helper after a bounded wait and report failure.
4. If the optional core-font directory is absent, the Font Port shall return an explicit skipped result without changing the session font path.

### Requirement 4: Reproducible and reversible operation
**Objective:** As the operator, I want predictable provisioning and restoration so the working laptop remains recoverable.

#### Acceptance Criteria
1. When preview is requested, the Font Port shall report intended changes and prerequisites without changing installed packages, fonts, caches or configuration.
2. When provisioning is repeated with unchanged desired state, the Font Port shall leave managed files unchanged and avoid unnecessary cache regeneration.
3. When restoring a prior managed font state, the Font Port shall restore only its owned changes and preserve unrelated fonts and preferences.
4. The Font Port shall use foundation-approved native package or reviewed pinned artifact routes and preserve the prohibition on Snap/snapd and Flatpak.
5. When private fonts are not supplied by the owner, the Font Port shall record them as optional and unavailable without fetching or decrypting source private data.
6. When validation runs, the Font Port shall distinguish successful file/family checks, pending session checks and failed checks without claiming runtime acceptance from document review.
