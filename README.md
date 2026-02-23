# Project Keats

Poem-a-Day app built on legally safe public-domain poetry.

## Data Sources

### PoetryDB (`data/poetrydb/`)
- **all_poems.json** — 2,268 poems from 127 authors (public domain)
- **authors.json** — author index
- Source: [PoetryDB](https://poetrydb.org)

### Planned
- Project Gutenberg poetry anthologies
- Wikisource public-domain poems

## Schema (per poem)

| Field | Description |
|-------|-------------|
| title | Poem title |
| author | Author name |
| lines | Array of text lines |
| linecount | Number of lines |

## Next Steps
- Ingestion pipeline with source adapters and rights verification
- Metadata enrichment (publication year, copyright status, jurisdiction)
- Daily poem picker algorithm
