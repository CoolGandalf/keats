"""
Post-processing pipeline for Keats project:
1. Remove parser artifacts (editorial apparatus misidentified as poems)
2. Cross-collection deduplication
3. Quality fixes (Hardy dates, etc.)
4. Integration with PoetryDB + excerpts into unified catalog
"""
import json
import os
import re
from difflib import SequenceMatcher

BASE = os.path.join(os.path.dirname(__file__), '..', 'data')
GUTENBERG_PARSED = os.path.join(BASE, 'gutenberg_parsed', 'all_parsed.json')
POETRYDB = os.path.join(BASE, 'poetrydb', 'all_poems.json')
EXCERPTS = os.path.join(BASE, 'excerpts.json')
OUTPUT = os.path.join(BASE, 'catalog.json')

WORDS_PER_MINUTE = 200
MAX_READING_MINUTES = 5


# --- Step 1: Artifact removal ---

# Titles that are editorial apparatus, not poems
ARTIFACT_TITLE_PATTERNS = [
    r'^variants?\s+(on|of)\b',
    r'^footnotes?\s+(on|to)\b',
    r'^sub-footnote',
    r'^sub-variant',
    r'^the\s+poems?$',
    r'^appendix\b',
    r'^preface\b',
    r'^introduction\b',
    r'^advertisement\b',
    r'^note\s+on\b',
    r'^notes\s+on\b',
    r'^marmaduke\.?\s*"?\s*$',  # Character name from The Borderers (play)
]

# Yeats play character names parsed as poem titles
YEATS_PLAY_TITLES = {
    'usheen', 's. patric', 'naschina', 'almintor', 'oona',
    'the wanderings of usheen',
}


def is_artifact(poem):
    """Return True if a poem entry is actually editorial apparatus."""
    title_lower = poem['title'].strip().lower()
    author_lower = poem['author'].strip().lower()

    # Wordsworth critical edition artifacts
    if 'wordsworth' in author_lower:
        for pattern in ARTIFACT_TITLE_PATTERNS:
            if re.match(pattern, title_lower, re.IGNORECASE):
                return True

    # Yeats play fragments
    if 'yeats' in author_lower:
        if title_lower in YEATS_PLAY_TITLES:
            return True

    # Generic: lines full of editorial markers
    if poem['lines']:
        first_line = poem['lines'][0].strip()
        if first_line.startswith('[Variant') or first_line.startswith('[Footnote'):
            return True

    # Table-of-contents entries (body is just a list of other poem titles)
    if ', etc' in title_lower or title_lower.endswith(' etc'):
        return True

    return False


def remove_artifacts(poems):
    """Remove editorial artifacts misidentified as poems."""
    clean = []
    removed = 0
    for p in poems:
        if is_artifact(p):
            removed += 1
        else:
            clean.append(p)
    return clean, removed


# --- Step 2: Cross-collection deduplication ---

def normalize_title(title):
    """Normalize title for comparison."""
    t = title.strip().lower()
    t = re.sub(r'[^\w\s]', '', t)  # Remove punctuation
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def normalize_first_line(lines):
    """Get normalized first non-empty line."""
    for line in lines:
        stripped = line.strip()
        if stripped:
            return re.sub(r'[^\w\s]', '', stripped.lower()).strip()
    return ''


def cross_dedup(poems):
    """Remove cross-collection duplicates, keeping the version with more lines."""
    # Group by (normalized_title, author)
    groups = {}
    for poem in poems:
        key = (normalize_title(poem['title']), poem['author'].strip().lower())
        groups.setdefault(key, []).append(poem)

    deduped = []
    removed = 0
    for key, group in groups.items():
        if len(group) == 1:
            deduped.append(group[0])
        else:
            # Same title + author from different sources
            # Check if they're actually the same poem (compare first lines)
            # Group by first line to separate genuinely different poems with same title
            by_first_line = {}
            for p in group:
                fl = normalize_first_line(p['lines'])
                # Use fuzzy matching for first lines
                matched = False
                for existing_fl in by_first_line:
                    if SequenceMatcher(None, fl[:60], existing_fl[:60]).ratio() > 0.8:
                        by_first_line[existing_fl].append(p)
                        matched = True
                        break
                if not matched:
                    by_first_line[fl] = [p]

            for fl, subgroup in by_first_line.items():
                # Keep the version with the most lines
                best = max(subgroup, key=lambda p: int(p['linecount']))
                deduped.append(best)
                removed += len(subgroup) - 1

    return deduped, removed


# --- Step 3: Quality fixes ---

def fix_trailing_dates(poem):
    """Remove trailing date lines from poems (Hardy, Coleridge, etc.)."""
    if not poem['lines']:
        return poem
    # Check last few non-blank lines for standalone dates
    # Patterns: "1867.", "1798.", "_December_ 1900.", "1867-1870."
    date_pattern = re.compile(r'^_?[A-Za-z]*_?\s*\d{4}[\-–]?\d{0,4}\.?\s*$')
    lines = list(poem['lines'])
    changed = False
    # Strip trailing blank lines first
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    # Remove trailing date lines (may be multiple)
    while lines and date_pattern.match(lines[-1].strip()):
        lines = lines[:-1]
        changed = True
        # Strip blank lines exposed by removal
        while lines and not lines[-1].strip():
            lines = lines[:-1]
    if changed:
        poem = dict(poem)
        poem['lines'] = lines
        non_blank = [l for l in lines if l.strip()]
        poem['linecount'] = str(len(non_blank))
    return poem


def fix_reading_time(poem):
    """Recalculate reading time."""
    word_count = sum(len(line.split()) for line in poem['lines'] if line.strip())
    poem['reading_time_minutes'] = round(word_count / WORDS_PER_MINUTE, 1)
    return poem


def apply_quality_fixes(poems):
    """Apply all quality fixes."""
    fixed = []
    for p in poems:
        p = fix_trailing_dates(p)
        p = fix_reading_time(p)
        fixed.append(p)
    return fixed


# --- Step 4: Integration ---

def normalize_poetrydb(poems):
    """Ensure PoetryDB poems have consistent schema."""
    normalized = []
    for p in poems:
        entry = {
            'title': p['title'],
            'author': p['author'],
            'lines': p['lines'],
            'linecount': p.get('linecount', str(len([l for l in p['lines'] if l.strip()]))),
            'source': 'poetrydb',
            'category': 'classic',
        }
        # Add reading time if missing
        word_count = sum(len(line.split()) for line in p['lines'] if line.strip())
        entry['reading_time_minutes'] = p.get('reading_time_minutes', round(word_count / WORDS_PER_MINUTE, 1))
        normalized.append(entry)
    return normalized


def normalize_excerpts(excerpts):
    """Convert excerpts to standard poem schema."""
    normalized = []
    for e in excerpts:
        text = e.get('text', '')
        # Skip entries with corrupted text (Gutenberg boilerplate leaked in)
        if not text or 'equipment' in text[:100] or 'donations' in text[:200]:
            continue
        lines = text.split('\n')
        # Strip leading blank lines and title line if it matches
        while lines and not lines[0].strip():
            lines = lines[1:]
        if lines and lines[0].strip().lower() == e['title'].strip().lower():
            lines = lines[1:]
        entry = {
            'title': e['title'],
            'author': e['author'],
            'lines': lines,
            'linecount': str(len([l for l in lines if l.strip()])),
            'source': f"excerpt:{e.get('source', 'unknown')}",
            'category': e.get('category', 'excerpt'),
            'reading_time_minutes': e.get('reading_time_minutes', 0),
            'note': e.get('note', ''),
        }
        normalized.append(entry)
    return normalized


def build_catalog(poetrydb_poems, gutenberg_poems, excerpt_poems, max_minutes=MAX_READING_MINUTES):
    """Build unified catalog, filtering long poems."""
    catalog = []
    long_count = 0

    for source_name, poems in [('poetrydb', poetrydb_poems),
                                ('gutenberg', gutenberg_poems),
                                ('excerpts', excerpt_poems)]:
        for p in poems:
            if p['reading_time_minutes'] > max_minutes:
                long_count += 1
                continue
            catalog.append(p)

    return catalog, long_count


# --- Main ---

def main():
    print("=" * 60)
    print("KEATS POST-PROCESSING PIPELINE")
    print("=" * 60)

    # Load data
    with open(GUTENBERG_PARSED) as f:
        gutenberg = json.load(f)
    print(f"\n1. Loaded {len(gutenberg)} Gutenberg poems")

    with open(POETRYDB) as f:
        poetrydb_raw = json.load(f)
    print(f"   Loaded {len(poetrydb_raw)} PoetryDB poems")

    with open(EXCERPTS) as f:
        excerpts_raw = json.load(f)
    print(f"   Loaded {len(excerpts_raw)} excerpts")

    # Step 1: Remove artifacts
    gutenberg, artifact_count = remove_artifacts(gutenberg)
    print(f"\n2. Artifact removal: {artifact_count} editorial artifacts removed")
    print(f"   Remaining: {len(gutenberg)} Gutenberg poems")

    # Step 2: Cross-collection dedup
    gutenberg, cross_dupe_count = cross_dedup(gutenberg)
    print(f"\n3. Cross-collection dedup: {cross_dupe_count} duplicates removed")
    print(f"   Remaining: {len(gutenberg)} unique Gutenberg poems")

    # Step 3: Quality fixes
    gutenberg = apply_quality_fixes(gutenberg)
    print(f"\n4. Quality fixes applied (Hardy dates, reading times)")

    # Save cleaned Gutenberg output
    cleaned_path = os.path.join(BASE, 'gutenberg_parsed', 'all_parsed_clean.json')
    with open(cleaned_path, 'w') as f:
        json.dump(gutenberg, f, indent=2)
    print(f"   Saved cleaned Gutenberg: {cleaned_path}")

    # Step 4: Build unified catalog
    poetrydb = normalize_poetrydb(poetrydb_raw)
    excerpts = normalize_excerpts(excerpts_raw)

    catalog, long_count = build_catalog(poetrydb, gutenberg, excerpts)
    print(f"\n5. Unified catalog built:")
    print(f"   PoetryDB:   {len(poetrydb_raw)} poems")
    print(f"   Gutenberg:  {len(gutenberg)} poems")
    print(f"   Excerpts:   {len(excerpts_raw)} entries")
    print(f"   Over {MAX_READING_MINUTES} min (excluded): {long_count}")
    print(f"   TOTAL in catalog: {len(catalog)}")

    # Per-source breakdown
    source_counts = {}
    for p in catalog:
        src = p.get('source', 'unknown')
        if src == 'poetrydb':
            key = 'PoetryDB'
        elif src.startswith('excerpt:'):
            key = 'Excerpts'
        else:
            key = 'Gutenberg'
        source_counts[key] = source_counts.get(key, 0) + 1
    for k, v in sorted(source_counts.items()):
        print(f"     {k}: {v}")

    # Per-author summary
    author_counts = {}
    for p in catalog:
        author_counts[p['author']] = author_counts.get(p['author'], 0) + 1
    print(f"\n   Authors: {len(author_counts)}")
    for author, count in sorted(author_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"     {author}: {count}")

    # Save catalog
    with open(OUTPUT, 'w') as f:
        json.dump(catalog, f, indent=2)
    print(f"\n   Saved: {OUTPUT} ({len(catalog)} poems)")

    return catalog


if __name__ == '__main__':
    main()
