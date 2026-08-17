from pathlib import Path
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QFrame
from database.database import get_connection
try:
    from mutagen.id3 import ID3, ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

class MP3ShowcasePage(QWidget):
    play_mp3 = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items=[]; self.visible_items=[]; self.current_index=-1
        self.build_ui(); self.load_files()
    def build_ui(self):
        root=QVBoxLayout(self); root.setContentsMargins(28,22,28,22); root.setSpacing(14)
        title=QLabel('MP3 SHOWCASE'); title.setStyleSheet('font-size:26px;font-weight:900;color:#fff;'); root.addWidget(title)
        search=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText('Zoek artiest, titel, album of bestand...'); search.addWidget(self.search,1)
        self.refresh=QPushButton('VERVERS'); search.addWidget(self.refresh); root.addLayout(search)
        self.status=QLabel('0 MP3\'s'); self.status.setStyleSheet('color:#9b9ba6;'); root.addWidget(self.status)
        body=QHBoxLayout(); body.setSpacing(20)
        self.list=QListWidget(); self.list.setMinimumWidth(360); self.list.currentRowChanged.connect(self.select_index); body.addWidget(self.list)
        card=QFrame(); card.setStyleSheet('QFrame{background:#121219;border:1px solid #2a2532;border-radius:10px;}'); cl=QVBoxLayout(card); cl.setContentsMargins(22,22,22,22); cl.setSpacing(10)
        self.cover=QLabel('NO COVER'); self.cover.setFixedSize(340,340); self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter); self.cover.setStyleSheet('background:#0b0b0f;color:#666672;border:1px solid #302b39;border-radius:6px;'); cl.addWidget(self.cover,0,Qt.AlignmentFlag.AlignHCenter)
        self.artist_label=QLabel('-'); self.artist_label.setStyleSheet('color:#d84b91;font-size:18px;font-weight:bold;'); cl.addWidget(self.artist_label)
        self.title_label=QLabel('-'); self.title_label.setWordWrap(True); self.title_label.setStyleSheet('color:#fff;font-size:25px;font-weight:800;'); cl.addWidget(self.title_label)
        self.meta_label=QLabel('-'); self.meta_label.setWordWrap(True); self.meta_label.setStyleSheet('color:#aaaab3;font-size:13px;'); cl.addWidget(self.meta_label)
        self.comment_label=QLabel(''); self.comment_label.setWordWrap(True); self.comment_label.setStyleSheet('color:#777783;font-size:12px;'); cl.addWidget(self.comment_label)
        controls=QHBoxLayout(); self.previous=QPushButton('◀ VORIGE'); self.play=QPushButton('▶ PLAY'); self.next=QPushButton('VOLGENDE ▶'); controls.addWidget(self.previous); controls.addWidget(self.play,1); controls.addWidget(self.next); cl.addLayout(controls)
        body.addWidget(card,1); root.addLayout(body,1)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(180); self.timer.timeout.connect(self.populate_list); self.search.textChanged.connect(lambda _: self.timer.start())
        self.refresh.clicked.connect(self.load_files); self.previous.clicked.connect(self.previous_track); self.next.clicked.connect(self.next_track); self.play.clicked.connect(self.play_current)
        self.setStyleSheet('QWidget{background:#0b0b0f;color:#f2f2f5;} QLineEdit,QPushButton,QListWidget{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:8px 10px;} QPushButton:hover{border-color:#d84b91;background:#24242c;} QListWidget::item{padding:8px;border-bottom:1px solid #24242d;} QListWidget::item:selected{background:#271522;border:1px solid #5d2947;}')
    def load_files(self):
        conn=get_connection()
        try: rows=conn.execute('SELECT path,artist,title,album,year,bpm,genre FROM mp3_files ORDER BY artist COLLATE NOCASE,title COLLATE NOCASE,path COLLATE NOCASE').fetchall()
        finally: conn.close()
        self.items=[tuple(r) for r in rows]; self.populate_list()
    def populate_list(self):
        q=self.search.text().strip().casefold(); self.visible_items=[r for r in self.items if not q or q in ' '.join(str(x or '') for x in r).casefold()]
        self.list.blockSignals(True); self.list.clear()
        for r in self.visible_items:
            name=Path(str(r[0])).name; artist=str(r[1] or '').strip(); title=str(r[2] or '').strip(); text=f'{artist} - {title}'.strip(' -') if artist or title else name
            it=QListWidgetItem(text); it.setToolTip(str(r[0])); self.list.addItem(it)
        self.list.blockSignals(False); self.status.setText(f'{len(self.visible_items)} van {len(self.items)} MP3\'s')
        if self.visible_items: self.list.setCurrentRow(0)
        else: self.current_index=-1; self.clear_showcase()
    def select_index(self,index):
        self.current_index=index
        if 0<=index<len(self.visible_items): self.show_item(self.visible_items[index])
    def show_item(self,row):
        path,artist,title,album,year,bpm,genre=row; self.artist_label.setText(str(artist or '-')); self.title_label.setText(str(title or Path(str(path)).stem))
        meta=[]
        if album: meta.append(f'Album: {album}')
        if year: meta.append(f'Jaar: {year}')
        if genre: meta.append(f'Genre: {genre}')
        if bpm: meta.append(f'BPM: {bpm}')
        self.meta_label.setText('  •  '.join(meta) if meta else 'Geen aanvullende metadata'); self.comment_label.setText(''); self.cover.setPixmap(QPixmap()); self.cover.setText('NO COVER')
        if MUTAGEN_AVAILABLE and Path(str(path)).exists():
            try:
                tags=ID3(str(path)); comments=tags.getall('COMM'); vals=[]
                for f in comments: vals += [str(v).strip() for v in f.text if str(v).strip()]
                if vals: self.comment_label.setText(' • '.join(dict.fromkeys(vals)))
                pics=tags.getall('APIC')
                if pics:
                    p=QPixmap();
                    if p.loadFromData(pics[0].data): self.cover.setPixmap(p.scaled(340,340,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)); self.cover.setText('')
            except (ID3NoHeaderError, Exception): pass
        self.previous.setEnabled(self.current_index>0); self.next.setEnabled(self.current_index+1<len(self.visible_items)); self.play.setEnabled(True)
    def clear_showcase(self):
        self.cover.setPixmap(QPixmap()); self.cover.setText('NO COVER'); self.artist_label.setText('-'); self.title_label.setText('-'); self.meta_label.setText('-'); self.comment_label.setText(''); self.previous.setEnabled(False); self.next.setEnabled(False); self.play.setEnabled(False)
    def play_current(self):
        if 0<=self.current_index<len(self.visible_items):
            path=str(self.visible_items[self.current_index][0])
            if Path(path).exists(): self.play_mp3.emit(path)
    def previous_track(self):
        if self.current_index>0: self.list.setCurrentRow(self.current_index-1)
    def next_track(self):
        if self.current_index+1<len(self.visible_items): self.list.setCurrentRow(self.current_index+1)
