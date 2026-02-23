"""
Parse the Oxford Book of English Verse (Gutenberg pg66619) into catalog entries.
Matches poems against the ranked top-1000 list, filters by reading time,
and deduplicates against the existing catalog.
"""
import json
import os
import re
from difflib import SequenceMatcher

BASE = os.path.join(os.path.dirname(__file__), '..', 'data')
CATALOG = os.path.join(BASE, 'catalog.json')
OBEV_FILE = os.path.join(BASE, 'gutenberg', 'pg66619.txt')
RANKED_LIST = os.path.join(BASE, 'ranked_top1000.txt')
WORDS_PER_MINUTE = 200
MAX_MINUTES = 5


def norm(s):
    return re.sub(r'[^\w\s]', '', s.strip().lower())


def parse_obev(filepath):
    """Parse all poems from the Oxford Book of English Verse."""
    with open(filepath, encoding='utf-8-sig') as f:
        text = f.read()
    lines = text.split('\n')

    poems = []
    current_author = 'Anonymous'

    # Pattern for poem headers: _N._ _Title_ or _N._ _Title line 1_
    poem_header_re = re.compile(r'^_(\d+)\.\_ _(.+)_\s*$')
    # Pattern for author headers: ALL CAPS, not indented, at least 2 words or known single names
    author_re = re.compile(r'^([A-Z][A-Z .\',()\-]+)$')
    # Pattern for date lines after author
    date_re = re.compile(r'^\d{4}\??[-–]?\d{0,4}\??$')
    circa_re = re.compile(r'^[cb]\.\s*\d{4}')
    # Footnote/glossary lines: _N._ word] meaning
    footnote_re = re.compile(r'^\s+_\d+\.\_ ')

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for author header
        if not line.startswith(' ') and not line.startswith('_'):
            m = author_re.match(line.strip())
            if m:
                candidate = m.group(1).strip()
                # Filter out non-author lines
                skip_words = {'PREFACE', 'CONTENTS', 'NUMBER', 'PAGE', 'PRINTED',
                              'OXFORD', 'THE', 'OF', 'AND', 'TO', 'FROM',
                              'ELIZABETHAN', 'NUMBERS', 'BY', 'UNNAMED',
                              'APPENDIX', 'INDEX', 'NOTES', 'GLOSSARY'}
                first_word = candidate.split()[0] if candidate.split() else ''
                if (len(candidate) > 3 and first_word not in skip_words
                        and not all(w in skip_words for w in candidate.split())):
                    current_author = candidate.title()
                    # Fix common title-case issues
                    current_author = current_author.replace(' Of ', ' of ')
                    current_author = current_author.replace(' The ', ' the ')
                    current_author = current_author.replace(' And ', ' and ')
                    current_author = current_author.replace(' De ', ' de ')
                    current_author = current_author.replace(' Von ', ' von ')
                i += 1
                continue

        # Check for poem header
        m = poem_header_re.match(line.strip())
        if m:
            num = int(m.group(1))
            title = m.group(2).strip().rstrip('_')
            # Clean italic markers from title
            title = title.replace('_', '')

            # Skip date line if present
            i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            if i < len(lines) and (date_re.match(lines[i].strip()) or circa_re.match(lines[i].strip())):
                i += 1

            # Skip blank lines before poem body
            while i < len(lines) and not lines[i].strip():
                i += 1

            # Collect poem lines until next poem header or author header
            poem_lines = []
            while i < len(lines):
                l = lines[i]

                # Stop at next poem header
                if poem_header_re.match(l.strip()):
                    break

                # Stop at next author header (ALL CAPS, non-indented, not a poem line)
                if not l.startswith(' ') and l.strip():
                    am = author_re.match(l.strip())
                    if am:
                        candidate = am.group(1).strip()
                        first_word = candidate.split()[0] if candidate.split() else ''
                        skip_words = {'PREFACE', 'CONTENTS', 'NUMBER', 'PAGE', 'PRINTED',
                                      'OXFORD', 'THE', 'OF', 'AND', 'TO', 'FROM',
                                      'ELIZABETHAN', 'NUMBERS', 'BY', 'UNNAMED',
                                      'APPENDIX', 'INDEX', 'NOTES', 'GLOSSARY'}
                        if (len(candidate) > 3 and first_word not in skip_words
                                and not all(w in skip_words for w in candidate.split())):
                            break

                # Skip footnote/glossary lines
                if footnote_re.match(l):
                    i += 1
                    continue

                # Skip [Illustration] markers
                if l.strip().startswith('[Illustration'):
                    i += 1
                    continue

                poem_lines.append(l)
                i += 1

            # Trim trailing blank lines
            while poem_lines and not poem_lines[-1].strip():
                poem_lines.pop()
            # Trim leading blank lines
            while poem_lines and not poem_lines[0].strip():
                poem_lines.pop(0)

            # Strip common leading indentation (poems are indented with spaces)
            if poem_lines:
                min_indent = float('inf')
                for pl in poem_lines:
                    if pl.strip():
                        indent = len(pl) - len(pl.lstrip())
                        min_indent = min(min_indent, indent)
                if min_indent > 0 and min_indent < float('inf'):
                    poem_lines = [pl[min_indent:] if len(pl) > min_indent else pl for pl in poem_lines]

            if poem_lines:
                non_blank = [l for l in poem_lines if l.strip()]
                word_count = sum(len(l.split()) for l in non_blank)
                rt = round(word_count / WORDS_PER_MINUTE, 1)

                poems.append({
                    'num': num,
                    'title': title,
                    'author': current_author,
                    'lines': poem_lines,
                    'linecount': str(len(non_blank)),
                    'source': 'gutenberg_obev',
                    'category': 'classic',
                    'reading_time_minutes': rt,
                })
            continue

        i += 1

    return poems


def load_ranked_list(path):
    """Parse the ranked list from a text file."""
    with open(path) as f:
        content = f.read()
    lines = content.split('\n')
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


def match_ranked(title, author, ranked_lookup):
    nt, na = norm(title), norm(author)
    author_last = na.split()[-1] if na.split() else na

    for (rt, ra), rank in ranked_lookup.items():
        ra_last = ra.split()[-1] if ra.split() else ra
        if author_last == ra_last or SequenceMatcher(None, na, ra).ratio() > 0.7:
            if SequenceMatcher(None, nt, rt).ratio() > 0.75:
                return rank
    return None


def is_in_catalog(title, author, catalog_keys):
    nt, na = norm(title), norm(author)
    if (nt, na) in catalog_keys:
        return True
    author_last = na.split()[-1] if na.split() else na
    for (ct, ca) in catalog_keys:
        if author_last in ca and SequenceMatcher(None, nt, ct).ratio() > 0.8:
            return True
    return False


def main():
    print("Parsing Oxford Book of English Verse...")
    poems = parse_obev(OBEV_FILE)
    print(f"  {len(poems)} poems parsed")

    # Show author distribution
    authors = {}
    for p in poems:
        authors[p['author']] = authors.get(p['author'], 0) + 1
    print(f"  {len(authors)} authors")
    for a, c in sorted(authors.items(), key=lambda x: -x[1])[:15]:
        print(f"    {a}: {c}")

    # Load ranked list
    ranked = load_ranked_list(RANKED_LIST)
    print(f"\n  {len(ranked)} ranked poems loaded")
    ranked_lookup = {}
    for r in ranked:
        ranked_lookup[(norm(r['title']), norm(r['author']))] = r['rank']

    # Load existing catalog
    with open(CATALOG) as f:
        catalog = json.load(f)
    print(f"  {len(catalog)} poems in catalog")
    catalog_keys = set()
    for p in catalog:
        catalog_keys.add((norm(p['title']), norm(p['author'])))

    # Match against ranked list and deduplicate
    added = []
    skipped_time = 0
    skipped_dupe = 0
    skipped_no_match = 0

    for poem in poems:
        rank = match_ranked(poem['title'], poem['author'], ranked_lookup)
        if rank is None:
            skipped_no_match += 1
            continue

        if is_in_catalog(poem['title'], poem['author'], catalog_keys):
            skipped_dupe += 1
            continue

        if poem['reading_time_minutes'] > MAX_MINUTES:
            skipped_time += 1
            print(f"  OVER TIME: #{rank:3d} \"{poem['title']}\" — {poem['author']} ({poem['reading_time_minutes']}min)")
            continue

        entry = {
            'title': poem['title'],
            'author': poem['author'],
            'lines': poem['lines'],
            'linecount': poem['linecount'],
            'source': 'gutenberg_obev',
            'category': 'classic',
            'reading_time_minutes': poem['reading_time_minutes'],
        }
        added.append((rank, entry))
        catalog_keys.add((norm(poem['title']), norm(poem['author'])))

    added.sort(key=lambda x: x[0])

    print(f"\nResults:")
    print(f"  Matched ranked list: {len(added) + skipped_dupe + skipped_time}")
    print(f"  Already in catalog: {skipped_dupe}")
    print(f"  Over {MAX_MINUTES} min: {skipped_time}")
    print(f"  NEW poems to add: {len(added)}")

    print(f"\nNew poems by rank:")
    for rank, entry in added:
        print(f"  #{rank:3d}  \"{entry['title']}\" — {entry['author']} ({entry['reading_time_minutes']}min)")

    # Add to catalog
    for rank, entry in added:
        catalog.append(entry)

    with open(CATALOG, 'w') as f:
        json.dump(catalog, f, indent=2)

    print(f"\nCatalog updated: {len(catalog)} total poems")


if __name__ == '__main__':
    main()
