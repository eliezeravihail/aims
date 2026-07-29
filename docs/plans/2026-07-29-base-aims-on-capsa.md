# Plan: Base aims on the Capsa capsule format
Status: in-progress
Started: 2026-07-29

## תקציר מנהלים

aims המציא בעצמו את משמעת-הארטיפקטים (ADRs, תוכניות, עץ-זיכרון) אבל אחסן
אותה בפריסה ביתית (`docs/adr` + `docs/plans` + `docs/memory`) עם סכמה
משלו. Capsa (הריפו הפרטי שלך, `capsa_version 0.2.0`) הוא בדיוק אותה
משמעת מנורמלת לתקן **פסיבי, נייד, מבוסס-סכמה**: קפסולת `.capsa/` אחת עם
`capsule.yaml`, `decisions/`, `plans/`, `insights/{code,dev,design}/`,
`charter.md` (ועוד טיפוסים ש-aims לא משתמש בהם: requirements, issues,
dependencies, releases). ה-README של Capsa אף מגדיר את התפקיד המדויק
של כלי כמו aims: *"התנהגות שמתחזקת את עצמה חיה מעל Capsa כשכבה
אופציונלית."*

התוכנית מבססת את aims על Capsa בשני שלבים בלתי-תלויים:
**שלב א' (נתונים)** — יוצר קפסולת `.capsa/` תואמת-סכמה לתוך ריפו aims
עצמו, וממגר לתוכה את 30 ה-ADRs → `decisions/`, את התוכניות →
`plans/`, ואת 15 צמתי-הזיכרון → `insights/` (הצמתים נושאי-הקוד →
`insights/code/` עם `code_globs`, ההיסטוריים → `insights/dev/`); מוסיף
`capsule.yaml` + `charter.md` נגזר מ-CLAUDE.md, ומכניס את ה-validator
של Capsa (stdlib-only) כשער אימות. **שלב ב' (כלים)** — ממקד מחדש את
ה-hooks/סקריפטים/פקודות/טסטים של aims כך שיקראו-יכתבו את `.capsa/`
במקום `docs/`, ומסיר את הפריסה הישנה. בסוף: aims = שכבת המשמעת
הפעילה, Capsa = פורמט האחסון הפסיבי; מקור-אמת אחד.

בחירה מודעת: אימוץ **הפריסה המלאה** של Capsa אבל אכלוס רק טיפוסי-הרשומות
ש-aims באמת מנהל (decisions/plans/insights/charter/manifest);
requirements/issues/dependencies/releases נשארים נעדרים (§2: תיקייה
נעדרת = "אין עדיין", לא שגיאה) עד שיהיה בהם צורך.

## מיפוי: ארטיפקט aims → רשומת Capsa

| aims (היום) | Capsa (`.capsa/`) | הערות המרה |
|---|---|---|
| `docs/adr/NNNN-slug.md` (×30) | `decisions/NNNN-slug.md` | כותרת-פרוזה (`Status:`/`Date:`/`Supersedes:`) → frontmatter YAML (`id,title,status,date,supersedes,superseded_by,discussion_ref,tags`). גוף Context/Decision/Consequences/Alternatives כבר תואם §4.3. |
| `docs/plans/*.md` | `plans/NNNN-slug.md` | `Status:` → `status` (`in-progress`→`in_progress`); הוספת `id,kind,opened`. גוף → Goal/Approach/Work-breakdown/Verification/Open-questions (§4.2). |
| `docs/memory/**` צומת נושא-קוד (×11) | `insights/code/<tag>-<leaf>.md` | `code:` globs → `code_globs` (חובה ל-kind:code, §4.9). גוף Purpose/Invariants/Pointers/Deltas נשמר בפרוזה. |
| `docs/memory/**` צומת `kind: topic` (done/grunt/templates/commands) | `insights/dev/*.md` | breadcrumbs היסטוריים, בלי code_globs. |
| `CLAUDE.md` (Workflow/Models/Hooks) | `charter.md` | Vision/Constraints/Ground-rules/Initial-decisions (§4.8). CLAUDE.md נשאר כהוראות-כלי; ה-charter הוא הצד הפרויקטי. |
| — | `capsule.yaml` | חדש: `capsa_version 0.2.0`, `project{name:aims,slug:aims,repo,created}`, `status: maintained`. |
| `docs/adr/README.md` (index) | — | נגזר; Capsa לא מאחסן אינדקסים (§1.4). מוחלף בסריקת התיקייה. |
| `docs/memory/README.md` + `readme-sync.sh` | — | אותו דבר — האינדקס נגזר, לא מאוחסן. |

## Changes

מסודר כך שכל שלב נבדק בנפרד. שלב א' **תוסף ולא-שובר** (הכלים ממשיכים
לקרוא `docs/`); שלב ב' ממקד מחדש ומסיר את הישן.

### שלב א' — צור את קפסולת aims (`.capsa/`)

#### `.capsa/capsule.yaml` (חדש)
```yaml
capsa_version: "0.2.0"
project:
  name: "aims"
  slug: aims
  repo: "https://github.com/eliezeravihail/aims"
  created: 2026-05-06
status: maintained
```

#### `.capsa/charter.md` (חדש, נגזר מ-CLAUDE.md)
`## Vision` (משמעת פיתוח רזה, dispatch יחיד) · `## Constraints`
(markdown+bash, אפס תלויות, אפס מצב גלובלי) · `## Ground rules`
(planning-as-behavior, hooks-inform-never-block, trivial-skip-declared)
· `## Initial decisions of record` (מצביע ל-decisions/0002, 0020).

#### `.capsa/decisions/NNNN-slug.md` (×30, ממוגר)
המרה מכנית של כל ADR: בניית frontmatter מה-`Status:`/`Date:`/`Supersedes:`/
`Superseded by:` הקיימים; מיפוי סטטוס לאנום Capsa
(`accepted|proposed|superseded|deprecated`) — הניואנס "accepted (amended
by 0026)" עובר ל-`tags: [amended-by-0026]` + `status: accepted`. ה-`id`
מספרי = ה-NNNN. הגוף נשאר כמות שהוא (כבר Context/Decision/Consequences/
Alternatives).

#### `.capsa/plans/NNNN-slug.md` (ממוגר)
תוכניות שהושלמו + הנוכחית, ממוספרות מחדש NNNN לפי תאריך. `status`
ממופה; גוף מותאם לכותרות §4.2 היכן שחסר.

#### `.capsa/insights/code/*.md` + `insights/dev/*.md` (×15, ממוגר)
מ-`docs/memory/`: צמתים עם `code:` לא-ריק → `insights/code/<tag>-<leaf>.md`
עם `kind: code` + `code_globs`; צמתים `kind: topic` → `insights/dev/`.
הגוף (Purpose/Invariants/Pointers/Deltas) נשמר.

#### `validator/validate.py` (מוטמע מ-Capsa, stdlib-only)
העתקה מ-`capsa/validator/` + `schema/`. שער האימות של השלב:
`python3 validator/validate.py .capsa` חייב לעבור נקי.

#### `docs/adr/NNNN-adopt-capsa-format.md` (ADR חדש ב-aims)
"aims מאמץ את Capsa כפורמט הקפסולה שלו." ממשיך (partial-supersede) את
ADR-0005 (פריסת docs/), ADR-0007/0008/0028 (סכמת הזיכרון הביתית → מוחלפת
ב-insights של Capsa). מתעד את המתח: החלטת Capsa `0002` ("aims נשאר
כמו-שהוא") הייתה החלטת-scope של *Capsa*; זו החלטה עצמאית של *aims* לאמץ
בכיוון ההפוך.

### מודל המצב של המנוע — **הוכרע: טריות מחושבת** (state model)

הכרעת-עיצוב מרכזית לשלב ב'. הקפסולה היא פורמט-שמירה **סטטי**; aims (ה-hooks
והמעטפת) הוא **התוכנה** שמחשבת ומתחזקת. לכן השלישייה הביתית של aים
(`dirty`/`last_touched`/`last_consolidated` בתוך כל צומת) מתמוטטת:

| aims היום (מאוחסן בצומת) | Capsa (המודל החדש) |
|---|---|
| `last_consolidated` | ← `updated:` על ה-insight (עובדה דורבלית, לגיטימית) |
| `last_touched` | מיותר — git יודע מתי הקוד השתנה |
| `dirty: true/false` | **מחושב, לא מאוחסן**: insight "מיושן" ⇔ קובץ ב-`code_globs` שלו קיבל commit **אחרי** `updated:`, או שיש עליו diff לא-מקומם |

הנמקה: §1.4 של Capsa ("מה שנגזר מרשומות — מחושב ע"י צרכנים, לא מאוחסן")
ו-§1.5 (אין run-state בקפסולה). טריות **אינה** run-state של המפעיל (מי-מבצע,
משמרות, עלות) — היא מידע-פרויקט שנראה בקפסולה דרך `updated:`, אבל הדגל
עצמו נגזר ולא נשמר. יתרון-לוואי: אין דגל שיוצא מסנכרון; מחיקת המטמון לא
פוגעת בנכונות. **דורש אפס שינוי ב-Capsa** (משתמש ב-`updated:` הקיים).

- `find-dirty` הופך ל-`find-stale`: לכל insight, `git log -1 --since=<updated>`
  על ה-`code_globs` (+ `git diff` לשינויים לא-מקומָמים) → מיושן/לא.
- ה-marker hook (`post-edit-marker`) נשאר רק כ**מטמון-ביצועים** אופציונלי
  ב-`.claude/` ("אלה נגעו בסשן") — מאיץ, לא מקור-אמת.
- קונסולידציה מסתיימת ב-`mark.sh <insight> consolidated` שרק **מקדם את
  `updated:`** (ומנקה את המטמון) — לא נוגע בשום דגל.

### שלב ב' — מקד מחדש את כלי aims ל-`.capsa/` (עוקב, גדול)

- **memory scripts** (`_lib.sh`, `mark`, `find-dirty`→`find-stale`, `lint`,
  `check-refs`, `consolidate`, `doctor`; `readme-sync` נמחק): קריאת
  frontmatter YAML של Capsa; טריות מחושבת מ-`updated:`+git (למעלה); `mark
  consolidated` מקדם `updated:` בלבד; `lint` מאציל ל-`validator/validate.py`.
- **hooks**: `session-start` (מציף `.capsa/plans` + `decisions` אחרונים +
  `charter`); `prompt-submit` (מזריק גוף insight לפי התאמת `code_globs`);
  `post-edit-marker` (מטמון-טריות אופציונלי + הערה עובדתית);
  `stop-consolidate`+`consolidate.sh` (מוסיף שורת-דלתא מתוארכת לגוף
  ה-insight + מקדם `updated:`); `pre-write`/`exit-plan-mode` (קוראים/כותבים
  `.capsa/plans` עם `status:` YAML במקום `Status:` פרוזה).
- **commands** (`/plan`, `/install-on`): `/plan` כותב `.capsa/plans/NNNN-slug.md`
  (frontmatter של Capsa); `/install-on` מבצע bootstrap ל-`.capsa/` (+ validator)
  בפרויקט-יעד במקום זריעת `docs/adr|plans|memory`.
- **tests**: ששת החבילות מותאמות לפריסת `.capsa/` ולמודל הטריות-המחושבת.
- **הסרה**: `docs/adr|plans|memory` + `docs/adr/README.md` + `readme-sync.sh`
  (אינדקס נגזר). `docs/index.html` נשאר.
- **dogfooding**: לערוך `templates/` ואז לסנכרן ל-`.claude/` דרך
  `/install-on .` בסוף — כדי לא לשבור את ה-hooks החיים של הסשן באמצע.

## Open design questions — הוכרעו

1. **עומק / פיצול** — RESOLVED: מבצעים גם שלב א' וגם שלב ב'. שלב א' כבר
   הושלם, אומת ונדחף (additive). שלב ב' עוקב באותו PR (#42).
2. **מודל המצב** — RESOLVED: **טריות מחושבת** (ראה הסעיף למעלה). לא מאחסנים
   דגל `dirty`; `updated:` + git הם המקור, marker = מטמון אופציונלי.
3. **מיפוי סטטוס-ADR** — RESOLVED (בוצע בשלב א'): amended→`accepted`+tag;
   superseded מלא→`superseded`+`superseded_by`; multi-supersede→tags.
4. **requirements** — RESOLVED: התיקייה נשארת נעדרת בינתיים (§2: נעדר =
   "אין עדיין"). תיזרע רק כשיהיה צורך אמיתי.
5. **חלון-כפילות** — RESOLVED: מקובל כחלון-מיגרציה קצר בתוך אותו PR; שלב ב'
   מסיר את `docs/` ומשאיר בית יחיד (`.capsa/`).

## Status

- **שלב א' — הושלם, אומת (validator: conforming), נדחף** (commit f051ace,
  PR #42): capsule.yaml, charter, 30 decisions, 19 plans, 15 insights,
  decision 0031, validator+schema מוטמעים.
- **שלב ב' — הוכרע ומעוגן (מודל טריות-מחושבת); טרם מומש.**

## Verification

שלב א' (בוצע):
- `python3 validator/validate.py .capsa` → conforming ✔.
- `bash tests/*.sh` (חבילת aims הקיימת) → ירוקה (שלב א' לא נוגע בכלים).
- בדיקת רגרסיה ב-validator: השחתת frontmatter → כישלון; שוחזר → ✔.

שלב ב' (יעדים):
- כל ששת חבילות הטסטים ירוקות אחרי המיקוד ל-`.capsa/`.
- `find-stale` מחשב טריות נכון: עריכת קובץ ב-`code_globs` של insight →
  מזוהה מיושן; `mark consolidated` מקדם `updated:` → כבר לא מיושן.
- `.capsa/` הוא הבית היחיד: `docs/adr|plans|memory` הוסרו; `validator`
  עדיין conforming; `bash -n` נקי על כל הסקריפטים; `copies-identical` עובר.

## Close-out checklist
- ADR: WRITE — NNNN-adopt-capsa-format (partial-supersede 0005/0007/0008/0028)
- Nodes: UPDATE — צמתי memory הרלוונטיים (או, אם שלב ב' מבוצע, מוסרים)
- CLAUDE.md: UPDATE — הפניה ל-`.capsa/` כמקור-האמת + Build&test עם ה-validator
- Tests: הטמעת `validator/validate.py`; חבילת bash קיימת נשארת
- TODO: שלב ב' (מיקוד הכלים) אם נדחה

## Risks / unknowns
- המרת 30 ADRs + 15 צמתים היא עבודת-תוכן; ה-validator + סכמות תופסים
  סטיות-פורמט מיד אחרי כל קובץ.
- מיפוי סטטוס-אנום עלול לאבד ניואנס ("partial 0011", "amended by 0026") —
  נשמר ב-`tags` וב-`superseded_by`, לא נמחק.
- Capsa הוא `0.1.0`→`0.2.0` צעיר; אם התקן ישתנה, ה-`capsa_version`
  המוצמד מגן — צרכן בודק שהוא תומך בגרסה.
