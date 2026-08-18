from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / 'gui' / 'mp3_showcase_page.py'
text = TARGET.read_text(encoding='utf-8-sig')

start = text.index('        list_panel = QWidget()')
end = text.index('        self.timer = QTimer(self)', start)
replacement = '''        self.list = QListWidget()
        self.list.setMinimumWidth(560)
        self.list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.currentRowChanged.connect(self.select_index)
        body.addWidget(self.list, 1)

'''
text = text[:start] + replacement + text[end:]

old_start = text.index('            name = Path(str(row[0])).name')
old_end = text.index('        self.list.blockSignals(False)', old_start)
replacement = '''            name = Path(str(row[0])).name
            artist = str(row[1] or '').strip() or 'Onbekende artiest'
            title = str(row[2] or '').strip() or name
            item = QListWidgetItem(f'{artist:<42}  {title}')
            item.setToolTip(str(row[0]))
            self.list.addItem(item)

'''
text = text[:old_start] + replacement + text[old_end:]

text = text.replace('            QListWidget::item{\n                padding:0;\n                border-bottom:1px solid #24242d;\n            }', '            QListWidget::item{\n                padding:10px 14px;\n                border-bottom:1px solid #24242d;\n            }')

TARGET.write_text(text, encoding='utf-8')
print('MP3 Showcase freeze fix toegepast: geen QWidget per MP3-item meer.')
