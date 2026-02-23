# Project Keats

Poem-a-Day app built on legally safe public-domain poetry.

## Data Sources

### PoetryDB (`data/poetrydb/`)
- **all_poems.json** — 2,268 poems from 127 authors (public domain)
- **authors.json** — author index
- Source: [PoetryDB](https://poetrydb.org)

### Project Gutenberg (`data/gutenberg/` → `data/gutenberg_parsed/`)
- **66 raw text files** from Project Gutenberg poetry collections
- **32 collections parsed** into individual poems via `scripts/parse_gutenberg.py`
- **3,003 unique poems** (after deduplication against PoetryDB)
- 19 authors including Frost, Yeats, Hardy, Wilde, Dickinson, Wordsworth, Burns, Kipling, Sappho

Top authors by poem count:
| Author | Poems |
|--------|-------|
| Robert Burns | 533 |
| Emily Dickinson | 436 |
| Walt Whitman | 339 |
| Christina Rossetti | 245 |
| William Wordsworth | 240 |
| Omar Khayyam (tr. Fitzgerald) | 176 |
| Samuel Taylor Coleridge | 166 |
| W.B. Yeats | 156 |
| Thomas Hardy | 151 |
| John Donne | 130 |
| Oscar Wilde | 104 |
| Sappho | 85 |
| Robert Frost | 47 |

### Curated Excerpts (`data/excerpts.json`)
- **22 excerpts** from epic/long-form works and Shakespeare speeches
- Extracted via `scripts/extract_excerpts.py` and `scripts/extract_shakespeare.py`

## Schema (per poem)

| Field | Description |
|-------|-------------|
| title | Poem title |
| author | Author name |
| lines | Array of text lines |
| linecount | Number of lines (string) |
| reading_time_minutes | Estimated reading time |
| source | Source collection title (Gutenberg only) |
| source_id | Project Gutenberg ID (Gutenberg only) |
| category | Genre category (Gutenberg only) |

## Scripts

- `scripts/parse_gutenberg.py` — Parse Gutenberg poetry collections into individual poems
- `scripts/extract_excerpts.py` — Extract famous passages from epic/long-form works
- `scripts/extract_shakespeare.py` — Extract Shakespeare monologues/speeches

## Next Steps
- Ingestion pipeline with source adapters and rights verification
- Metadata enrichment (publication year, copyright status, jurisdiction)
- Daily poem picker algorithm
