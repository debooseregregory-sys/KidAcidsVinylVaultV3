from pathlib import Path
import ast
import subprocess

FILES = [
    Path('gui/main_window.py'),
    Path('gui/release_library_page.py'),
    Path('gui/release_detail_page.py'),
]


def git_head(path: Path) -> str:
    return subprocess.run(
        ['git', 'show', f'HEAD:{path.as_posix()}'],
        check=True,
        capture_output=True,
        text=True,
        encoding='utf-8',
    ).stdout


def style_calls(source: str):
    tree = ast.parse(source)
    out = []
    counts = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != 'setStyleSheet':
            continue
        key = ast.dump(node.func.value, include_attributes=False)
        ordinal = counts.get(key, 0)
        counts[key] = ordinal + 1
        seg = ast.get_source_segment(source, node)
        if seg:
            out.append((key, ordinal, node.lineno - 1, node.col_offset, node.end_lineno - 1, node.end_col_offset, seg))
    return out


def offset(lines, row, col):
    return sum(len(x) for x in lines[:row]) + col

for path in FILES:
    current = path.read_text(encoding='utf-8-sig')
    head = git_head(path)
    cur_calls = style_calls(current)
    head_calls = style_calls(head)

    cur_map = {(k, o): (srow, scol, erow, ecol) for k, o, srow, scol, erow, ecol, _ in cur_calls}
    head_map = {(k, o): seg for k, o, _, _, _, _, seg in head_calls}

    lines = current.splitlines(keepends=True)
    replacements = []
    for key, ordinal, srow, scol, erow, ecol, _ in cur_calls:
        replacement = head_map.get((key, ordinal))
        if replacement is None:
            continue
        replacements.append((offset(lines, srow, scol), offset(lines, erow, ecol), replacement))

    for start, end, replacement in sorted(replacements, reverse=True):
        current = current[:start] + replacement + current[end:]

    path.write_text(current, encoding='utf-8-sig')
    print(f'DONKERE STYLE HERSTELD: {path}')

print('KLAAR: alleen setStyleSheet-blokken zijn hersteld naar HEAD.')
