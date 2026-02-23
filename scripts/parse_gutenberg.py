"""
Parse Project Gutenberg poetry collections into individual poems.
Outputs JSON matching the PoetryDB schema: title, author, lines, linecount, reading_time_minutes.
"""
import json
import os
import re
import sys
from difflib import SequenceMatcher

BASE = os.path.join(os.path.dirname(__file__), '..', 'data', 'gutenberg')
POETRYDB = os.path.join(os.path.dirname(__file__), '..', 'data', 'poetrydb', 'all_poems.json')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'gutenberg_parsed')
MANIFEST = os.path.join(BASE, 'manifest.json')

# Average reading speed for poetry (slower than prose)
WORDS_PER_MINUTE = 200

# Collections to skip (epics handled via excerpts, already well-represented, or complex formats)
SKIP_IDS = {
    21700,   # Don Juan (epic)
    5131,    # Childe Harold's Pilgrimage (epic)
    24280,   # Endymion (epic)
    610,     # Idylls of the King (epic)
    2383,    # Canterbury Tales (medieval, complex)
    70717,   # Faerie Queene Vol 1 (epic)
    72698,   # Faerie Queene Vol 2 (epic)
    26,      # Paradise Lost (epic)
    6130,    # Iliad (epic)
    3160,    # Odyssey (epic)
    8800,    # Divine Comedy (Cary)
    1004,    # Divine Comedy (Longfellow)
    228,     # Aeneid (epic)
    28621,   # Metamorphoses (epic)
    4800,    # Shelley Complete Works (massive, 182 already in PDB)
    2428,    # Pope Essay on Man (didactic)
    9800,    # Pope Rape of the Lock (already excerpted)
    45159,   # Rumi (complex prose/poetry mix)
    26288,   # Marvell To His Coy Mistress (file is a 404 HTML page, not downloaded)
    8601,    # Tennyson Early Poems (critical edition with heavy editorial apparatus — needs custom parser)
    # Shakespeare plays and narrative poems (handled separately)
    1041, 1045, 1505,
    1513, 1515, 1521, 1522, 1523, 1524, 1526, 1533,
    23042, 2257, 1103,
}


def read_gutenberg(pg_id):
    """Read a Gutenberg text file, stripping header/footer."""
    path = os.path.join(BASE, f'pg{pg_id}.txt')
    with open(path, encoding='utf-8') as f:
        text = f.read()

    # Strip BOM
    text = text.lstrip('\ufeff')

    # Extract between START and END markers
    start_match = re.search(r'\*\*\* START OF (?:THE )?PROJECT GUTENBERG EBOOK .+?\*\*\*', text)
    end_match = re.search(r'\*\*\* END OF (?:THE )?PROJECT GUTENBERG EBOOK .+?\*\*\*', text)

    if start_match:
        text = text[start_match.end():]
    if end_match:
        text = text[:end_match.start()]

    return text


def calculate_reading_time(lines):
    """Calculate reading time in minutes from lines of poetry."""
    word_count = sum(len(line.split()) for line in lines if line.strip())
    return round(word_count / WORDS_PER_MINUTE, 1)


def clean_lines(lines):
    """Clean poem lines: strip trailing whitespace, remove line numbers, normalize."""
    cleaned = []
    for line in lines:
        # Remove Gutenberg-style line numbers at end (e.g. "  10" at position 70+)
        line = re.sub(r'\s{4,}\d+\s*$', '', line)
        # Strip trailing whitespace
        line = line.rstrip()
        cleaned.append(line)

    # Remove leading/trailing blank lines
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return cleaned


def strip_indent(lines):
    """Remove common leading whitespace from all non-blank lines."""
    non_blank = [l for l in lines if l.strip()]
    if not non_blank:
        return lines
    min_indent = min(len(l) - len(l.lstrip()) for l in non_blank)
    if min_indent > 0:
        return [l[min_indent:] if l.strip() else '' for l in lines]
    return lines


def is_title_line(line):
    """Check if a line looks like a poem title."""
    stripped = line.strip()
    if not stripped or len(stripped) > 120:
        return False
    # Skip common non-title lines
    if stripped.startswith(('[', '(', '_', '*', '#')):
        return False
    if re.match(r'^(CONTENTS|PREFACE|NOTE|INDEX|INTRODUCTION TO|TRANSCRIBER)', stripped, re.IGNORECASE):
        return False
    if re.match(r'^\d{4}[.\s]?$', stripped):  # Year only
        return False
    if re.match(r'^(BY |EDITED |PRODUCED |LONDON|OXFORD|NEW YORK|MACMILLAN|METHUEN)', stripped, re.IGNORECASE):
        return False
    if re.match(r'^\*\s*\*\s*\*', stripped):  # Decorators
        return False
    if re.match(r'^\[Picture:', stripped):
        return False
    # Page number references
    if re.match(r'^PAGE\s*$', stripped, re.IGNORECASE):
        return False
    return True


def is_all_caps_title(line):
    """Check if a line is an ALL CAPS title (allowing punctuation)."""
    stripped = line.strip()
    if not stripped or len(stripped) < 2 or len(stripped) > 100:
        return False
    # Must have at least 2 letter characters
    letters = re.sub(r'[^A-Za-z]', '', stripped)
    if len(letters) < 2:
        return False
    # Check if all letters are uppercase
    if letters == letters.upper() and letters != letters.lower():
        # Not a Roman numeral alone
        if re.match(r'^[IVXLC]+\.?$', stripped):
            return False
        return True
    return False


def is_roman_numeral(line):
    """Check if a line is a Roman numeral (poem number)."""
    stripped = line.strip()
    return bool(re.match(r'^[IVXLC]+\.?\s*$', stripped))


def is_arabic_numeral(line):
    """Check if line is just a number (poem number)."""
    stripped = line.strip()
    return bool(re.match(r'^\d{1,4}\.?\s*$', stripped))


def skip_front_matter(text):
    """Skip publisher info, prefaces, TOC, etc. Return text starting at first poem."""
    lines = text.split('\n')

    # Strategy: find the end of contents/preface section
    # Look for patterns that indicate poems are starting

    # First, try to find a clear "poems start here" signal
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Some books have section headers like "SONGS OF INNOCENCE" before poems
        # but after the TOC. We need to distinguish TOC entries from actual content.

        # If we find a line that's just a few words followed by blank lines
        # and then indented text or regular text, that's likely a poem start.
        pass

    return text  # Will be handled per-collection


def make_poem(title, body_lines, author, source, source_id, category):
    """Create a poem dict matching the PoetryDB schema."""
    lines = clean_lines(body_lines)
    lines = strip_indent(lines)

    if not lines or not title:
        return None

    # Convert blank lines to empty strings (PoetryDB convention)
    final_lines = []
    for line in lines:
        final_lines.append(line if line.strip() else '')

    linecount = len([l for l in final_lines if l.strip()])
    reading_time = calculate_reading_time(final_lines)

    # Clean up title
    title = title.strip()
    title = re.sub(r'\s+', ' ', title)
    # Remove trailing periods from titles (Yeats style)
    title = title.rstrip('.')
    # Title case if all caps
    if title == title.upper() and len(title) > 3:
        title = title_case(title)

    return {
        'title': title,
        'author': author,
        'lines': final_lines,
        'linecount': str(linecount),
        'reading_time_minutes': reading_time,
        'source': source,
        'source_id': source_id,
        'category': category,
    }


def title_case(s):
    """Smart title case that handles articles, prepositions, etc."""
    small_words = {'a', 'an', 'the', 'and', 'but', 'or', 'nor', 'for', 'yet',
                   'so', 'at', 'by', 'in', 'of', 'on', 'to', 'up', 'as', 'is',
                   'it', 'if', 'my', 'no', 'do'}
    words = s.lower().split()
    result = []
    for i, word in enumerate(words):
        # Strip punctuation for checking
        clean = re.sub(r'[^a-z]', '', word.lower())
        if i == 0 or clean not in small_words:
            result.append(word.capitalize())
        else:
            result.append(word.lower())
    return ' '.join(result)


# ============================================================================
# Collection-specific parsers
# ============================================================================

def parse_frost(text, pg_id, author, source_title, category):
    """Parse Frost: title on own line, 4-space indented body."""
    lines = text.split('\n')
    poems = []

    # Skip to after the TOC (find first poem by looking for a non-indented
    # short line followed by blank line then indented text)
    # Frost TOC has indented entries with descriptions; poems have
    # unindented title then indented body.

    # Find end of TOC: the TOC entries are all indented with 4+ spaces.
    # First non-blank, non-indented line after a big gap = first poem title.
    i = 0
    # Skip any producer notes at top
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Find the contents section
    toc_start = None
    for j in range(i, len(lines)):
        if re.match(r'^\s*CONTENTS\s*$', lines[j], re.IGNORECASE):
            toc_start = j
            break

    if toc_start is not None:
        # Skip past TOC: find first poem (title line preceded by 2+ blank lines after TOC)
        blank_count = 0
        i = toc_start + 1
        while i < len(lines):
            if not lines[i].strip():
                blank_count += 1
            else:
                if blank_count >= 3 and not lines[i].startswith(' '):
                    break
                if lines[i].strip() and not lines[i].startswith(' '):
                    blank_count = 0
                else:
                    blank_count = 0
            i += 1
    else:
        # No TOC found, skip front matter heuristically
        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped and not stripped.startswith(('Produced', 'A BOY', 'NORTH OF', 'By ')):
                # Check if this could be first poem title
                if (not lines[i].startswith(' ') and len(stripped) < 60
                        and i + 2 < len(lines) and not lines[i + 1].strip()):
                    break
            i += 1

    # Now parse poems: title line (not indented, short) + body (indented or blank)
    current_title = None
    current_body = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for poem title: non-indented, relatively short, followed by blank+indented
        if (stripped and not line.startswith(' ') and len(stripped) < 80
                and is_title_line(line)):
            # Check if next non-blank line is indented (poem body)
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].startswith('    '):
                # This is a poem title
                if current_title and current_body:
                    poem = make_poem(current_title, current_body, author,
                                     source_title, pg_id, category)
                    if poem:
                        poems.append(poem)
                current_title = stripped
                current_body = []
                i += 1
                continue

        if current_title:
            current_body.append(line)

        i += 1

    # Don't forget the last poem
    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_blake(text, pg_id, author, source_title, category):
    """Parse Blake: section headers + ALL CAPS or Title Case titles."""
    lines = text.split('\n')
    poems = []

    # Skip front matter: find the actual SONGS OF INNOCENCE section
    # (not the TOC entry, but the section header before poems start)
    i = 0
    # The pattern is: "SONGS OF INNOCENCE" on its own line, then blank lines,
    # then "INTRODUCTION" as the first poem title
    for j, line in enumerate(lines):
        if line.strip() == 'INTRODUCTION' and j > 50:
            # Verify this is the real poem, not TOC
            # Check that it's preceded by section header or blank lines
            # and followed by blank line then poem text
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and lines[k].strip():
                i = j
                break

    current_title = None
    current_body = []
    section_name = None  # Track "Songs of Innocence" vs "Songs of Experience"

    while i < len(lines):
        stripped = lines[i].strip()

        # Track section headers
        if stripped in ('SONGS OF INNOCENCE', 'SONGS OF EXPERIENCE'):
            section_name = stripped
            i += 1
            continue

        # Skip [Picture:...] lines
        if stripped.startswith('[Picture:'):
            i += 1
            continue

        # Check for poem title: ALL CAPS or standalone short line after blank lines
        if (stripped and is_all_caps_title(lines[i])
                and is_title_line(lines[i])):
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
            current_title = stripped
            current_body = []
            i += 1
            continue

        if current_title:
            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_dickinson(text, pg_id, author, source_title, category):
    """Parse Dickinson: Roman numeral numbering with optional titles."""
    lines = text.split('\n')
    poems = []

    # Skip front matter: find first "I. LIFE." section or "I." poem number
    i = 0
    for j, line in enumerate(lines):
        stripped = line.strip()
        if stripped == 'I. LIFE.' or (stripped == 'I.' and j > 100):
            i = j
            break

    current_number = None
    current_title = None
    current_body = []
    current_section = None  # "LIFE", "LOVE", "NATURE", "TIME AND ETERNITY"

    while i < len(lines):
        stripped = lines[i].strip()

        # Section headers like "I. LIFE.", "II. LOVE.", etc.
        section_match = re.match(r'^[IVX]+\.\s+([A-Z][A-Z\s]+)\.\s*$', stripped)
        if section_match:
            if current_number and current_body:
                t = current_title or f'Poem {current_number}'
                poem = make_poem(t, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
                current_number = None
                current_title = None
                current_body = []
            current_section = section_match.group(1).strip()
            i += 1
            continue

        # Poem number: "I.", "II.", "III.", etc. or "CXVII." etc.
        if re.match(r'^[IVXLC]+\.\s*$', stripped) and len(stripped) < 10:
            # Save previous poem
            if current_number and current_body:
                t = current_title or f'Poem {current_number}'
                poem = make_poem(t, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)

            current_number = stripped.rstrip('.')
            current_title = None
            current_body = []
            i += 1

            # Check if next non-blank line is a title (ALL CAPS, short)
            while i < len(lines) and not lines[i].strip():
                i += 1

            if i < len(lines):
                next_stripped = lines[i].strip()
                # Title lines in Dickinson: ALL CAPS, short
                if (next_stripped and is_all_caps_title(lines[i])
                        and len(next_stripped) < 60
                        and not next_stripped.startswith('[')):
                    current_title = next_stripped
                    i += 1
                # Skip bracketed notes like [Published in "A Masque of Poets"...]
                while i < len(lines) and lines[i].strip().startswith('['):
                    # Skip multi-line bracket notes
                    while i < len(lines) and ']' not in lines[i]:
                        i += 1
                    i += 1  # skip the closing bracket line
            continue

        if current_number is not None:
            # Skip standalone section dividers
            if stripped.startswith('[') and stripped.endswith(']'):
                i += 1
                continue
            current_body.append(lines[i])

        i += 1

    if current_number and current_body:
        t = current_title or f'Poem {current_number}'
        poem = make_poem(t, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    # Renumber: use the title if available, otherwise "Poem N (section)"
    for p in poems:
        if p['title'].startswith('Poem '):
            num = p['title'].replace('Poem ', '')
            if current_section:
                p['title'] = f'Poem {num}'
            # First line as alt title if it's short enough
            first_line = next((l for l in p['lines'] if l.strip()), '')
            if first_line and len(first_line) < 60:
                p['title'] = first_line.strip().rstrip(',;:—–-')

    return poems


def parse_hardy(text, pg_id, author, source_title, category):
    """Parse Hardy: ALL CAPS titles, indented body, dates at end."""
    lines = text.split('\n')
    poems = []

    # Skip front matter: find past the CONTENTS section
    i = 0
    contents_found = False
    for j, line in enumerate(lines):
        if re.match(r'^\s*CONTENTS\s*$', line.strip()):
            contents_found = True
            continue
        if contents_found:
            # Skip TOC entries (they have page numbers)
            if line.strip() and not re.search(r'\d+\s*$', line.strip()):
                # Not a TOC entry — check if it's a Picture or section header
                if line.strip().startswith('[Picture:'):
                    continue
                if is_all_caps_title(line) and is_title_line(line):
                    i = j
                    break

    current_title = None
    current_body = []

    while i < len(lines):
        stripped = lines[i].strip()

        # Skip [Picture:...] lines
        if stripped.startswith('[Picture:'):
            i += 1
            continue

        # Check for poem title: ALL CAPS
        if (stripped and is_all_caps_title(lines[i])
                and is_title_line(lines[i]) and len(stripped) > 1):
            # Save previous poem
            if current_title and current_body:
                # Strip trailing date lines
                while current_body and re.match(r'^\s*\d{4}[\.\s]*$', current_body[-1]):
                    current_body.pop()
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
            current_title = stripped
            current_body = []
            i += 1
            continue

        if current_title:
            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        while current_body and re.match(r'^\s*\d{4}[\.\s]*$', current_body[-1]):
            current_body.pop()
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_wilde(text, pg_id, author, source_title, category):
    """Parse Wilde: ALL CAPS titles, centered/indented body with italics."""
    lines = text.split('\n')
    poems = []

    # Skip front matter: find past CONTENTS and NOTE sections
    i = 0
    # Find "POEMS" section header after contents
    for j, line in enumerate(lines):
        stripped = line.strip()
        if stripped == 'POEMS' and j > 50:
            i = j + 1
            break

    # Section headers to skip (these are group titles, not poem titles)
    section_headers = {'POEMS', 'ELEUTHERIA', 'ROSA MYSTICA', 'WIND FLOWERS',
                       'FLOWERS OF GOLD', 'IMPRESSIONS DE THÉÂTRE',
                       'THE FOURTH MOVEMENT', 'FLOWER OF LOVE',
                       'UNCOLLECTED POEMS (1876–1893)', 'UNCOLLECTED POEMS',
                       'DEVOTIONAL PIECES'}

    current_title = None
    current_body = []

    while i < len(lines):
        stripped = lines[i].strip()

        # Check for poem title: ALL CAPS
        if stripped and is_all_caps_title(lines[i]) and is_title_line(lines[i]):
            # Skip section headers
            if stripped.upper() in section_headers or stripped in section_headers:
                i += 1
                continue

            # Skip roman numeral sub-headers like "I." "II." etc.
            if re.match(r'^[IVX]+\.?\s*$', stripped):
                i += 1
                continue

            # Save previous poem
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)

            current_title = stripped
            current_body = []
            i += 1
            continue

        # Also catch Title Case titles for some poems
        if (stripped and not lines[i].startswith(' ')
                and len(stripped) < 60
                and stripped not in section_headers
                and not stripped.startswith(('_', '[', '(', '*'))
                and re.match(r'^[A-Z]', stripped)
                and not any(c.islower() and c2.isupper() for c, c2 in zip(stripped, stripped[1:]))):
            # Check if preceded by 2+ blank lines and followed by blank+text
            if i >= 2 and not lines[i-1].strip() and not lines[i-2].strip():
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and lines[j].strip():
                    # Possible title
                    if current_title and current_body:
                        poem = make_poem(current_title, current_body, author,
                                         source_title, pg_id, category)
                        if poem:
                            poems.append(poem)
                    current_title = stripped
                    current_body = []
                    i += 1
                    continue

        if current_title:
            # Clean italic markers
            body_line = lines[i].replace('_', '')
            current_body.append(body_line)

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_yeats(text, pg_id, author, source_title, category):
    """Parse Yeats shorter collections: Title with period, body text."""
    lines = text.split('\n')
    poems = []

    # Skip front matter — find past publisher info, copyright, etc.
    # Yeats front matter includes: title page, publisher, copyright, TOC
    # The actual poems start after repeated title or section header

    # Known front-matter terms to skip
    front_matter_terms = {
        'THE MACMILLAN COMPANY', 'MACMILLAN AND CO', 'LONDON', 'NEW YORK',
        'COPYRIGHT', 'ALL RIGHTS RESERVED', 'NORWOOD PRESS',
        'BY THE SAME WRITER', 'THE SECRET ROSE', 'THE CELTIC TWILIGHT',
        'THE WIND AMONG THE REEDS', 'THE SHADOWY WATERS',
        'IDEAS OF GOOD AND EVIL', 'POEMS', 'BEING POEMS',
    }

    i = 0
    # Find the first actual poem: look for an ALL CAPS line that's followed
    # by actual poetry (indented or regular text), after skipping all front matter
    # Strategy: skip until we find a title preceded by at least 2 blank lines
    # that is NOT a publisher/copyright term
    found_start = False
    for j, line in enumerate(lines):
        stripped = line.strip()
        if j < 30:
            continue
        if not stripped:
            continue
        # Skip known front matter
        is_front = False
        for term in front_matter_terms:
            if term in stripped.upper():
                is_front = True
                break
        if is_front:
            continue
        # Skip single-word items or items that are clearly not titles
        if stripped.startswith(('_', '[', '(', '*', 'BY ', 'Set ')):
            continue
        if re.match(r'^\d{4}', stripped):  # Year
            continue

        # Look for ALL CAPS title followed by poem content
        if (is_all_caps_title(line) and is_title_line(line)
                and len(stripped) > 3):
            # Check followed by blank then text
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines):
                next_line = lines[k].strip()
                # Next line should look like poetry (has lowercase letters)
                if next_line and any(c.islower() for c in next_line):
                    i = j
                    found_start = True
                    break

    if not found_start:
        i = 50  # fallback

    current_title = None
    current_body = []

    # Some Yeats collections have very long narrative poems (e.g. "The Old Age of Queen Maeve")
    # We'll include them and let the reading_time filter handle it

    while i < len(lines):
        stripped = lines[i].strip()

        # Stop at play sections (e.g. "THE GREEN HELMET" play in pg30488,
        # "ON BAILE'S STRAND" play in pg30652)
        if ('PERSONS OF THE PLAY' in stripped or 'DRAMATIS PERSONAE' in stripped
                or re.match(r'^_An Heroic', stripped)
                or re.match(r'^\s*SCENE:', stripped)):
            # Save current poem and stop
            if current_title and current_body:
                while current_body and re.match(r'^\s*[A-Z][a-z]+,?\s*\d{4}\.?\s*$', current_body[-1].strip()):
                    current_body.pop()
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
            break

        # Skip [Picture/Illustration] lines
        if stripped.startswith(('[Picture:', '[Illustration')):
            i += 1
            continue

        # Detect poem titles: ALL CAPS line ending with period, or
        # ALL CAPS line preceded by 2+ blank lines
        is_potential_title = False

        if stripped and len(stripped) < 80:
            if is_all_caps_title(lines[i]) and is_title_line(lines[i]):
                is_potential_title = True
            elif (stripped.endswith('.') and stripped[:-1] == stripped[:-1].upper()
                  and len(stripped) > 3 and stripped[:-1] != stripped[:-1].lower()):
                is_potential_title = True

        if is_potential_title:
            # Verify: preceded by blank lines or is first poem
            preceded_by_blank = (i == 0 or not lines[i-1].strip())
            if preceded_by_blank or current_title is None:
                if current_title and current_body:
                    # Remove trailing date lines like "August, 1902."
                    while current_body and re.match(r'^\s*[A-Z][a-z]+,?\s*\d{4}\.?\s*$', current_body[-1].strip()):
                        current_body.pop()
                    poem = make_poem(current_title, current_body, author,
                                     source_title, pg_id, category)
                    if poem:
                        poems.append(poem)
                current_title = stripped.rstrip('.')
                current_body = []
                i += 1
                continue

        if current_title:
            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        while current_body and re.match(r'^\s*[A-Z][a-z]+,?\s*\d{4}\.?\s*$', current_body[-1].strip()):
            current_body.pop()
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_yeats_poems(text, pg_id, author, source_title, category):
    """Parse Yeats 'Poems' (pg38877) — large volume with plays mixed in.
    Only extract lyric poems, skip dramatic works."""
    lines = text.split('\n')
    poems = []

    # This volume has: Crossways, The Rose, The Wind Among the Reeds, etc.
    # Plus plays like The Countess Cathleen, The Land of Heart's Desire
    # We need to detect and skip the plays.

    # Plays have character names in ALL CAPS followed by dialogue
    # They also have stage directions in brackets/italics

    # Skip front matter
    i = 0
    for j, line in enumerate(lines):
        stripped = line.strip()
        if stripped == 'CROSSWAYS' and j > 30:
            i = j
            break
        if stripped == 'THE SONG OF THE HAPPY SHEPHERD' and j > 30:
            i = j
            break

    # Sections that are plays (skip these entirely)
    play_titles = {
        'THE COUNTESS CATHLEEN', 'THE LAND OF HEART\'S DESIRE',
        'THE COUNTESS KATHLEEN', 'THE SHADOWY WATERS',
    }

    in_play = False
    current_title = None
    current_body = []

    # Section headers (group titles, not poem titles)
    section_headers = {'CROSSWAYS', 'THE ROSE', 'THE WIND AMONG THE REEDS',
                       'IN THE SEVEN WOODS', 'THE OLD AGE OF QUEEN MAEVE',
                       'BAILE AND AILLINN', 'NARRATIVE AND DRAMATIC',
                       'LYRICAL'}

    while i < len(lines):
        stripped = lines[i].strip()

        # Check for play start
        if stripped in play_titles:
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
                current_title = None
                current_body = []
            in_play = True
            i += 1
            continue

        # Detect play end: look for next ALL CAPS title that isn't a character name
        if in_play:
            if (stripped and is_all_caps_title(lines[i]) and is_title_line(lines[i])
                    and stripped not in play_titles
                    and not re.match(r'^[A-Z]+\.\s', stripped)  # Character name
                    and len(stripped) > 3
                    and i > 0 and not lines[i-1].strip()):
                # Check it's not a character name (followed by dialogue)
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    next_line = lines[j].strip()
                    if not (next_line.startswith('(') or next_line.startswith('[')):
                        in_play = False
                        # Fall through to title detection below
                    else:
                        i += 1
                        continue
                else:
                    in_play = False
            else:
                i += 1
                continue

        # Skip section headers
        if stripped in section_headers:
            i += 1
            continue

        # Poem title detection
        if (stripped and is_all_caps_title(lines[i]) and is_title_line(lines[i])
                and len(stripped) > 1):
            if i > 0 and not lines[i-1].strip():
                if current_title and current_body:
                    poem = make_poem(current_title, current_body, author,
                                     source_title, pg_id, category)
                    if poem:
                        poems.append(poem)
                current_title = stripped
                current_body = []
                i += 1
                continue

        if current_title:
            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_sonnets_numbered(text, pg_id, author, source_title, category):
    """Parse sonnet sequences numbered with Roman numerals (EBB, Shakespeare)."""
    lines = text.split('\n')
    poems = []

    # Skip front matter: find first "I" or "I." sonnet
    i = 0
    for j, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^I\.?\s*$', stripped) and j > 20:
            # Verify next non-blank line starts a poem
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and lines[k].strip():
                i = j
                break

    current_number = None
    current_body = []

    while i < len(lines):
        stripped = lines[i].strip()

        # Roman numeral line (with or without trailing period)
        if re.match(r'^[IVXLC]+\.?\s*$', stripped) and len(stripped) < 10:
            if current_number is not None and current_body:
                title = _numbered_title(current_number, source_title)
                poem = make_poem(title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)

            current_number = stripped.rstrip('.')
            current_body = []
            i += 1
            continue

        if current_number is not None:
            current_body.append(lines[i])

        i += 1

    if current_number is not None and current_body:
        title = _numbered_title(current_number, source_title)
        poem = make_poem(title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def _numbered_title(number, source_title):
    """Generate title for numbered poem sequences."""
    if 'Sonnets from the Portuguese' in source_title:
        return f'Sonnets from the Portuguese: {number}'
    elif 'Rubaiyat' in source_title:
        return f'Rubaiyat: {number}'
    elif 'Sonnet' in source_title:
        return f'Sonnet {number}'
    return f'{number}'


def parse_rubaiyat(text, pg_id, author, source_title, category):
    """Parse Rubaiyat: numbered quatrains with Roman numerals and periods.
    Has two editions (First Edition and Fifth Edition) — parse both."""
    lines = text.split('\n')
    poems = []

    # Find "First Edition" header
    i = 0
    for j, line in enumerate(lines):
        if line.strip() == 'First Edition':
            i = j + 1
            break

    current_number = None
    current_body = []
    edition = 'First Edition'

    while i < len(lines):
        stripped = lines[i].strip()

        # Edition headers
        if stripped == 'Fifth Edition':
            # Save last poem from first edition
            if current_number is not None and current_body:
                title = f'Rubaiyat {current_number} ({edition})'
                poem = make_poem(title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
                current_number = None
                current_body = []
            edition = 'Fifth Edition'
            i += 1
            continue

        # Stop at Notes section
        if stripped == 'Notes' or stripped == 'Notes.':
            break

        # Roman numeral line with period
        if re.match(r'^[IVXLC]+\.\s*$', stripped):
            if current_number is not None and current_body:
                title = f'Rubaiyat {current_number} ({edition})'
                poem = make_poem(title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)

            current_number = stripped.rstrip('.')
            current_body = []
            i += 1
            continue

        if current_number is not None:
            current_body.append(lines[i])

        i += 1

    if current_number is not None and current_body:
        title = f'Rubaiyat {current_number} ({edition})'
        poem = make_poem(title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_kipling(text, pg_id, author, source_title, category):
    """Parse Kipling: ALL CAPS titles in TOC format, then full poems."""
    lines = text.split('\n')
    poems = []

    # Kipling has a long TOC with first-line previews, then the actual poems.
    # Find where actual poems start (after TOC + section header repetition)

    # Look for the actual poem section start
    i = 0
    for j, line in enumerate(lines):
        stripped = line.strip()
        if stripped == 'BARRACK-ROOM BALLADS AND OTHER VERSES' and j > 50:
            i = j
            break
        # Alternative: first "TO WOLCOTT BALESTIER" after TOC
        if stripped == 'TO WOLCOTT BALESTIER' and j > 200:
            i = j
            break

    current_title = None
    current_body = []

    # Section headers to skip
    section_headers = {
        'BARRACK-ROOM BALLADS AND OTHER VERSES',
        'BARRACK-ROOM BALLADS', 'OTHER VERSES',
        'THE SEVEN SEAS', 'BALLADS',
        'THE FIVE NATIONS', 'SERVICE SONGS',
        'DEPARTMENTAL DITTIES', 'DEDICATION',
        'GENERAL SUMMARY', 'CHAPTER HEADINGS',
    }

    while i < len(lines):
        stripped = lines[i].strip()

        # Year headers like "1889-1891"
        if re.match(r'^\d{4}[-–]\d{4}\s*$', stripped):
            i += 1
            continue

        # Section headers
        if stripped in section_headers:
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
                current_title = None
                current_body = []
            i += 1
            continue

        # Poem title: ALL CAPS or quoted ALL CAPS
        title_stripped = stripped.strip('"\'')
        if (stripped and len(stripped) < 80
                and (is_all_caps_title(lines[i]) or
                     (title_stripped and is_all_caps_title('  ' + title_stripped + '  '.replace('"', '').replace("'", ""))))
                and is_title_line(lines[i])):
            # Check preceded by blank lines
            if not lines[i-1].strip() if i > 0 else True:
                if current_title and current_body:
                    poem = make_poem(current_title, current_body, author,
                                     source_title, pg_id, category)
                    if poem:
                        poems.append(poem)
                current_title = stripped.strip('"')
                current_body = []
                i += 1
                continue

        # Also handle Title Case titles for sub-poems (e.g. "The Coastwise Lights")
        if (stripped and not lines[i].startswith('  ') and len(stripped) < 60
                and re.match(r'^[A-Z][a-zA-Z\s\'\-]+$', stripped)
                and i > 0 and not lines[i-1].strip()):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip().startswith(' '):
                if current_title and current_body:
                    poem = make_poem(current_title, current_body, author,
                                     source_title, pg_id, category)
                    if poem:
                        poems.append(poem)
                current_title = stripped
                current_body = []
                i += 1
                continue

        if current_title:
            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_sappho(text, pg_id, author, source_title, category):
    """Parse Sappho: section headers (ALL CAPS), Title Case poem titles."""
    lines = text.split('\n')
    poems = []

    # Find start: "SAPPHICS" section
    i = 0
    for j, line in enumerate(lines):
        if line.strip() == 'SAPPHICS':
            i = j + 1
            break

    # Section headers
    sections = {'SAPPHICS', 'LYRICS', 'EPITHALAMIA', 'FRAGMENTS', 'ODE TO APHRODITE',
                'HYMENAIOS', 'EPIGRAMS'}

    current_title = None
    current_body = []

    while i < len(lines):
        stripped = lines[i].strip()

        # Skip section headers and [Illustration] lines
        if stripped in sections:
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
                current_title = None
                current_body = []
            i += 1
            continue

        if stripped.startswith('[Illustration'):
            i += 1
            continue

        # Poem titles: ALL CAPS short lines preceded by blank
        if (stripped and is_all_caps_title(lines[i]) and is_title_line(lines[i])
                and len(stripped) < 60
                and (i == 0 or not lines[i-1].strip())):
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
            current_title = stripped
            current_body = []
            i += 1
            continue

        if current_title:
            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_rossetti(text, pg_id, author, source_title, category):
    """Parse Rossetti: Title Case titles, body with possible line numbers."""
    lines = text.split('\n')
    poems = []

    # Find where poems actually start (after TOC)
    i = 0
    # Look for the section marker that precedes the first poem
    for j, line in enumerate(lines):
        stripped = line.strip()
        # Find "GOBLIN MARKET, AND OTHER POEMS, 1862" repeated after TOC
        if re.match(r'^GOBLIN MARKET.*1862\s*$', stripped) and j > 100:
            i = j + 1
            break
        # For pg19188, look for different markers
        if stripped == 'POEMS' and j > 50 and source_title != 'Goblin Market, The Prince\'s Progress, and Other Poems':
            i = j + 1
            break

    # Section headers to skip
    section_patterns = [
        r"^GOBLIN MARKET.*\d{4}$",
        r"^THE PRINCE'S PROGRESS.*\d{4}$",
        r"^MISCELLANEOUS POEMS.*$",
        r"^DEVOTIONAL PIECES$",
        r"^POEMS\s*$",
        r"^VERSES\s*$",
    ]

    current_title = None
    current_body = []

    while i < len(lines):
        stripped = lines[i].strip()

        # Skip section headers
        if any(re.match(p, stripped) for p in section_patterns):
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
                current_title = None
                current_body = []
            i += 1
            continue

        # Poem title: ALL CAPS, preceded by blank lines
        if (stripped and is_all_caps_title(lines[i]) and is_title_line(lines[i])
                and i > 0 and not lines[i-1].strip()):
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
            current_title = stripped
            current_body = []
            i += 1
            continue

        if current_title:
            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_generic_caps(text, pg_id, author, source_title, category):
    """Generic parser for collections with ALL CAPS titles.
    Works for: Burns, Tennyson, Poe, Coleridge, Marvell, Donne, Keats, Wordsworth."""
    lines = text.split('\n')
    poems = []

    # Find past front matter: look for CONTENTS then skip past it
    contents_end = 0
    found_contents = False
    for j, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^CONTENTS', stripped, re.IGNORECASE):
            found_contents = True
            continue
        if found_contents and stripped and not re.search(r'\d+\s*$', stripped.replace('.', '')):
            # Non-TOC line after contents — might be start of poems
            if is_all_caps_title(lines[j]) and is_title_line(lines[j]):
                contents_end = j
                break

    # If no contents found, skip known front matter patterns
    if not found_contents:
        for j, line in enumerate(lines):
            stripped = line.strip()
            if (j > 20 and stripped and is_all_caps_title(lines[j])
                    and is_title_line(lines[j]) and len(stripped) > 3
                    and not lines[j-1].strip() if j > 0 else True):
                contents_end = j
                break

    i = contents_end

    # Track section headers to skip (these group poems, not poem titles themselves)
    # Heuristic: if a line is ALL CAPS and the very next content is another ALL CAPS title,
    # the first one is probably a section header.

    current_title = None
    current_body = []

    # Known non-poem headers
    skip_headers = {
        'PREFACE', 'INTRODUCTION', 'NOTE', 'NOTES', 'APPENDIX',
        'CONTENTS', 'INDEX', 'GLOSSARY', 'MEMOIR', 'BIOGRAPHY',
        'FOOTNOTES', 'TRANSCRIBER', 'ADVERTISEMENT',
    }

    while i < len(lines):
        stripped = lines[i].strip()

        # Skip [Picture/Illustration] and transcriber notes
        if stripped.startswith(('[Picture:', '[Illustration', '[Transcriber')):
            i += 1
            continue

        # Check for poem title
        if (stripped and is_all_caps_title(lines[i]) and is_title_line(lines[i])
                and len(stripped) > 1):

            # Skip known non-poem headers
            clean_title = re.sub(r'[^A-Z ]', '', stripped).strip()
            if clean_title in skip_headers:
                i += 1
                continue

            # Check preceded by blank line
            if i > 0 and not lines[i-1].strip():
                if current_title and current_body:
                    poem = make_poem(current_title, current_body, author,
                                     source_title, pg_id, category)
                    if poem:
                        poems.append(poem)
                current_title = stripped
                current_body = []
                i += 1
                continue

        if current_title:
            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_wordsworth(text, pg_id, author, source_title, category):
    """Parse Wordsworth: various formats across volumes."""
    # Wordsworth collections use a mix of ALL CAPS titles and footnotes.
    # Use generic caps parser as base, which handles most cases.
    return parse_generic_caps(text, pg_id, author, source_title, category)


def parse_burns(text, pg_id, author, source_title, category):
    """Parse Burns: titles are NOT indented, body is 5-space indented."""
    lines = text.split('\n')
    poems = []

    # Burns format:
    # - Titles: NO leading spaces, Title Case, e.g. "Song—Handsome Nell^1"
    # - Followed by: "     Tune—..." (indented) and "[Footnote...]" blocks
    # - Poem body: 5-space indented verse lines
    # - Year headers like "1771 - 1779" between groups

    # Skip to first year header (past introductory note)
    i = 0
    for j, line in enumerate(lines):
        stripped = line.strip()
        if (re.match(r'^1\d{3}\s*[-–—]\s*1\d{3}\s*$', stripped)
                or re.match(r'^1\d{3}\s*$', stripped)):
            if j > 50:
                i = j + 1
                break

    current_title = None
    current_body = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Year headers
        if (re.match(r'^1\d{3}\s*[-–—]?\s*(1\d{3})?\s*$', stripped)
                and not line.startswith(' ')):
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
                current_title = None
                current_body = []
            i += 1
            continue

        # Title detection: NOT indented, preceded by blank line, starts with uppercase
        if (stripped and not line.startswith(' ')
                and len(stripped) < 120
                and re.match(r'^[A-Z]', stripped)
                and i > 0 and not lines[i-1].strip()):
            # Skip known non-titles
            if stripped.startswith(('Tune', '[Footnote', 'Choir')):
                i += 1
                continue
            # This is a title line
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
            # Clean footnote markers from title
            current_title = re.sub(r'\^?\d+$', '', stripped).strip()
            current_body = []
            i += 1
            continue

        if current_title:
            # Skip Tune lines (indented)
            if stripped.startswith(('Tune', 'Choir.')):
                i += 1
                continue
            # Skip [Footnote...] blocks
            if stripped.startswith('[Footnote'):
                while i < len(lines):
                    if ']' in lines[i]:
                        break
                    i += 1
                i += 1
                continue
            current_body.append(line)

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_tennyson(text, pg_id, author, source_title, category):
    """Parse Tennyson Early Poems: complex editorial apparatus.
    Format: Title, subtitle, editorial notes (prose), numbered stanzas, footnotes.
    We extract only the verse stanzas."""
    lines = text.split('\n')
    poems = []

    # Find "Early Poems" section (second occurrence — first is in TOC)
    i = 0
    found_count = 0
    for j, line in enumerate(lines):
        if line.strip() == 'Early Poems':
            found_count += 1
            if found_count == 2 or j > 500:
                i = j + 1
                break

    # Strategy: identify poem titles, then for each poem extract only the
    # verse lines (skip editorial prose and footnotes).
    # Poem titles are Title Case on their own line after 2+ blank lines.
    # Verse lines are indented or short poetic lines.
    # Editorial prose is long unindented sentences with periods.
    # Footnotes start with [N] pattern.

    current_title = None
    current_body = []

    stop_markers = {'Appendix—Suppressed Poems', 'Bibliography of the _Poems_ of 1842'}

    while i < len(lines):
        stripped = lines[i].strip()

        if stripped in stop_markers:
            break

        # Poem title: Title Case, preceded by 2+ blank lines, not a footnote/prose
        if (stripped and len(stripped) < 80
                and not stripped.startswith(('[', '(', '_', ' '))
                and not re.match(r'^\d+$', stripped)  # Not a stanza number
                and re.match(r'^[A-Z"]', stripped)):
            # Count preceding blank lines
            blank_before = 0
            for k in range(i-1, max(i-5, -1), -1):
                if k < 0 or not lines[k].strip():
                    blank_before += 1
                else:
                    break
            if blank_before >= 2:
                # Not a prose continuation (check it's short and title-like)
                if len(stripped) < 60 and '.' not in stripped[:-1]:
                    if current_title and current_body:
                        poem = make_poem(current_title, current_body, author,
                                         source_title, pg_id, category)
                        if poem:
                            poems.append(poem)
                    current_title = stripped
                    current_body = []
                    i += 1
                    continue

        if current_title:
            # Skip editorial prose, footnotes, and metadata
            # Footnotes: lines starting with [N]
            if re.match(r'^\s*\[\d+\]', stripped):
                i += 1
                continue
            # Subtitles and publication dates
            if re.match(r'^(a |First published|In \d{4}|MARCH,|This (stanza|poem)|With this cf)', stripped):
                i += 1
                continue
            # Long prose lines (editorial commentary)
            if (len(stripped) > 80 and not lines[i].startswith(' ')
                    and stripped.count(' ') > 10):
                i += 1
                continue
            # Stanza numbers alone on a line
            if re.match(r'^\d+$', stripped):
                i += 1
                continue
            # Skip "Published" or "Written" notes
            if stripped.startswith(('Published', 'Written', 'Reprinted', 'Omitted')):
                i += 1
                continue

            current_body.append(lines[i])

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


def parse_whitman(text, pg_id, author, source_title, category):
    """Parse Whitman's Leaves of Grass: Title Case titles, indented body."""
    lines = text.split('\n')
    poems = []

    # Whitman format: titles are NOT indented, body lines start with 2+ spaces
    # Book headers: "BOOK I.  INSCRIPTIONS" etc. — ALL CAPS with BOOK prefix
    # Section headers: ALL CAPS group names
    # Poem titles: Title Case, not indented, short

    # Skip front matter (epigraph)
    i = 0
    for j, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'^BOOK [IVX]+\.', stripped) or stripped == "One's-Self I Sing":
            i = j
            break

    current_title = None
    current_body = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Book headers like "BOOK I.  INSCRIPTIONS" — skip
        if re.match(r'^BOOK [IVXLC]+\.', stripped):
            i += 1
            continue

        # Section headers in ALL CAPS — skip but save current poem
        if (stripped and is_all_caps_title(line) and len(stripped) > 3
                and not stripped.startswith('[')):
            if current_title and current_body:
                poem = make_poem(current_title, current_body, author,
                                 source_title, pg_id, category)
                if poem:
                    poems.append(poem)
                current_title = None
                current_body = []
            i += 1
            continue

        # Poem title: NOT indented (no leading spaces), preceded by 2+ blank lines
        # and followed by blank line then indented body
        if (stripped and not line.startswith(' ') and len(stripped) < 80
                and re.match(r'^[A-Z"\[\(]', stripped)):
            # Check preceded by at least 2 blank lines
            blank_before = 0
            for k in range(i-1, max(i-5, 0), -1):
                if not lines[k].strip():
                    blank_before += 1
                else:
                    break
            if blank_before >= 2:
                # Check next non-blank line is indented (body text)
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and lines[j].startswith('  '):
                    if current_title and current_body:
                        poem = make_poem(current_title, current_body, author,
                                         source_title, pg_id, category)
                        if poem:
                            poems.append(poem)
                    current_title = stripped
                    current_body = []
                    i += 1
                    continue

        if current_title:
            current_body.append(line)

        i += 1

    if current_title and current_body:
        poem = make_poem(current_title, current_body, author,
                         source_title, pg_id, category)
        if poem:
            poems.append(poem)

    return poems


# ============================================================================
# Dispatch and main
# ============================================================================

# Map pg_id to parser function
PARSERS = {
    # Frost
    3021: parse_frost,
    3026: parse_frost,
    # Yeats
    38877: parse_yeats_poems,  # Large "Poems" volume with plays
    36865: parse_yeats,
    30488: parse_yeats,
    30652: parse_yeats,
    # Hardy
    3167: parse_hardy,
    3168: parse_hardy,
    # Wilde
    1057: parse_wilde,
    1031: parse_wilde,
    # Kipling
    323: parse_kipling,
    # Sappho
    42166: parse_sappho,
    # Dickinson
    12242: parse_dickinson,
    # EBB Sonnets
    2002: parse_sonnets_numbered,
    # Blake
    1934: parse_blake,
    # Rossetti
    16950: parse_rossetti,
    19188: parse_rossetti,
    # Burns
    1279: parse_burns,
    # Tennyson
    8601: parse_tennyson,
    # Poe
    10031: parse_generic_caps,
    # Coleridge
    8208: parse_generic_caps,
    11101: parse_generic_caps,
    # Marvell — pg26288 is a bad download (HTML 404), skip via SKIP_IDS
    # Donne
    48688: parse_generic_caps,
    48772: parse_generic_caps,
    # Keats
    23684: parse_generic_caps,
    8209: parse_generic_caps,
    2490: parse_generic_caps,
    # Wordsworth
    10219: parse_wordsworth,
    9622: parse_generic_caps,
    8774: parse_generic_caps,
    8824: parse_generic_caps,
    # Whitman
    1322: parse_whitman,
    # Rubaiyat (special: numbered quatrains with periods)
    246: parse_rubaiyat,
    # Shakespeare Sonnets
    1041: parse_sonnets_numbered,
}


def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)


def load_poetrydb():
    """Load existing PoetryDB poems for deduplication."""
    try:
        with open(POETRYDB) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def fuzzy_match(s1, s2, threshold=0.85):
    """Check if two strings are similar enough to be duplicates."""
    s1 = s1.lower().strip()
    s2 = s2.lower().strip()
    if s1 == s2:
        return True
    return SequenceMatcher(None, s1, s2).ratio() >= threshold


def deduplicate(poems, existing_poems):
    """Remove poems that already exist in PoetryDB."""
    # Build lookup: (normalized_author, normalized_title) -> True
    existing = set()
    for p in existing_poems:
        author = p['author'].lower().strip()
        title = p['title'].lower().strip()
        existing.add((author, title))

    deduped = []
    dupes = 0
    for poem in poems:
        author = poem['author'].lower().strip()
        title = poem['title'].lower().strip()

        # Exact match
        if (author, title) in existing:
            dupes += 1
            continue

        # Fuzzy match
        is_dupe = False
        for ea, et in existing:
            if fuzzy_match(author, ea) and fuzzy_match(title, et):
                is_dupe = True
                break

        if is_dupe:
            dupes += 1
        else:
            deduped.append(poem)

    return deduped, dupes


def main():
    manifest = load_manifest()
    existing_poems = load_poetrydb()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_poems = []
    stats = []

    for entry in manifest:
        pg_id = entry['id']

        if pg_id in SKIP_IDS:
            continue

        if pg_id not in PARSERS:
            print(f"  SKIP pg{pg_id} ({entry['title']}) — no parser assigned")
            continue

        parser = PARSERS[pg_id]
        text = read_gutenberg(pg_id)
        author = entry['author']
        source_title = entry['title']
        category = entry['category']

        poems = parser(text, pg_id, author, source_title, category)

        # Filter out empty/tiny poems (less than 2 non-blank lines)
        poems = [p for p in poems if int(p['linecount']) >= 2]

        # Save per-collection JSON
        output_path = os.path.join(OUTPUT_DIR, f'pg{pg_id}.json')
        with open(output_path, 'w') as f:
            json.dump(poems, f, indent=2)

        all_poems.extend(poems)
        stats.append({
            'pg_id': pg_id,
            'title': source_title,
            'author': author,
            'poems_found': len(poems),
        })
        print(f"  pg{pg_id}: {len(poems):3d} poems — {source_title} ({author})")

    # Deduplicate against PoetryDB
    deduped, dupe_count = deduplicate(all_poems, existing_poems)

    # Flag poems over 5 minutes
    long_poems = [p for p in deduped if p['reading_time_minutes'] > 5]
    short_poems = [p for p in deduped if p['reading_time_minutes'] <= 5]

    # Save combined output
    combined_path = os.path.join(OUTPUT_DIR, 'all_parsed.json')
    with open(combined_path, 'w') as f:
        json.dump(deduped, f, indent=2)

    # Summary
    print(f"\n{'='*60}")
    print(f"PARSING COMPLETE")
    print(f"{'='*60}")
    print(f"Collections parsed: {len(stats)}")
    print(f"Total poems extracted: {len(all_poems)}")
    print(f"Duplicates removed (in PoetryDB): {dupe_count}")
    print(f"Unique poems: {len(deduped)}")
    print(f"  Under 5 min: {len(short_poems)}")
    print(f"  Over 5 min: {len(long_poems)}")
    print(f"\nOutput: {OUTPUT_DIR}/")
    print(f"  Per-collection: pg<id>.json")
    print(f"  Combined: all_parsed.json ({len(deduped)} poems)")

    # Per-author summary
    author_counts = {}
    for p in deduped:
        author_counts[p['author']] = author_counts.get(p['author'], 0) + 1
    print(f"\nPer-author breakdown:")
    for author, count in sorted(author_counts.items(), key=lambda x: -x[1]):
        print(f"  {author}: {count}")

    return deduped


if __name__ == '__main__':
    main()
