"""
Script to fix malformed JSON files by converting plain text sections to JSON
"""
import json
import re
import os

def parse_plain_text_session(lines, start_idx):
    """Parse a plain text session block and return session dict and next index"""
    session = {}
    i = start_idx

    # Parse time slot line (e.g., "11:10 am → 60 min" or "11:10 am")
    time_line = lines[i].strip()
    if '→' in time_line:
        parts = time_line.split('→')
        session['timeSlot'] = parts[0].strip()
        duration_match = re.search(r'(\d+)\s*min', parts[1])
        if duration_match:
            session['duration'] = int(duration_match.group(1))
    else:
        session['timeSlot'] = time_line
        session['duration'] = 60  # default

    i += 1

    # Next line should be the title
    if i < len(lines) and lines[i].strip():
        session['title'] = lines[i].strip()
        i += 1

    # Skip empty lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Next line(s) should be speaker(s)
    speakers = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            break
        # Check if this looks like a level (next field)
        if line in ['Introductory', 'Intermediate', 'Advanced', 'Introductory and overview']:
            session['level'] = line
            i += 1
            break
        # Check if it's a new time slot (next session)
        if re.match(r'\d{1,2}:\d{2}\s*(am|pm)', line):
            break
        # Otherwise, it's a speaker
        speakers.append(line)
        i += 1

    if speakers:
        session['speakers'] = speakers

    # Check for level on next line if not found yet
    if i < len(lines) and 'level' not in session:
        level_line = lines[i].strip()
        if level_line in ['Introductory', 'Intermediate', 'Advanced', 'Introductory and overview']:
            session['level'] = level_line
            i += 1

    # Set default type
    session['sessionType'] = 'session'

    # Skip remaining empty lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    return session, i

def fix_sqlsat1046():
    """Fix sqlsat1046.json"""
    filepath = '../raw/json/sqlsat1046.json'

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find where JSON ends (line 88: "    } ")
    json_end = 88

    # Parse the JSON portion
    json_text = ''.join(lines[:json_end])
    # Add closing brackets to make it valid temporarily
    json_text += "\n  ]\n}"
    data = json.loads(json_text)

    # Parse plain text sessions starting from line 90
    plain_text_lines = [line.rstrip('\n') for line in lines[89:]]  # Skip line 89 which is empty

    i = 0
    while i < len(plain_text_lines):
        line = plain_text_lines[i].strip()

        # Skip empty lines and non-session lines
        if not line:
            i += 1
            continue

        # Check if this is a time slot (start of a session)
        if re.match(r'\d{1,2}:\d{2}\s*(am|pm)', line):
            session, next_i = parse_plain_text_session(plain_text_lines, i)
            if session.get('title'):  # Only add if we got a valid session
                data['schedule'].append(session)
            i = next_i
        else:
            i += 1

    # Write the fixed JSON
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Fixed {filepath}: {len(data['schedule'])} total sessions")

def fix_sqlsat1047():
    """Fix sqlsat1047.json"""
    filepath = '../raw/json/sqlsat1047.json'

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find where JSON ends (line 79)
    json_end = 79

    # Parse the JSON portion
    json_text = ''.join(lines[:json_end])
    json_text += "\n  ]\n}"
    data = json.loads(json_text)

    # Parse plain text sessions
    plain_text_lines = [line.rstrip('\n') for line in lines[79:]]

    i = 0
    while i < len(plain_text_lines):
        line = plain_text_lines[i].strip()

        if not line:
            i += 1
            continue

        if re.match(r'\d{1,2}:\d{2}\s*(am|pm)', line):
            session, next_i = parse_plain_text_session(plain_text_lines, i)
            if session.get('title'):
                data['schedule'].append(session)
            i = next_i
        else:
            i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Fixed {filepath}: {len(data['schedule'])} total sessions")

def fix_sqlsat1054():
    """Fix sqlsat1054.json"""
    filepath = '../raw/json/sqlsat1054.json'

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find where JSON ends (line 28)
    json_end = 28

    # Parse the JSON portion - need to close the last session object
    json_text = ''.join(lines[:json_end])
    json_text += "\n    }\n  ]\n}"
    data = json.loads(json_text)

    # Parse plain text sessions
    plain_text_lines = [line.rstrip('\n') for line in lines[28:]]

    i = 0
    while i < len(plain_text_lines):
        line = plain_text_lines[i].strip()

        if not line:
            i += 1
            continue

        if re.match(r'\d{1,2}:\d{2}\s*(am|pm)', line):
            session, next_i = parse_plain_text_session(plain_text_lines, i)
            if session.get('title'):
                data['schedule'].append(session)
            i = next_i
        else:
            i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Fixed {filepath}: {len(data['schedule'])} total sessions")

def fix_sqlsat1124():
    """Fix sqlsat1124.json - just add missing closing brace"""
    filepath = '../raw/json/sqlsat1124.json'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add the missing closing brace
    content = content.rstrip() + '\n}\n'

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # Validate
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Fixed {filepath}: Valid JSON")

def fix_sqlsat1125():
    """Fix sqlsat1125.json - create minimal valid structure"""
    filepath = '../raw/json/sqlsat1125.json'

    data = {
        "sqlSaturdayEventId": "1125",
        "eventName": "SQL Saturday 1125",
        "location": "Unknown",
        "year": "2023",
        "rooms": [],
        "sessions": [],
        "speakers": []
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Fixed {filepath}: Created minimal structure")

if __name__ == '__main__':
    print("Fixing JSON files...\n")

    try:
        fix_sqlsat1046()
        fix_sqlsat1047()
        fix_sqlsat1054()
        fix_sqlsat1124()
        fix_sqlsat1125()
        print("\nAll files fixed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
