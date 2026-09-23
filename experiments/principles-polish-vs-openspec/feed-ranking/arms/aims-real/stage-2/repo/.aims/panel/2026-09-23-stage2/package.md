ROLE
You are a design Worker — a senior engineer as capable as the Guide. The design is the deliverable. This is a
DESIGN-ONLY task: write no implementation code and create no source files. Type signatures, interface
sketches and a few illustrative lines are welcome where they make a boundary concrete. If evidence
invalidates the objective, report it instead of expanding scope. Do not read other files in
.aims/panel/2026-09-23-stage2/ except this package — other Workers' drafts must stay unseen; your work must
be independent. (Reading .aims/panel/2026-09-23-feed-ranking/ is also not needed.)

CONTEXT: THE EXISTING DESIGN
Stage 1 is designed (not yet implemented) in DESIGN.md at the repo root — read it in full; it is the
codebase you are changing. Also read goals.md (product decisions, stage 1 AND the new "Stage 2" section),
architecture.md, decisions/0001-stage1-architecture.md, base-dependencies.md.

DESIGN GOAL
Absorb two new product rules — eligibility (block/mute) and diversity (≤ 2 same-author in a row) — into the
stage-1 architecture so that each new rule has exactly one owner, is modelled as the kind of thing it is,
and every stage-1 rule keeps its single owner and its exact behavior. The result must stay buildable:
changed/added modules, concrete Python signatures, the request contract (library and CLI JSON) for the
lists and the item metadata, the types crossing each seam, the error vocabulary additions.

The hard decisions at its core (decide them, with reasons and rejected alternatives):
(a) Where "an ineligible item never appears" lives, so that no entry path can surface one, and where it
    sits relative to validation and scoring (validity comes first — see goals.md).
(b) Diversity turns "the order" from a pure sort key into a sequence built from the ranked order. Who owns
    "the order" now, how the stage-1 rank order (score desc, id asc, exact) and the diversity arrangement
    relate, and how the infeasible tail behaves (omitted — see goals.md) — without a second owner of order
    or of the score.
(c) What each item now carries (author, topics) and what the request carries (the lists), and where each
    new validation rule is owned — consistent with how stage 1 owns its input rules.

BEHAVIOR IT MUST SATISFY (constraint — grounded product decisions; the full text is goals.md "Stage 2")
- Request carries, next to `user` and candidates: a block list (author ids) and a mute list (topic ids).
  Both required; empty allowed; repeated entries allowed. Service stores nothing; `user` still does not
  affect the result.
- Each candidate: exactly one required author id (non-empty str); a required collection of zero or more
  topic ids (each non-empty str; repeats allowed = one). Missing/malformed author, topics, or list entry →
  whole request rejected, naming the item where applicable. Matching exact, case-sensitive.
- Blocked author OR any topic muted → the item is absent from the feed. Never shown low; no sentinel score.
- Validity first: every candidate (eligible or not) must satisfy the stage-1 contract (signals in [0,1],
  unique id, …) and the new metadata contract; otherwise the request is rejected. Eligibility applies only
  to a valid request.
- Diversity (hard): from the eligible items in stage-1 rank order (score desc, id asc), build the feed
  position by position; at each position place the highest-ranked remaining item that would not make a
  third consecutive same-author item. Deferred items keep relative order. When only items by the author of
  the last two placed items remain, they are omitted and the feed ends.
  Examples: a1[A] a2[A] a3[A] a4[A] b1[B] b2[B] → a1 a2 b1 a3 a4 b2 ;
            a1[A] a2[A] a3[A] b1[B] c1[C] → a1 a2 b1 a3 c1 ;
            a1[A] a2[A] a3[A] → a1 a2 ;
            b1[B] a1[A] a2[A] a3[A] → b1 a1 a2  (a3 omitted; stated consequence of the greedy reading).
- Response shape unchanged: ordered items each with its own stage-1 score + weights version. Removed
  items are simply absent; no counts reported. The feed is no longer strictly score-descending.
- Empty block and mute lists and no author runs >2 → exactly the stage-1 result.
- All candidates ineligible → empty feed, not an error.
- Everything else in stage 1 unchanged: scoring formula, exact Decimal numbers, weights, version id,
  reload semantics and one-version-per-request, error types' handling, CLI exit codes.

WHY NOW
A new product change has been received; both rules land on the order that stage 1 fixed in one owner
(`rank_feed`, key (score.copy_negate(), item_id)).

EXIT CRITERIA (how the result will be measured)
- Buildable: every added/changed signature in Python; CLI request JSON shape; rule → owner → entry-path
  table updated for every stage-1 and stage-2 rule.
- Ineligible items absent on every entry path (library, CLI, internal ranking function); a blocked item
  with the top score is absent; an item with one muted topic among several is absent.
- An invalid-but-ineligible item still rejects the request (bad signal; duplicate id with an ineligible
  twin).
- Empty lists and no long runs → byte-identical stage-1 output (characterization).
- Diversity: all four examples above; runs of 1, 2, exactly 3; interleaving; many authors; single author;
  infeasible tail; ties inside and across authors still broken by id; a blocked item between two runs does
  not "break" a run (diversity runs on the filtered sequence); scores shown unchanged.
- No stage-1 rule gains a second owner; no new rule has two.
- Subtractive and concept-fit passes clean: no -inf / sentinel score, no penalty term in the score, no
  synthetic or placeholder item, no flag argument switching behaviour.

PRESERVE
All of DESIGN.md stage 1 except the order rule the change deliberately rewrites. The pure core / thin shell
boundary; FeedService as the only mutable state; Decimal exactness traps (copy_negate, EXACT context).

WHAT "GOOD" AIMS AT
The standard is .claude/skills/aims-guide/references/design-principles.md (read it), and for a change to an
existing design, .claude/skills/aims-guide/references/add-feature-principles.md (read it) — the target, not
a checklist. Match the stage-1 design's grain (frozen value types validated in their constructor,
from_mapping for runtime key sets, one error type per distinct handling). Where a principle doesn't apply
at this scale, don't force it; say why.

SUBSTRATE (fixed; do not revisit)
Python 3.11+, standard library only. Single process. No network/database/persistence.

TESTING (to include in the design, not to run)
Say how the design is verified test-first: which decisions get which tests, including characterization of
stage-1 behavior before the change, and adversarial edges (empty lists, repeated list entries, case
differences, empty topics, item with a muted and an unmuted topic, blocked item with top score, all
ineligible, invalid ineligible item, every diversity example, infeasible tail, ties).

NON-GOALS
Storing the lists; per-user weights; diversity by topic or configurable limit; reporting removed items;
pagination; a generic rule/filter plugin framework; stages not yet revealed. The modules, classes and
interfaces are YOURS to choose.

BEFORE RETURNING
Run a subtractive pass: for every type, guard, wrapper or abstraction you introduced, name the present
product force that requires it; delete what fails. Run a concept-fit pass: is each element the kind of
thing it is (eligibility is a filter; diversity is a sequence constraint)?

RETURN
Write your full design to the file named in your axis block (markdown): it must be a complete stage-2
architecture document (it may reference DESIGN.md sections that are unchanged instead of copying them, but
every changed section must be complete). Include: module skeleton (changed/added), public signatures, the
types crossing each seam, error vocabulary additions, the rule → owner → entry-path table (all rules), the
hard decisions with reasons and rejected alternatives, the test plan, what you cut in the subtractive pass.
Then reply with a 10-line summary.
