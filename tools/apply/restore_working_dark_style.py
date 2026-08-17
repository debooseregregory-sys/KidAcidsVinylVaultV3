from pathlib import Path
import ast
import re
import subprocess

FILES = [
    Path("gui/main_window.py"),
    Path("gui/release_library_page.py"),
    Path("gui/release_detail_page.py"),
]


def head_text(path: Path) -> str:
    result = subprocess.run(
        ["git", "show", f"HEAD:{path.as_posix()}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def expr_key(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = expr_key(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def style_calls(source: str):
    tree = ast.parse(source)
    calls = []
    counts = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "setStyleSheet":
            continue
        key = expr_key(func.value)
        if not key:
            continue
        segment = ast.get_source_segment(source, node)
        if not segment:
            continue
        start = (node.lineno - 1, node.col_offset)
        end = (node.end_lineno - 1, node.end_col_offset)
        ordinal = counts.get(key, 0)
        counts[key] = ordinal + 1
        calls.append({
            "key": key,
            "ordinal": ordinal,
            "segment": segment,
            "start": start,
            "end": end,
        })

    return calls


def line_offset(lines, row, col):
    return sum(len(line) for line in lines[:row]) + col


def restore_style_blocks(current: str, head: str) -> str:
    current_calls = style_calls(current)
    head_calls = style_calls(head)

    by_key = {}
    for call in current_calls:
        by_key.setdefault((call["key"], call["ordinal"]), []).append(call)

    replacements = []
    current_lines = current.splitlines(keepends=True)

    for hcall in head_calls:
        candidates = by_key.get((hcall["key"], hcall["ordinal"]), [])
        if not candidates:
            continue
        ccall = candidates.pop(0)
        start = line_offset(current_lines, *ccall["start"])
        end = line_offset(current_lines, *ccall["end"])
        replacements.append((start, end, hcall["segment"]))

    for start, end, replacement in sorted(replacements, reverse=True):
        current = current[:start] + replacement + current[end:]

    return current


def remove_theme_cleanup_lines(source: str) -> str:
    source = re.sub(r"^\s*root\.setStyleSheet\(\"\"\)\s*$\n?", "", source, flags=re.MULTILINE)
    source = re.sub(r"^\s*widget\.setStyleSheet\(\"\"\)\s*$\n?", "", source, flags=re.MULTILINE)
    return source


def tune_main_window(source: str) -> str:
    source = source.replace(
        'background-color: #271522;',
        'background-color: #17171d;',
    )
    source = source.replace(
        'QLabel#navIcon {\n                background: transparent;\n                color: #777783;\n                font-size: 18px;',
        'QLabel#navIcon {\n                background: transparent;\n                color: #c7c7d0;\n                font-size: 30px;',
    )
    source = source.replace(
        'QLabel#navText {\n                background: transparent;\n                color: inherit;\n                font-size: 13px;',
        'QLabel#navText {\n                background: transparent;\n                color: inherit;\n                font-size: 16px;',
    )
    source = source.replace(
        'icon_label.setFixedWidth(\n            24\n        )',
        'icon_label.setFixedWidth(\n            42\n        )',
    )
    source = source.replace(
        'button.setMinimumHeight(\n            48\n        )',
        'button.setMinimumHeight(\n            56\n        )',
        1,
    )
    return source


def tune_library(source: str) -> str:
    source = source.replace(
        'QTableWidget {\n                background-color: #101010;\n                alternate-background-color: #171717;\n                color: #eeeeee;\n                gridline-color: #292929;\n                border: 1px solid #303030;\n                selection-background-color: #383838;\n                selection-color: #ffffff;\n                font-size: 13px;',
        'QTableWidget {\n                background-color: #101010;\n                alternate-background-color: #171717;\n                color: #eeeeee;\n                gridline-color: #292929;\n                border: 1px solid #303030;\n                selection-background-color: #383838;\n                selection-color: #ffffff;\n                font-size: 15px;',
    )
    return source


def tune_detail(source: str) -> str:
    pattern = re.compile(
        r'(self\.review_checklist\.setStyleSheet\(\s*"""\s*)(.*?)(\s*"""\s*\)\s*)',
        re.DOTALL,
    )
    replacement = (
        'self.review_checklist.setStyleSheet(\n'
        '            """\n'
        '            QLabel {\n'
        '                color: #f2f2f5;\n'
        '                background-color: #18181d;\n'
        '                border: 1px solid #383842;\n'
        '                border-radius: 7px;\n'
        '                padding: 9px 12px;\n'
        '                font-size: 15px;\n'
        '                font-weight: bold;\n'
        '            }\n'
        '            """\n'
        '        )'
    )
    source, count = pattern.subn(replacement, source, count=1)
    return source


for path in FILES:
    current = path.read_text(encoding="utf-8-sig")
    head = head_text(path)

    restored = restore_style_blocks(current, head)
    restored = remove_theme_cleanup_lines(restored)

    if path.name == "main_window.py":
        restored = tune_main_window(restored)
    elif path.name == "release_library_page.py":
        restored = tune_library(restored)
    elif path.name == "release_detail_page.py":
        restored = tune_detail(restored)

    path.write_text(restored, encoding="utf-8-sig")
    print(f"DARK STYLE HERSTELD: {path}")

print("KLAAR: functionele wijzigingen behouden, roze themawijzigingen verwijderd")
