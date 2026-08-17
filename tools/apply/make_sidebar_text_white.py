from pathlib import Path

path = Path("gui/main_window.py")
text = path.read_text(encoding="utf-8-sig")

old = '''            QPushButton#navButton {
                background-color: transparent;
                color: #a8a8b3;
'''
new = '''            QPushButton#navButton {
                background-color: transparent;
                color: #ffffff;
'''

if old in text:
    text = text.replace(old, new, 1)
else:
    raise RuntimeError("navButton stylesheet not found")

old = '''            QLabel#navText {
                background: transparent;
                color: inherit;
                font-size: 13px;
                font-weight: 600;
            }
'''
new = '''            QLabel#navText {
                background: transparent;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
            }
'''

if old in text:
    text = text.replace(old, new, 1)
else:
    raise RuntimeError("navText stylesheet not found")

path.write_text(text, encoding="utf-8-sig")
print("SIDEBAR TEKST IS NU WIT")
