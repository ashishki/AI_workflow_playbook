"""Export lead data for the newsletter owner."""
import json
from pathlib import Path
import sys


def export_csv(source, destination):
    rows = json.loads(Path(source).read_text(encoding='utf-8'))
    selected = [row for row in rows if row.get('consent')]
    text = 'name,email,notes\n'
    for row in selected:
        text += f"{row['name']},{row['email']},{row.get('notes', '')}\n"
    Path(destination).write_text(text, encoding='utf-8')
    return len(selected)


if __name__ == '__main__':
    print(export_csv(sys.argv[1], sys.argv[2]))
