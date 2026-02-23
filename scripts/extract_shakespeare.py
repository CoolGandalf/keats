"""
Extract famous Shakespeare speeches/monologues from Gutenberg play texts.
Outputs JSON suitable for merging into the excerpts catalog.
"""
import os, json, re

BASE = os.path.join(os.path.dirname(__file__), '..', 'data', 'gutenberg')
EXCERPTS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'excerpts.json')
WPM = 150


def read_pg(pid):
    with open(os.path.join(BASE, f'pg{pid}.txt'), encoding='utf-8') as f:
        return f.readlines()


def find_line(lines, marker):
    for i, line in enumerate(lines):
        if marker in line:
            return i
    return None


def extract_until(lines, start, stop_markers, max_lines=80):
    """Extract from start until a stop marker or max_lines."""
    result = []
    for i in range(start, min(start + max_lines, len(lines))):
        line = lines[i]
        # Check stop markers (but not in first few lines)
        if i > start + 3:
            for sm in stop_markers:
                if sm in line:
                    return '\n'.join(result).strip()
        result.append(line.rstrip())
    return '\n'.join(result).strip()


def verse_lines(text):
    return len([l for l in text.split('\n') if l.strip()])


def reading_time(text):
    return round(len(text.split()) / WPM, 1)


speeches = []

# === HAMLET (pg1524) ===
hamlet = read_pg(1524)

# To be, or not to be
idx = find_line(hamlet, 'To be, or not to be')
if idx:
    text = extract_until(hamlet, idx, ['Soft you now', 'OPHELIA', 'Nymph, in thy'])
    speeches.append({
        "title": "To Be, or Not to Be",
        "author": "William Shakespeare",
        "source": "Hamlet, Act 3, Scene 1",
        "source_id": 1524,
        "category": "shakespeare_speech",
        "note": "The most famous soliloquy in English literature. Hamlet's meditation on existence, death, and the fear of the unknown."
    } | {"text": text})

# O, that this too too solid flesh
idx = find_line(hamlet, 'too, too solid flesh') or find_line(hamlet, 'too too solid flesh') or find_line(hamlet, 'too too sullied')
if idx:
    text = extract_until(hamlet, idx, ['HORATIO', 'Hail to your', 'Enter Horatio'])
    speeches.append({
        "title": "O, That This Too Too Solid Flesh Would Melt",
        "author": "William Shakespeare",
        "source": "Hamlet, Act 1, Scene 2",
        "source_id": 1524,
        "category": "shakespeare_speech",
        "note": "Hamlet's first soliloquy, expressing despair at his mother's remarriage and the corruption of the world."
    } | {"text": text})

# === AS YOU LIKE IT (pg1523) ===
ayli = read_pg(1523)
idx = find_line(ayli, 'All the world')
if idx:
    text = extract_until(ayli, idx, ['ORLANDO', 'Enter Orlando', 'Dear master'], max_lines=35)
    speeches.append({
        "title": "All the World's a Stage",
        "author": "William Shakespeare",
        "source": "As You Like It, Act 2, Scene 7",
        "source_id": 1523,
        "category": "shakespeare_speech",
        "note": "Jaques' meditation on the seven ages of human life, from infant to old age. One of Shakespeare's most quoted passages."
    } | {"text": text})

# === MACBETH (pg1533) ===
macbeth = read_pg(1533)
# Find "She should have died" or "Tomorrow, and tomorrow"
idx = find_line(macbeth, 'Tomorrow, and tomorrow') or find_line(macbeth, 'Tomorrow and tomorrow')
if idx:
    # Back up to "She should have died" if it's nearby
    for j in range(max(0, idx-5), idx):
        if 'She should have died' in macbeth[j]:
            idx = j
            break
    text = extract_until(macbeth, idx, ['Enter a Messenger', 'Enter', 'MESSENGER', 'Thou com'], max_lines=20)
    speeches.append({
        "title": "Tomorrow, and Tomorrow, and Tomorrow",
        "author": "William Shakespeare",
        "source": "Macbeth, Act 5, Scene 5",
        "source_id": 1533,
        "category": "shakespeare_speech",
        "note": "Macbeth's nihilistic response to Lady Macbeth's death. 'Life's but a walking shadow, a poor player / That struts and frets his hour upon the stage.'"
    } | {"text": text})

# === HENRY V (pg1521) ===
henry = read_pg(1521)

# Once more unto the breach
idx = find_line(henry, 'Once more unto the breach')
if idx:
    text = extract_until(henry, idx, ['Exeunt', 'Alarm', 'Enter'], max_lines=40)
    speeches.append({
        "title": "Once More Unto the Breach",
        "author": "William Shakespeare",
        "source": "Henry V, Act 3, Scene 1",
        "source_id": 1521,
        "category": "shakespeare_speech",
        "note": "Henry V rallying his troops at the siege of Harfleur. A rousing call to martial valor."
    } | {"text": text})

# St. Crispin's Day - search for the specific opening line
idx = find_line(henry, 'This day is call')
if idx:
    text = extract_until(henry, idx, ['Enter Salisbury', 'SALISBURY', 'Enter '], max_lines=40)
    speeches.append({
        "title": "St. Crispin's Day Speech",
        "author": "William Shakespeare",
        "source": "Henry V, Act 4, Scene 3",
        "source_id": 1521,
        "category": "shakespeare_speech",
        "note": "Henry's pre-battle speech before Agincourt. 'We few, we happy few, we band of brothers.' Perhaps the greatest battle speech ever written."
    } | {"text": text})

# === MERCHANT OF VENICE (pg1515) ===
merchant = read_pg(1515)
idx = find_line(merchant, 'quality of mercy')
if idx:
    text = extract_until(merchant, idx, ['SHYLOCK', 'BASSANIO', 'My deeds upon my head'], max_lines=25)
    speeches.append({
        "title": "The Quality of Mercy",
        "author": "William Shakespeare",
        "source": "The Merchant of Venice, Act 4, Scene 1",
        "source_id": 1515,
        "category": "shakespeare_speech",
        "note": "Portia's eloquent argument for mercy. 'It droppeth as the gentle rain from heaven / Upon the place beneath. It is twice blest.'"
    } | {"text": text})

# === JULIUS CAESAR (pg1522) ===
jc = read_pg(1522)
idx = find_line(jc, 'Friends, Romans, countrymen')
if idx:
    # Antony's speech - extract ~50 lines (the core of it)
    text = extract_until(jc, idx, ['ALL.', 'FOURTH CITIZEN', 'We will be satisfied'], max_lines=55)
    speeches.append({
        "title": "Friends, Romans, Countrymen",
        "author": "William Shakespeare",
        "source": "Julius Caesar, Act 3, Scene 2",
        "source_id": 1522,
        "category": "shakespeare_speech",
        "note": "Mark Antony's masterful funeral oration, turning the Roman crowd against Caesar's assassins. One of Shakespeare's greatest political speeches."
    } | {"text": text})

# === RICHARD III (pg2257) ===
r3 = read_pg(2257)
idx = find_line(r3, 'Now is the winter of our discontent')
if idx:
    text = extract_until(r3, idx, ['Enter CLARENCE', 'CLARENCE', 'Brother, good day', 'Enter Clarence'], max_lines=50)
    speeches.append({
        "title": "Now Is the Winter of Our Discontent",
        "author": "William Shakespeare",
        "source": "Richard III, Act 1, Scene 1",
        "source_id": 2257,
        "category": "shakespeare_speech",
        "note": "Richard III's opening soliloquy establishing his villainy. 'I am determined to prove a villain.'"
    } | {"text": text})

# === TWELFTH NIGHT (pg1526) ===
tn = read_pg(1526)
idx = find_line(tn, 'If music be the food of love')
if idx:
    text = extract_until(tn, idx, ['CURIO', 'Will you go hunt', 'Enter VALENTINE'], max_lines=20)
    speeches.append({
        "title": "If Music Be the Food of Love",
        "author": "William Shakespeare",
        "source": "Twelfth Night, Act 1, Scene 1",
        "source_id": 1526,
        "category": "shakespeare_speech",
        "note": "Duke Orsino's opening speech on love and excess. The famous first lines of the play."
    } | {"text": text})

# === THE TEMPEST (pg23042) ===
tempest = read_pg(23042)
idx = find_line(tempest, 'Our revels now are ended')
if idx:
    text = extract_until(tempest, idx, ['Sir, I am vex', 'ARIEL', 'A turn or two'], max_lines=20)
    speeches.append({
        "title": "Our Revels Now Are Ended",
        "author": "William Shakespeare",
        "source": "The Tempest, Act 4, Scene 1",
        "source_id": 23042,
        "category": "shakespeare_speech",
        "note": "Prospero's reflection on the illusory nature of theater and life. Often read as Shakespeare's farewell to the stage. 'We are such stuff as dreams are made on.'"
    } | {"text": text})

# === ROMEO AND JULIET (pg1513) ===
rj = read_pg(1513)
idx = find_line(rj, 'O Romeo, Romeo')
if idx:
    # Combine both parts of Juliet's soliloquy, skipping Romeo's aside
    part1 = []
    part2 = []
    in_part2 = False
    for j in range(idx, min(idx + 30, len(rj))):
        line = rj[j]
        if 'ROMEO' in line.strip() and line.strip().startswith('ROMEO'):
            if not in_part2:
                # Skip Romeo's aside
                continue
            else:
                break  # Romeo speaks again = end of Juliet's speech
        if 'Aside' in line or 'Shall I hear more' in line:
            continue
        if 'JULIET' in line.strip() and line.strip().startswith('JULIET'):
            in_part2 = True
            continue
        if not in_part2:
            if line.strip():
                part1.append(line.rstrip())
        else:
            if line.strip() or part2:
                part2.append(line.rstrip())
    text = '\n'.join(part1 + [''] + part2).strip()
    speeches.append({
        "title": "O Romeo, Romeo! Wherefore Art Thou Romeo?",
        "author": "William Shakespeare",
        "source": "Romeo and Juliet, Act 2, Scene 2",
        "source_id": 1513,
        "category": "shakespeare_speech",
        "note": "Juliet's balcony soliloquy on love and names. 'What's in a name? That which we call a rose / By any other name would smell as sweet.'"
    } | {"text": text})

# === Add reading times and filter ===
print(f"{'Time':>5}  {'Lines':>5}  Title")
print("-" * 70)
kept = []
cut = []
for sp in speeches:
    sp['verse_lines'] = verse_lines(sp['text'])
    sp['reading_time_minutes'] = reading_time(sp['text'])
    status = "OK" if sp['reading_time_minutes'] <= 5.0 else "CUT"
    print(f"{sp['reading_time_minutes']:>4}m  {sp['verse_lines']:>5}  [{status}] {sp['title']}")
    if sp['reading_time_minutes'] <= 5.0:
        kept.append(sp)
    else:
        cut.append(sp)

print(f"\nKeeping: {len(kept)}, Cutting: {len(cut)}")

# Merge into existing excerpts
with open(EXCERPTS_PATH) as f:
    excerpts = json.load(f)

excerpts.extend(kept)

with open(EXCERPTS_PATH, 'w') as f:
    json.dump(excerpts, f, indent=2, ensure_ascii=False)

print(f"Total excerpts now: {len(excerpts)}")
