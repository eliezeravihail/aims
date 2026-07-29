# Plan: Base aims on the Capsa capsule format
Status: draft
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

### שלב ב' — מקד מחדש את כלי aims ל-`.capsa/` (עוקב, גדול)

- **hooks**: `session-start` (מציף `.capsa/plans` + `decisions` + charter);
  `prompt-submit` (מזריק גוף insight לפי `code_globs`); `post-edit-marker`
  (מסמן insights נושאי-קוד dirty); `stop-consolidate` + `consolidate.sh`
  (מוסיף Deltas לגוף ה-insight); `pre-write`/`exit-plan-mode` (קוראים
  `.capsa/plans`).
- **memory scripts** (`_lib.sh`, `mark`, `find-dirty`, `lint`, `check-refs`,
  `consolidate`, `readme-sync`, `doctor`): פרסינג frontmatter YAML של Capsa
  במקום הסכמה הביתית; `lint` מאציל ל-`validator/validate.py`.
- **commands** (`/plan`, `/install-on`): `/plan` כותב ל-`.capsa/plans/`;
  `/install-on` מבצע bootstrap ל-`.capsa/` בפרויקט-יעד (מחליף את זריעת
  `docs/adr|plans|memory`).
- **tests**: מותאמים לפריסת `.capsa/`.
- **הסרה**: `docs/adr|plans|memory` + `docs/adr/README.md` +
  `readme-sync.sh` (האינדקס נגזר עכשיו). `docs/index.html` נשאר.

## Open design questions

1. **שלב ב' עכשיו או אחר-כך?** שלב א' לבדו כבר "מבסס את aims על Capsa"
   ברמת-הנתונים ובר-אימות (validator עובר), בלי לשבור כלום. שלב ב' הוא
   מאמץ נפרד וגדול (~15 סקריפטים + טסטים). המלצה: לאשר ולבצע את שלב א'
   עכשיו, ולפצל את שלב ב' ל-PR/סשן נפרד.
2. **חלון-כפילות.** בין שלב א' לשלב ב' גם `.capsa/decisions/` וגם
   `docs/adr/` קיימים עם אותו תוכן — מפר זמנית את "בית יחיד" (§1.4).
   מקובל כחלון-מיגרציה, או שעדיף לבצע א'+ב' יחד למרות הגודל?
3. **סטטוס ADRs שלא באנום.** aims משתמש ב-"accepted (amended by 0026)",
   "superseded by 0020". Capsa: `superseded` דורש `superseded_by` מספרי.
   מיפוי: amended→`accepted`+tag; superseded→`superseded`+`superseded_by`.
   מאשר?
4. **לזרוע requirements?** aims לא מנהל requirements פורמליים היום. אפשר
   לגזור 3–4 מה-README ("hooks inform never block", "zero deps",
   "idempotent install", "single-dispatch") עם verification-block, או
   להשאיר את התיקייה נעדרת. המלצה: להשאיר נעדרת בשלב א'.

## Verification

- `python3 validator/validate.py .capsa` → נקי (manifest + כל רשומה מול schema).
- `bash tests/*.sh` (חבילת aims הקיימת) → ירוקה (שלב א' לא נוגע בכלים).
- ספירת המרה: `ls .capsa/decisions | wc -l` = 30 (+ה-ADR החדש = 31);
  כל `docs/memory` leaf → insight; כל `docs/plans` → plan.
- בדיקת רגרסיה ב-validator: להשחית frontmatter אחד, לוודא כישלון, לשחזר.

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
