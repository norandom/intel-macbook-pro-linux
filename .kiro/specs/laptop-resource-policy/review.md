# Specification review evidence

## Scope and mode
Specification documents only; no resource implementation, privileged application, reboot or pressure test occurred. Requirements and design advance using the batch-authorized `-y` path. Task auto-approval follows a passing review, not a skipped gate. Parent performs a separate cross-spec review.

## Requirements gate — PASS, inline
Read EARS and requirements-review rules and template. Checked7 numeric requirement groups/26 acceptance criteria against P01–P06 and the owner intake. Every criterion has an EARS subject/response; technology names here name explicitly requested observable capabilities rather than invented implementation requirements. Adjacent shell loading, disk swap/resume, excluded VM/GPU behavior and permitted package policy are explicit. Latest desktop-audio clarification was folded into6.2 and boundary context. No scope ambiguity remains for the feature's requested behavior.

## Design gate — PASS, inline
Full discovery consulted pinned actual modules and missing system assets, official manuals, local packages/sysctls/handler and installed Avahi routing. All26 IDs appear in traceability. Boundaries, allowed dependencies, file plan, typed state/error contracts and validation are populated. Source tuning has explicit adopt/reject decisions. Source browser preferences and uncapped half-RAM zram are rejected with rationale. No source VM service or boot profile is inherited.

Local repair: replaced speculative executable D-Bus fallback support with the observed `SystemdService` alias and `Exec=/bin/false`; an unexpected future executable route blocks this component rather than inventing an override. Rechecked ownership and review gates. No need to resolve missing adjacent GPU unit to generate this independent design.

## Task plan gate — PASS, inline
Checked full coverage,1–3 hour executable units, observable completion bullets, explicit setup, file ownership, integration and validation. Plan has3 major groups,11 executable subtasks and6 parallel core implementation/fixture tasks. Privileged host application remains serialized; parallel markers do not authorize concurrent apt/service changes.

Local repair: package-startup guarding was initially implicit in later integration; added explicit1.3 setup before swap/earlyoom component implementation and updated all core dependencies. This is prerequisite implementation, not an extra deployment task.

## Task-graph sanity — PASS, inline fallback
At sanity-review time all4 slots were occupied by parent, this worker, container worker and its independent reviewer (observed with collaboration.list_agents). Per task skill fallback and parent instruction, reviewed in the current context without busy waiting. This is **inline**, not independent review.

Reviewed requirements.md/design.md and task-generation/parallel rules directly alongside the in-memory draft. Found the guarded-package prerequisite omission described above; repaired once, then repeated sanity checks. Latest verdict PASS: setup precedes all core tasks; core files/tests do not overlap; no hidden loader/root-deploy implementation is bundled; integration owns assembled modes; final validation distinguishes planned/effective/pending. The Avahi unexpected-route blocker and package/OOM/swap conflict guards are explicit designed runtime conditions, not unresolved document decisions.

## Fresh mechanical evidence
Python regex assertions on current documents reported:
- Acceptance criteria:26; missing task mappings:[]; invalid task mappings:[];
- Subtasks:11; parallel markers:6;
- Every executable task has `Done:`, `_Boundary:_` and numeric `_Requirements:_`;
- All explicit dependency IDs exist; no unresolved template placeholders;
- All26 acceptance IDs appear in design traceability.

## Limits and readiness
Document gates pass. Implementation has not begun; all task checkboxes remain unchecked. Metadata readiness means the specification is approved for implementation under batch fast-track, not that foundation integration or runtime acceptance is complete. Current system bus denial prevents verification of running/enabled services. Resume metadata is partially inaccessible. These checks must be repeated with the permitted host environment before affected mutation or success claims. Parent independent cross-spec review may identify follow-up document repairs.

## Cross-spec contract amendment — PASS, consumer correction
Parent cross-review identified that the no-autostart packaging support had no defined foundation API. The foundation amendment defines `install_packages(request: PackageRequest, *, prevent_service_start: bool = False) -> None` in its task 2.4. Resource design and task 1.3 now require that prerequisite and call `install_packages(request, prevent_service_start=True)`. Foundation owns policy-rc.d conflict detection, unchanged preservation of known deny policy, temporary deny-all state and journal recovery; resource code only consumes the contract. Protected-hook/no-go checks remain independent, with no boot/crypto authorization implied by startup suppression.

Fresh mechanical check after this correction: all 26 acceptance criteria remain mapped in tasks and design; both documents contain the exact guarded-install call and foundation task 2.4 prerequisite. No requirements, runtime files or foundation files changed in this consumer correction. Foundation implementation readiness remains an upstream condition.

## Final independent batch review

Cross-spec re-review after the documented repairs: PASS. See
[the portfolio review](../cross-spec-review.md). Prior pending-review notes above
are historical; runtime/implementation acceptance remains pending.
