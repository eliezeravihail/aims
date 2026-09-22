# Phase 1 — product-owner log

Every question an arm stopped to ask, and the verbatim answer given from `../hidden/oracle.md`; the same
question gets the same words in every arm (`PROTOCOL.md` §4.6). Questions raised only at hand-back, after the
arm had already chosen and finished, are listed separately.

**The rule applied to every question, in every arm.** A question answered in `../hidden/oracle.md` gets that
answer. A question the card itself answers gets the card's own sentence(s), quoted verbatim, and nothing else —
this is no new information, since every arm's prompt carries the same card. Any other question gets the default:
*"I don't know — choose a simple, sensible technical approach."* Proposals an arm says it will adopt "unless you
object" get no reply: the product owner volunteers nothing.

| arm | question (verbatim) | answer (verbatim) |
|---|---|---|
| w2 (aims) | 1. "Files under `docs/` that sit outside every `docs/<lang>/` folder" — shared, or an error? | "I don't know — choose a simple, sensible technical approach." |
| w2 (aims) | 2. "An explicit `nav:` in `mkdocs.yml`" — one nav for every language, or one per language? | "I don't know — choose a simple, sensible technical approach." |
| w2 (aims) | 3. "A page that exists only in a non-default language (for example `docs/fr/extra.md` with no `docs/en/extra.md`)" — leave it out, publish only in French, or fail? | The card says: "A page may exist in any subset of the languages." and "Every page exists in every language." |
| w1 (aims) | 1. "A page that exists only in a non-default language, e.g. docs/fr/extra.md with no docs/en/extra.md" — French only, error, or ignored? | The card says: "A page may exist in any subset of the languages." and "Every page exists in every language." |
| w1 (aims) | 2. "An explicit `nav:` in mkdocs.yml for a multi-language site" — fixed text verbatim, translated titles override, or per-language overrides? | "I don't know — choose a simple, sensible technical approach." |
| w1 (aims) | 3. "Non-page files, and anything in docs/ outside a declared language folder" — shared, or ignored with a warning? | "I don't know — choose a simple, sensible technical approach." |
| w1 (aims) | 4. "Right-to-left languages such as `he`" — lang/dir attributes, full RTL layout, or nothing? | "The page should read right to left. Nothing beyond what the theme already supports." *(from `oracle.md`, stage 1)* |
| w3 (aims) | Q1. "A page that exists in a non-default language but not in the default one" — error, French only, or shown in every language? | The card says: "A page may exist in any subset of the languages." and "Every page exists in every language." |
| w3 (aims) | Q2. "An explicit `nav:` in `mkdocs.yml` on a multi-language site" — one nav, or per-language overrides? | "I don't know — choose a simple, sensible technical approach." |

*w3 also said it would treat right-to-left as out of scope "unless you say otherwise" — a stated decision, not a question: no reply, per the rule.*
| w5 (unaided) | *(at hand-back, after finishing — not a stop to ask)* "Decisions for the product owner to confirm": pages only in a non-default language left out; nav section headings untranslated; labels need Babel; right-to-left | none given — raised after the arm had chosen and finished |
