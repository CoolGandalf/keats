"""
Extract commonly anthologized excerpts from epic/long-form Gutenberg texts.
Outputs a JSON catalog of excerpts suitable for poem-a-day delivery.
"""
import json
import re
import os

BASE = os.path.join(os.path.dirname(__file__), '..', 'data', 'gutenberg')
OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'excerpts.json')


def read_gutenberg(pg_id):
    path = os.path.join(BASE, f'pg{pg_id}.txt')
    with open(path, encoding='utf-8') as f:
        return f.readlines()


def extract_lines(lines, start_marker, end_marker=None, start_offset=0, max_lines=None, end_offset=0):
    """Extract lines between markers. Returns (text, start_idx, end_idx)."""
    start_idx = None
    for i, line in enumerate(lines):
        if start_marker in line and start_idx is None:
            start_idx = i + start_offset
            break
    if start_idx is None:
        return None, None, None

    if end_marker:
        end_idx = None
        for i, line in enumerate(lines[start_idx + 1:], start_idx + 1):
            if end_marker in line:
                end_idx = i + end_offset
                break
        if end_idx is None:
            end_idx = min(start_idx + (max_lines or 300), len(lines))
    elif max_lines:
        end_idx = min(start_idx + max_lines, len(lines))
    else:
        end_idx = len(lines)

    text = ''.join(lines[start_idx:end_idx]).strip()
    return text, start_idx, end_idx


def extract_between_cantos(lines, canto_pattern, next_pattern):
    """Extract text between two canto headers."""
    start = None
    end = None
    for i, line in enumerate(lines):
        if canto_pattern in line.strip() and start is None:
            start = i
        elif next_pattern in line.strip() and start is not None:
            end = i
            break
    if start is None:
        return None
    if end is None:
        end = min(start + 300, len(lines))
    # Skip header lines, get poem text
    text_start = start
    for i in range(start, min(start + 5, len(lines))):
        if lines[i].strip() == '':
            text_start = i + 1
    return ''.join(lines[text_start:end]).strip()


def clean_gutenberg_text(text):
    """Remove Gutenberg headers/footers and clean whitespace."""
    # Remove excessive blank lines
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    return text.strip()


def count_verse_lines(text):
    """Count non-blank lines."""
    return len([l for l in text.split('\n') if l.strip()])


excerpts = []


# === PARADISE LOST (pg26) ===
pl = read_gutenberg(26)

# Book I opening - Invocation + Satan's early speeches (~300 lines)
pl_book1_start = None
for i, line in enumerate(pl):
    if "Of Man" in line and "first" in line and "disobedience" in line:
        pl_book1_start = i
        break
if pl_book1_start is None:
    # Fallback: find Book I marker and go 2 lines after
    for i, line in enumerate(pl):
        if line.strip() == 'Book I' and i < 200:
            pl_book1_start = i + 2
            break
excerpts.append({
    "title": "Paradise Lost: Book I — The Invocation and Satan's Speech",
    "author": "John Milton",
    "source": "Paradise Lost, Book I (opening ~300 lines)",
    "source_id": 26,
    "category": "epic_excerpt",
    "note": "The most excerpted passage from Paradise Lost. Contains the invocation, Satan waking in Hell, and his defiant speeches including 'The mind is its own place' and 'Better to reign in Hell than serve in Heaven.'",
    "text": clean_gutenberg_text(''.join(pl[pl_book1_start:pl_book1_start + 200])),
    "verse_lines": count_verse_lines(''.join(pl[pl_book1_start:pl_book1_start + 200]))
})

# Book IV - Satan's Soliloquy on seeing Eden
text, _, _ = extract_lines(pl, "Book IV", "Book V", max_lines=120, start_offset=2)
if text:
    # Try to find just the soliloquy
    for i, line in enumerate(pl):
        if "O thou that with surpassing glory" in line or "horror and doubt distract" in line.lower():
            sol_start = i
            sol_text = ''.join(pl[sol_start:sol_start+90]).strip()
            excerpts.append({
                "title": "Paradise Lost: Satan's Soliloquy on Mount Niphates",
                "author": "John Milton",
                "source": "Paradise Lost, Book IV, lines 32-113",
                "source_id": 26,
                "category": "epic_excerpt",
                "note": "Satan's tortured self-examination upon seeing Eden. Psychologically complex; often compared to Hamlet's soliloquies.",
                "text": clean_gutenberg_text(sol_text),
                "verse_lines": count_verse_lines(sol_text)
            })
            break

# Book IX - The Temptation scene (~300 lines from the core temptation)
# Find "Serpent, we might have spar'd" or Eve's temptation
for i, line in enumerate(pl):
    if "Book IX" in line:
        book9_start = i
        break
# Extract just the opening of Book IX (~300 lines including the temptation setup)
text = ''.join(pl[book9_start:book9_start + 200]).strip()
excerpts.append({
    "title": "Paradise Lost: Book IX — The Temptation and Fall (opening)",
    "author": "John Milton",
    "source": "Paradise Lost, Book IX (opening ~300 lines)",
    "source_id": 26,
    "category": "epic_excerpt",
    "note": "The dramatic climax of the poem. Satan enters the serpent and prepares to tempt Eve.",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})

# Book XII ending - The Expulsion
for i, line in enumerate(pl):
    if "Book XII" in line:
        book12_start = i
        break
# Get the last ~40 lines of the poem (before Gutenberg footer)
poem_end = len(pl)
for i in range(len(pl) - 1, 0, -1):
    if '*** END' in pl[i] or 'End of' in pl[i] or 'Project Gutenberg' in pl[i]:
        poem_end = i
        break
last_lines = ''.join(pl[max(poem_end-45, book12_start):poem_end]).strip()
excerpts.append({
    "title": "Paradise Lost: The Expulsion from Eden",
    "author": "John Milton",
    "source": "Paradise Lost, Book XII (closing lines)",
    "source_id": 26,
    "category": "epic_excerpt",
    "note": "'The world was all before them, where to choose / Their place of rest, and Providence their guide.' One of the most famous closing passages in English poetry.",
    "text": clean_gutenberg_text(last_lines),
    "verse_lines": count_verse_lines(last_lines)
})


# === LEAVES OF GRASS (pg1322) ===
lg = read_gutenberg(1322)

# Helper to find poem boundaries in Leaves of Grass
def extract_whitman_poem(lines, title_text, max_lines=300):
    start = None
    for i, line in enumerate(lines):
        if title_text in line.strip() and len(line.strip()) < len(title_text) + 10:
            start = i
            break
    if start is None:
        return None
    # Find next poem (line that looks like a title after blank lines)
    in_blank = False
    end = min(start + max_lines, len(lines))
    for i in range(start + 2, min(start + max_lines, len(lines))):
        if lines[i].strip() == '':
            in_blank = True
        elif in_blank and lines[i].strip() and not lines[i].startswith(' ') and not lines[i].startswith('\t'):
            # Potential new poem title
            candidate = lines[i].strip()
            if candidate and candidate[0].isupper() and len(candidate) < 80 and not candidate.startswith('('):
                end = i
                break
            in_blank = False
        else:
            in_blank = False
    return ''.join(lines[start:end]).strip()

whitman_poems = [
    ("I Hear America Singing", "Short, iconic celebration of democratic labor. One of Whitman's most widely taught poems."),
    ("O Captain! My Captain!", "Whitman's most popular poem during his lifetime. Elegy for Lincoln, widely memorized."),
    ("A Noiseless Patient Spider", "One of the great short lyrics in English. Perfect metaphor for the soul's reaching outward."),
]

for title, note in whitman_poems:
    text = extract_whitman_poem(lg, title)
    if text:
        excerpts.append({
            "title": title,
            "author": "Walt Whitman",
            "source": "Leaves of Grass",
            "source_id": 1322,
            "category": "extracted_poem",
            "note": note,
            "text": clean_gutenberg_text(text),
            "verse_lines": count_verse_lines(text)
        })

# Song of Myself - extract sections 1-6 and section 52
som_start = None
for i, line in enumerate(lg):
    if 'Song of Myself' in line.strip() and len(line.strip()) < 25:
        som_start = i
        break

if som_start:
    # Find section markers (numbered sections)
    # Whitman's Song of Myself has 52 sections.
    # Keep a short Section 1 entry in the live catalog; the full poem is too long
    # for the app's daily-poem picker, but this puts the 1891–92 text in rotation.
    sect1 = None
    sect2 = None
    sect7 = None
    for i in range(som_start, min(som_start + 2000, len(lg))):
        stripped = lg[i].strip()
        if stripped == '1' and sect1 is None:
            sect1 = i
        elif stripped == '2' and sect2 is None:
            sect2 = i
        elif stripped == '7':
            sect7 = i
            break

    if sect1 and sect2:
        text = "Song of Myself (Section 1)\n\n" + ''.join(lg[sect1:sect2]).strip()
        excerpts.append({
            "title": "Song of Myself (Section 1)",
            "author": "Walt Whitman",
            "source": "Leaves of Grass — Song of Myself",
            "source_id": 1322,
            "category": "epic_excerpt",
            "note": "The opening section of Whitman's 1891–92 'Death-Bed' edition text. Added from the Poetry Foundation request; the full poem is deliberately not in daily rotation because it is 1,600+ lines.",
            "text": clean_gutenberg_text(text),
            "verse_lines": count_verse_lines(text),
            "reading_time_minutes": 0.6
        })

    # Longer reference excerpt: sections 1-6, including the famous grass passage.
    if sect7:
        text = ''.join(lg[som_start:sect7]).strip()
        excerpts.append({
            "title": "Song of Myself (Sections 1-6)",
            "author": "Walt Whitman",
            "source": "Leaves of Grass — Song of Myself",
            "source_id": 1322,
            "category": "epic_excerpt",
            "note": "The opening of Whitman's masterpiece. 'I celebrate myself, and sing myself.' Includes the famous 'What is the grass?' passage. The founding document of American free verse.",
            "text": clean_gutenberg_text(text),
            "verse_lines": count_verse_lines(text),
            "reading_time_minutes": 6.0
        })

# Crossing Brooklyn Ferry
cbf = extract_whitman_poem(lg, "Crossing Brooklyn Ferry", max_lines=500)
if cbf:
    excerpts.append({
        "title": "Crossing Brooklyn Ferry",
        "author": "Walt Whitman",
        "source": "Leaves of Grass",
        "source_id": 1322,
        "category": "extracted_poem",
        "note": "Whitman's most formally perfect poem. A meditation on time, community, and connection across generations.",
        "text": clean_gutenberg_text(cbf),
        "verse_lines": count_verse_lines(cbf)
    })


# === DIVINE COMEDY - Longfellow (pg1004) ===
dc = read_gutenberg(1004)

# Map cantos
dc_cantos = []
for i, line in enumerate(dc):
    m = re.match(r'^(Inferno|Purgatorio|Paradiso): Canto ([IVXLC]+)\s*$', line.strip())
    if m:
        dc_cantos.append((i, m.group(1), m.group(2)))

def get_dc_canto(section, number):
    for idx, (line_no, sec, num) in enumerate(dc_cantos):
        if sec == section and num == number:
            next_line = dc_cantos[idx + 1][0] if idx + 1 < len(dc_cantos) else len(dc)
            return ''.join(dc[line_no:next_line]).strip()
    return None

dc_excerpts = [
    ("Inferno", "I", "Inferno, Canto I: The Dark Wood", "One of the most famous openings in all literature. 'Midway upon the journey of our life / I found myself within a forest dark.'"),
    ("Inferno", "III", "Inferno, Canto III: The Gate of Hell", "'Abandon all hope, ye who enter here.' The vestibule of the uncommitted and Charon's ferry."),
    ("Inferno", "V", "Inferno, Canto V: Paolo and Francesca", "The circle of the lustful. The most emotionally powerful episode in the Inferno. 'That day we read no further.'"),
    ("Inferno", "XXVI", "Inferno, Canto XXVI: Ulysses", "Ulysses describes his final voyage beyond the Pillars of Hercules. Inspired Tennyson's 'Ulysses.'"),
    ("Inferno", "XXXIII", "Inferno, Canto XXXIII: Ugolino", "Count Ugolino gnaws Archbishop Ruggieri's skull; tells of starving to death with his children. The most horrifying episode in the Inferno."),
    ("Inferno", "XXXIV", "Inferno, Canto XXXIV: Satan", "The three-headed Satan at the center of Hell; the climb out. The structural climax of the Inferno."),
]

for section, number, title, note in dc_excerpts:
    text = get_dc_canto(section, number)
    if text:
        excerpts.append({
            "title": title,
            "author": "Dante Alighieri (tr. Henry Wadsworth Longfellow)",
            "source": f"The Divine Comedy — {section}, Canto {number}",
            "source_id": 1004,
            "category": "epic_excerpt",
            "note": note,
            "text": clean_gutenberg_text(text),
            "verse_lines": count_verse_lines(text)
        })

# Paradiso XXXIII - just extract ~145 lines (a single canto, trimmed)
para33 = get_dc_canto("Paradiso", "XXXIII")
if para33:
    # Trim to actual canto content (not the Gutenberg footer)
    para33_lines = para33.split('\n')
    trimmed = []
    for line in para33_lines:
        if '*** END' in line or 'Project Gutenberg' in line:
            break
        trimmed.append(line)
    para33_text = '\n'.join(trimmed).strip()
    excerpts.append({
        "title": "Paradiso, Canto XXXIII: The Final Vision",
        "author": "Dante Alighieri (tr. Henry Wadsworth Longfellow)",
        "source": "The Divine Comedy — Paradiso, Canto XXXIII",
        "source_id": 1004,
        "category": "epic_excerpt",
        "note": "The vision of God and 'the Love that moves the sun and the other stars.' The culmination of the entire Comedy.",
        "text": clean_gutenberg_text(para33_text),
        "verse_lines": count_verse_lines(para33_text)
    })


# === DON JUAN (pg21700) ===
dj = read_gutenberg(21700)

# The Isles of Greece
for i, line in enumerate(dj):
    if "The isles of Greece" in line:
        isles_start = i
        break
# Find end (back to narrative)
isles_end = isles_start + 200
for i in range(isles_start + 5, isles_start + 200):
    if dj[i].strip() == '' and i + 1 < len(dj):
        next_line = dj[i+1].strip()
        if next_line and ('Thus' in next_line or 'said' in next_line.lower() or next_line[0].isdigit()):
            isles_end = i
            break
text = ''.join(dj[isles_start:isles_end]).strip()
excerpts.append({
    "title": "The Isles of Greece",
    "author": "Lord Byron",
    "source": "Don Juan, Canto III",
    "source_id": 21700,
    "category": "epic_excerpt",
    "note": "A Greek poet sings of Greece's lost glory at Haidée's feast. The most famous lyric passage in Don Juan, frequently anthologized as a standalone poem.",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})


# === CHILDE HAROLD'S PILGRIMAGE (pg5131) ===
ch = read_gutenberg(5131)

# Apostrophe to the Ocean - search for "Roll on"
for i, line in enumerate(ch):
    if "Roll on, thou deep" in line:
        ocean_start = i - 2  # include stanza start
        break
# Find ~7 stanzas worth
text = ''.join(ch[ocean_start:ocean_start + 80]).strip()
excerpts.append({
    "title": "Apostrophe to the Ocean",
    "author": "Lord Byron",
    "source": "Childe Harold's Pilgrimage, Canto IV, stanzas 178-184",
    "source_id": 5131,
    "category": "epic_excerpt",
    "note": "'Roll on, thou deep and dark blue Ocean — roll!' The most famous passage in the poem. Nearly universal in Romantic poetry anthologies.",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})

# Eve of Waterloo
for i, line in enumerate(ch):
    if "There was a sound of revelry" in line:
        waterloo_start = i - 2
        break
text = ''.join(ch[waterloo_start:waterloo_start + 90]).strip()
excerpts.append({
    "title": "The Eve of Waterloo",
    "author": "Lord Byron",
    "source": "Childe Harold's Pilgrimage, Canto III, stanzas 21-28",
    "source_id": 5131,
    "category": "epic_excerpt",
    "note": "The Duchess of Richmond's ball on the eve of battle. One of the most famous passages in Romantic poetry — the abrupt shift from revelry to war.",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})


# === ENDYMION (pg24280) ===
end = read_gutenberg(24280)

# "A thing of beauty" opening
for i, line in enumerate(end):
    if "A thing of beauty" in line:
        beauty_start = i
        break
text = ''.join(end[beauty_start:beauty_start + 35]).strip()
excerpts.append({
    "title": "A Thing of Beauty (from Endymion)",
    "author": "John Keats",
    "source": "Endymion, Book I, opening lines",
    "source_id": 24280,
    "category": "epic_excerpt",
    "note": "'A thing of beauty is a joy for ever.' The opening line is proverbial. Almost universally the excerpt chosen from Endymion.",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})


# === CANTERBURY TALES (pg2383) ===
ct = read_gutenberg(2383)

# General Prologue opening - find "Whan that Aprille" or similar
for i, line in enumerate(ct):
    if 'april' in line.lower() and ('whan' in line.lower() or 'when' in line.lower() or 'shour' in line.lower()):
        prologue_start = i
        print(f"CT prologue found at line {i}: {line.rstrip()}")
        break


# === AENEID (pg228) ===
ae = read_gutenberg(228)

# "Arms, and the man" opening
for i, line in enumerate(ae):
    if 'Arms, and the man' in line or 'arms and the man' in line.lower():
        arms_start = i
        break
text = ''.join(ae[arms_start:arms_start + 50]).strip()
excerpts.append({
    "title": "The Aeneid: Opening Invocation",
    "author": "Virgil (tr. John Dryden)",
    "source": "The Aeneid, Book I (opening)",
    "source_id": 228,
    "category": "epic_excerpt",
    "note": "'Arms, and the man I sing.' One of the most recognized opening lines in Western literature.",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})

# Book IV - Dido - just the death scene (~150 lines from end of Book IV)
ae_book5_start = None
for i, line in enumerate(ae):
    if 'BOOK V' in line and i > 3400:
        ae_book5_start = i
        break
if ae_book5_start:
    dido_text = ''.join(ae[ae_book5_start - 180:ae_book5_start]).strip()
    excerpts.append({
        "title": "The Aeneid: The Death of Dido",
        "author": "Virgil (tr. John Dryden)",
        "source": "The Aeneid, Book IV (closing ~150 lines)",
        "source_id": 228,
        "category": "epic_excerpt",
        "note": "Dido's curse, self-immolation, and death. The emotional climax of one of the great tragic love stories in Western literature.",
        "text": clean_gutenberg_text(dido_text),
        "verse_lines": count_verse_lines(dido_text)
    })


# === METAMORPHOSES (pg28621) ===
met = read_gutenberg(28621)

# Search for key stories
ovid_stories = [
    ("Apollo and Daphne", "apollo", "daphne", "The archetypal metamorphosis story. Apollo pursues Daphne; she transforms into a laurel tree."),
    ("Narcissus and Echo", "narcissus", "echo", "The origin of 'narcissism.' Narcissus falls in love with his own reflection."),
    ("Pyramus and Thisbe", "pyramus", "thisbe", "Star-crossed lovers; the source for Shakespeare's Romeo and Juliet."),
    ("Daedalus and Icarus", "daedalus", "icarus", "The flight from Crete; Icarus falls into the sea. One of the most iconic cautionary myths."),
    ("Orpheus and Eurydice", "orpheus", "eurydice", "The foundational myth of poetry and loss."),
]

for story_title, kw1, kw2, note in ovid_stories:
    # Find a line containing both keywords, or first occurrence of the rarer keyword
    best_start = None
    for i, line in enumerate(met):
        ll = line.lower()
        if kw1 in ll and kw2 in ll:
            best_start = max(0, i - 5)
            break
    # Fallback: find first occurrence of rarer keyword (kw2)
    if best_start is None:
        for i, line in enumerate(met):
            if kw2 in line.lower() and i > 100:
                best_start = max(0, i - 5)
                break
    if best_start:
        # Extract ~120 lines (a readable excerpt)
        text = ''.join(met[best_start:best_start + 130]).strip()
        excerpts.append({
            "title": f"Metamorphoses: {story_title}",
            "author": "Ovid (tr. J.J. Howard)",
            "source": f"Metamorphoses — {story_title}",
            "source_id": 28621,
            "category": "epic_excerpt",
            "note": note,
            "text": clean_gutenberg_text(text),
            "verse_lines": count_verse_lines(text)
        })


# === IDYLLS OF THE KING (pg610) ===
idylls = read_gutenberg(610)

# The Passing of Arthur
# Find the actual poem section (not the table of contents entry)
passing_start = None
for i, line in enumerate(idylls):
    if 'The Passing of Arthur' in line.strip() and i > 1000:
        passing_start = i
        break
# Find the end - "To the Queen" epilogue starts after the poem
passing_end = len(idylls)
for i in range(passing_start + 50, len(idylls)):
    if 'To the Queen' in idylls[i]:
        passing_end = i
        break

text = ''.join(idylls[passing_start:passing_end]).strip()
excerpts.append({
    "title": "The Passing of Arthur",
    "author": "Alfred, Lord Tennyson",
    "source": "Idylls of the King",
    "source_id": 610,
    "category": "epic_excerpt",
    "note": "Arthur's final battle, the casting of Excalibur into the mere, the barge bearing Arthur to Avalon. 'The old order changeth, yielding place to new.' The most famous section of the Idylls.",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})


# === ILIAD (pg6130) ===
il = read_gutenberg(6130)

# Opening invocation
for i, line in enumerate(il):
    if "Achilles" in line and ('wrath' in line.lower() or 'rage' in line.lower()):
        iliad_start = i
        break
text = ''.join(il[iliad_start:iliad_start + 60]).strip()
excerpts.append({
    "title": "The Iliad: Invocation — The Wrath of Achilles",
    "author": "Homer (tr. Alexander Pope)",
    "source": "The Iliad, Book I (opening)",
    "source_id": 6130,
    "category": "epic_excerpt",
    "note": "'Achilles' wrath, to Greece the direful spring / Of woes unnumber'd, heavenly goddess, sing!' The iconic opening.",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})


# === ODYSSEY (pg3160) ===
od = read_gutenberg(3160)

# Opening
for i, line in enumerate(od):
    if 'man' in line.lower() and ('muse' in line.lower() or 'tell' in line.lower()) and i < 500:
        od_start = i
        break
text = ''.join(od[od_start:od_start + 50]).strip()
excerpts.append({
    "title": "The Odyssey: Opening Invocation",
    "author": "Homer (tr. Alexander Pope)",
    "source": "The Odyssey, Book I (opening)",
    "source_id": 3160,
    "category": "epic_excerpt",
    "note": "The invocation to the Muse and introduction of 'the man of many wiles.'",
    "text": clean_gutenberg_text(text),
    "verse_lines": count_verse_lines(text)
})


# === FAERIE QUEENE - Cave of Despair (pg70717) ===
fq = read_gutenberg(70717)

for i, line in enumerate(fq):
    if 'Cave of Despaire' in line or 'cave of Despaire' in line or 'DESPAIRE' in line or 'Despair' in line:
        print(f"FQ Despair ref at line {i}: {line.rstrip()}")


# === Write output ===
# Add summary stats
for ex in excerpts:
    ex['verse_lines'] = count_verse_lines(ex['text'])

print(f"\n=== EXCERPT CATALOG ===")
print(f"Total excerpts: {len(excerpts)}")
print(f"\nBy source:")
sources = {}
for ex in excerpts:
    src = ex['source'].split('—')[0].split(',')[0].strip()
    sources[src] = sources.get(src, 0) + 1
for src, count in sorted(sources.items()):
    print(f"  {src}: {count}")

print(f"\nBy length:")
short = [e for e in excerpts if e['verse_lines'] <= 50]
medium = [e for e in excerpts if 50 < e['verse_lines'] <= 150]
long = [e for e in excerpts if e['verse_lines'] > 150]
print(f"  Short (≤50 lines): {len(short)}")
print(f"  Medium (51-150 lines): {len(medium)}")
print(f"  Long (150+ lines): {len(long)}")

print(f"\nAll excerpts:")
for ex in excerpts:
    print(f"  [{ex['verse_lines']:>4} lines] {ex['title']}")

with open(OUTPUT, 'w') as f:
    json.dump(excerpts, f, indent=2, ensure_ascii=False)
print(f"\nWritten to {OUTPUT}")
