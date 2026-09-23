# Measurement of the merged stage-2 design (round 1) — fix-list, most severe first

F1 (S3, §1 contracts / test coverage — regression of recorded content). The stage-1 per-module test plan
(stage-1 DESIGN §10: numbers, signals, weights, request, ranking, config_file, service incl. the concurrency
"no mix" and "overlapping reloads" tests, cli exit codes 2/3/4/5) was dropped in the merge. §14 Step 0 says
"build stage 1 exactly as specified in decisions/0001 and this document's unchanged sections", but no
section of DESIGN.md now holds those tests (the stage-1 copy is at .aims/panel/2026-09-23-stage2/DESIGN-stage1.md,
§10). Direction: restore the stage-1 test obligations inside §14 as the Step-0 suite (adjusted only where
stage 2 changed a signature — e.g. the request test now goes through the fixture helper), so DESIGN.md
alone is buildable.

F2 (S2, §0/§5 encapsulation claim not by construction). §9 "Why the run limit can't become a second owner"
says its only use of the input is position and author. It receives `Candidate`, which carries `item_id`
(and signals), so re-ranking by id or by signals is expressible; the barrier against scores holds (no score
on Candidate), the barrier against re-ranking is a convention. §8 states its residual honestly; §9 does
not. Direction: state precisely what holds by construction (cannot read or change a score; returns the
candidates it received) and what is a convention guarded by a named test (never compares ids/signals — the
"each position = earliest placeable remaining item" property check), in the same form as §8's residual.
Do NOT reintroduce a new module or a generic T parameter (that was weighed and rejected; decisions/0002).

F3 (S2, §3 naming / contract consistency). §5 message table row "topics is a string, a mapping or not
iterable" shows the message "… not a string" for all three, while §3.1 `_require_id_set` gives a
different message for a mapping / non-iterable ("must be a collection of ids"). Direction: make the table
and the helper contract agree (one row per distinct message), same for the list rows.

F4 (S1, §5). `Candidate.from_mapping` now reports missing/unknown for non-signal keys (`author`, `topics`)
through `read_signal_fields`; the design does not say how it keeps `InvalidRequest.signal` None for those
while setting it for a missing signal. Direction: state the rule in one line (signal is set only when the
key is in SIGNAL_NAMES) and the unknown-key message (`item 'b': unknown 'topic'`).

F5 (S1, §10 / §2 SLAP of the plan). §14 Step 1 introduces "a no-op arrangement step" as a refactor — a
placeholder with no rule. Direction: either drop it (the split arrives with Step 4) or justify it.

F6 (S1, buildability / acceptance evidence). There is no stage-2 end-to-end worked example with concrete
numbers and its expected output (stage 1 has goals.md's core scenario). Direction: add one CLI example —
weights, a request with a blocked item, a muted item, and an author run that forces a deferral and an
omitted tail — with the exact expected stdout (compute scores exactly per §6; verify by hand).

Everything else measured clean: eligibility owner and funnel; validity-first by construction; run-limit
algorithm (simulated: all four goals.md examples + 4 more + 20k random property checks pass); stage-1
owners preserved; no sentinel/penalty/flag; subtractive and concept-fit passes.
