# knowledge-library-agents

Claude Code plugin — multi-agent system for building and maintaining a technical knowledge base (BOOKS).

## Agents
| Agent | Role | Model |
|-------|------|-------|
| Agent 4 | Book Finder | Haiku |
| Agent 5 | Book Encoder | Sonnet |

## Commands
| Command | What it does |
|---------|-------------|
| `/project:books-init` | Encode the book queue (`books-init-queue.yaml`) |
| `/project:ingest-local-sources <folder>` | Encode local PDFs or text files |
| `/project:find-book <domain>` | Find the best foundational book for a domain |
| `/project:encode-book` | Encode a single book |
| `/project:books-status` | Coverage and quality report |
| `/project:books-update` | Find new editions and refresh stale books |
| `/project:books-audit` | Knowledge hygiene: dedupe, ranking, decay |

## Install
1. Clone this repo
2. Open the folder in Claude Code
3. Run `/project:books-init --priority 1` to encode the initial queue

## Ingest local sources
```bash
/project:ingest-local-sources ./papers/yolo --category OBJECT_DETECTION --slug yolo_papers
/project:ingest-local-sources ./notes/pytorch --category TRAINING_OPTIMIZATION
```
Supports: `.pdf` (via pdftotext or pdfminer.six), `.txt`, `.md`

## Knowledge categories
ANN · CNN · VISION · OBJECT_DETECTION · REFACTORING · ALGORITHMS · NLP · RL · TRAINING_OPTIMIZATION · DISTRIBUTED_SYSTEMS
