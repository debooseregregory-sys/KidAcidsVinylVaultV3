from pathlib import Path

p = Path('gui/mp3_showcase_page.py')
text = p.read_text(encoding='utf-8-sig')

needle = '        self.body_layout = body\n'
if needle in text and '        body = QHBoxLayout()\n        self.body_layout = body\n' not in text:
    text = text.replace(
        needle,
        '        body = QHBoxLayout()\n'
        '        body.setSpacing(20)\n'
        '        self.body_layout = body\n',
        1,
    )

needle = '        self.controls_layout.addWidget(self.previous)\n'
if needle in text and '        controls_layout = QHBoxLayout()\n        self.controls_layout = controls_layout\n' not in text:
    text = text.replace(
        needle,
        '        controls_layout = QHBoxLayout()\n'
        '        controls_layout.setSpacing(10)\n'
        '        self.controls_layout = controls_layout\n'
        '        self.controls_layout.addWidget(self.previous)\n',
        1,
    )

p.write_text(text, encoding='utf-8-sig')
print('OK: MP3 Showcase layout variables initialized before use.')
