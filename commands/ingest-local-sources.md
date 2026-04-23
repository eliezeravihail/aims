---
description: "Encode a local folder of PDF or text files into the BOOKS knowledge base"
allowed-tools: Read, Write, Bash
---

## Usage
/project:ingest-local-sources <path_to_folder> [--category <CATEGORY>] [--slug <slug>]

Example:
/project:ingest-local-sources ./papers/yolo --category OBJECT_DETECTION

## Step 1 — Scan
```bash
find <path_to_folder> -type f \( -name "*.pdf" -o -name "*.txt" -o -name "*.md" \)
```
Display the list of found files.

## Step 2 — Extract text
For each PDF:
```bash
pdftotext "<file.pdf>" "<file.txt>"
```
If pdftotext is not installed:
```bash
pip install pdfminer.six
python -c "from pdfminer.high_level import extract_text; print(extract_text('<file.pdf>'))"
```
For .txt and .md files — read directly with the Read tool.

## Step 3 — Identify context
From the extracted text identify:
- Document title
- Authors (if present)
- Main topics (up to 10)
- Publication year (if mentioned)

## Step 4 — Dedupe check
Read `skills/BOOKS/<CATEGORY>/_meta.md` and check:
- Is there a book with a similar slug?
- Is topic overlap > 80%?
If yes — report and ask the user whether to continue.

## Step 5 — Encode
For each identified topic create:
`skills/BOOKS/<CATEGORY>/<slug>_<topic>.md`

Each file must contain:
- Core definitions
- Key algorithms / patterns
- One code example (if applicable)
- Common pitfalls
- Connections to other topics in the source

## Step 6 — Update _meta.md
Append one row:
| <slug> | <title> | local_v1 | <quality_score> | <today> | false | — |

Quality score heuristic:
- Known tier_1a source = 0.85+
- Research paper with citations = 0.75+
- Anonymous document = 0.60

## Step 7 — Summary report
- How many files were processed
- Which topics were created
- Assigned quality_score
- Any duplicates found
