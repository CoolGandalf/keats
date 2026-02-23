"""
Fill gaps in the catalog using the Poetry Foundation dataset from HuggingFace.
Matches poems against the ranked top-1000 list, filters for reading time,
and deduplicates against the existing catalog.
"""
import json
import os
import re
from difflib import SequenceMatcher
from datasets import load_dataset

BASE = os.path.join(os.path.dirname(__file__), '..', 'data')
CATALOG = os.path.join(BASE, 'catalog.json')
RANKED_LIST = os.path.join(os.path.dirname(__file__), '..', 'data', 'ranked_top1000.json')
WORDS_PER_MINUTE = 200
MAX_MINUTES = 5


def norm(s):
    return re.sub(r'[^\w\s]', '', s.strip().lower())


def parse_ranked_list(path):
    """Parse the ranked list from a text file."""
    with open(path) as f:
        lines = f.readlines()
    ranked = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.match(r'^\d+$', line):
            rank = int(line)
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines):
                title = lines[i].strip().lstrip('\t')
                i += 1
                while i < len(lines) and not lines[i].strip():
                    i += 1
                if i < len(lines):
                    author = lines[i].strip().lstrip('\t')
                    ranked.append({'rank': rank, 'title': title, 'author': author})
        i += 1
    return ranked


def clean_pf_poem(raw_text):
    """Clean Poetry Foundation poem text into lines array."""
    # Remove \r\r\n artifacts
    text = raw_text.replace('\r\r\n', '\n').replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    # Strip leading/trailing blank lines
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


def reading_time(lines):
    word_count = sum(len(line.split()) for line in lines if line.strip())
    return round(word_count / WORDS_PER_MINUTE, 1)


def is_in_catalog(title, author, catalog_keys):
    """Check if poem is already in catalog."""
    nt, na = norm(title), norm(author)
    # Exact match
    if (nt, na) in catalog_keys:
        return True
    # Fuzzy
    author_last = na.split()[-1] if na.split() else na
    for (ct, ca) in catalog_keys:
        if author_last in ca and SequenceMatcher(None, nt, ct).ratio() > 0.8:
            return True
    return False


def match_ranked(title, author, ranked_lookup):
    """Find matching entry in ranked list. Returns rank or None."""
    nt, na = norm(title), norm(author)
    author_last = na.split()[-1] if na.split() else na

    for (rt, ra), rank in ranked_lookup.items():
        ra_last = ra.split()[-1] if ra.split() else ra
        if author_last == ra_last or SequenceMatcher(None, na, ra).ratio() > 0.7:
            if SequenceMatcher(None, nt, rt).ratio() > 0.75:
                return rank
    return None


def main():
    print("Loading Poetry Foundation dataset...")
    ds = load_dataset('suayptalha/Poetry-Foundation-Poems', split='train')
    print(f"  {len(ds)} poems loaded")

    print("Loading existing catalog...")
    with open(CATALOG) as f:
        catalog = json.load(f)
    print(f"  {len(catalog)} poems in catalog")

    # Build catalog lookup
    catalog_keys = set()
    for p in catalog:
        catalog_keys.add((norm(p['title']), norm(p['author'])))

    # Load ranked list
    ranked_path = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'ranked_top1000.txt'
    )
    if not os.path.exists(ranked_path):
        # Try alternate location
        import glob
        candidates = glob.glob(os.path.expanduser(
            '~/.claude/projects/-Users-leighllewelyn/*/tool-results/b5b23d7.txt'
        ))
        if candidates:
            ranked_path = candidates[0]

    ranked = parse_ranked_list(ranked_path)
    print(f"  {len(ranked)} ranked poems loaded")

    # Build ranked lookup
    ranked_lookup = {}
    for r in ranked:
        ranked_lookup[(norm(r['title']), norm(r['author']))] = r['rank']

    # Process Poetry Foundation poems
    added = []
    skipped_time = 0
    skipped_dupe = 0
    skipped_no_match = 0

    for row in ds:
        poet = (row['Poet'] or '').strip()
        title = (row['Title'] or '').strip().replace('\r\n', '').replace('\r', '').strip()
        poem_text = row['Poem'] or ''

        if not poet or not title or not poem_text:
            continue

        # Check if it matches ranked list
        rank = match_ranked(title, poet, ranked_lookup)
        if rank is None:
            skipped_no_match += 1
            continue

        # Check if already in catalog
        if is_in_catalog(title, poet, catalog_keys):
            skipped_dupe += 1
            continue

        # Parse and check reading time
        lines = clean_pf_poem(poem_text)
        rt = reading_time(lines)
        if rt > MAX_MINUTES:
            skipped_time += 1
            continue

        linecount = len([l for l in lines if l.strip()])

        poem = {
            'title': title,
            'author': poet,
            'lines': lines,
            'linecount': str(linecount),
            'source': 'poetry_foundation',
            'category': 'classic',
            'reading_time_minutes': rt,
            'rank': rank,
        }
        added.append(poem)
        catalog_keys.add((norm(title), norm(poet)))

    # Sort by rank
    added.sort(key=lambda p: p['rank'])

    print(f"\nResults:")
    print(f"  Matched ranked list: {len(added) + skipped_dupe + skipped_time}")
    print(f"  Already in catalog: {skipped_dupe}")
    print(f"  Over {MAX_MINUTES} min: {skipped_time}")
    print(f"  NEW poems added: {len(added)}")

    print(f"\nNew poems by rank tier:")
    for lo, hi in [(1, 100), (101, 200), (201, 400), (401, 600), (601, 800), (801, 1000)]:
        tier = [p for p in added if lo <= p['rank'] <= hi]
        print(f"  {lo}-{hi}: {len(tier)} poems")

    print(f"\nTop-100 additions:")
    for p in added:
        if p['rank'] <= 100:
            print(f"  #{p['rank']:3d}  \"{p['title']}\" — {p['author']} ({p['reading_time_minutes']}min)")

    print(f"\nTop-200 additions:")
    for p in added:
        if 100 < p['rank'] <= 200:
            print(f"  #{p['rank']:3d}  \"{p['title']}\" — {p['author']} ({p['reading_time_minutes']}min)")

    # Merge into catalog
    # Remove rank field before saving (internal use only)
    for p in added:
        del p['rank']

    catalog.extend(added)

    with open(CATALOG, 'w') as f:
        json.dump(catalog, f, indent=2)

    print(f"\nCatalog updated: {len(catalog)} total poems")
    print(f"Saved to {CATALOG}")


if __name__ == '__main__':
    main()
