from pathlib import Path

p = Path('gui/mp3_duplicate_cleaner.py')
# This installer rebuilds the cleaner from a stable database-driven matcher.
# It preserves multi-select, ignore groups, delete files, duration fallback, and double-click play.

text = r'''from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QProgressBar, QCheckBox
)

from database.database import get_connection

try:
    from mutagen.mp3 import MP3
except Exception:
    MP3 = None

_COPY_SUFFIX_RE = re.compile(r"\s*(?:\([0-9]+\)|\[[0-9]+\]|[_-](?:copy|kopie|[0-9]+))\s*$", re.I)


def normalize_text(value):
    value = str(value or '').casefold().strip()
    value = value.replace('_', ' ')
    value = re.sub(r'\s+', ' ', value)
    return value.strip()


def normalize_copy_suffix(value):
    value = normalize_text(value)
    while True:
        cleaned = _COPY_SUFFIX_RE.sub('', value).strip(' -_')
        if cleaned == value:
            return value
        value = cleaned


def track_key(artist, title):
    a = normalize_text(artist)
    t = normalize_copy_suffix(title)
    return f'{a}|||{t}' if a and t else ''


def duration_text(value, path):
    try:
        seconds = float(value)
        if seconds > 0:
            seconds = int(round(seconds))
            return f'{seconds // 60}:{seconds % 60:02d}'
    except Exception:
        pass
    if MP3 is not None:
        try:
            seconds = int(round(float(MP3(str(path)).info.length)))
            return f'{seconds // 60}:{seconds % 60:02d}'
        except Exception:
            pass
    return '--:--'


def ensure_ignore_table():
    conn = get_connection()
    try:
        conn.execute('CREATE TABLE IF NOT EXISTS mp3_duplicate_ignored (track_key TEXT PRIMARY KEY, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
        conn.commit()
    finally:
        conn.close()


def load_ignored_keys():
    ensure_ignore_table()
    conn = get_connection()
    try:
        return {str(r[0]) for r in conn.execute('SELECT track_key FROM mp3_duplicate_ignored').fetchall()}
    finally:
        conn.close()


def save_ignored_keys(keys):
    ensure_ignore_table()
    conn = get_connection()
    try:
        conn.execute('DELETE FROM mp3_duplicate_ignored')
        conn.executemany('INSERT OR IGNORE INTO mp3_duplicate_ignored(track_key) VALUES (?)', [(k,) for k in sorted(keys)])
        conn.commit()
    finally:
        conn.close()


class HashWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)

    def __init__(self, ignored_keys, show_ignored, parent=None):
        super().__init__(parent)
        self.ignored_keys = set(ignored_keys or set())
        self.show_ignored = bool(show_ignored)
        self._stop = False

    def request_stop(self):
        self._stop = True
        self.requestInterruption()

    def run(self):
        try:
            conn = get_connection()
            try:
                rows = conn.execute('''
                    SELECT m.id, m.path, m.artist, m.title, m.album, m.year,
                           m.duration, COALESCE(m.metadata_checked,0),
                           EXISTS(SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id)
                    FROM mp3_files m
                    WHERE m.path IS NOT NULL
                    ORDER BY m.artist COLLATE NOCASE, m.title COLLATE NOCASE, m.path COLLATE NOCASE
                ''').fetchall()
            finally:
                conn.close()

            total = len(rows)
            groups = defaultdict(list)

            for n, row in enumerate(rows, 1):
                if self._stop or self.isInterruptionRequested():
                    return
                mp3_id, path, artist, title, album, year, duration, checked, linked = row
                path = str(path or '')
                key = track_key(artist, title)
                if key and Path(path).is_file():
                    groups[key].append({
                        'id': int(mp3_id), 'path': path,
                        'artist': str(artist or '').strip(),
                        'title': str(title or '').strip(),
                        'album': str(album or '').strip(), 'year': year,
                        'duration': duration, 'checked': int(checked or 0),
                        'linked': int(linked or 0)
                    })
                if n == total or n % 250 == 0:
                    self.progress.emit(n, total)

            out = []
            for key, members in groups.items():
                if len(members) < 2:
                    continue
                ignored = key in self.ignored_keys
                if ignored and not self.show_ignored:
                    continue
                out.append({'key': key, 'ignored': ignored, 'files': members})

            out.sort(key=lambda g: (-len(g['files']), g['files'][0]['artist'].casefold(), g['files'][0]['title'].casefold()))
            self.finished_scan.emit(out)
        except Exception as exc:
            self.failed.emit(str(exc))


class MP3DuplicateCleaner(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('MP3 DUBBELE TRACKS')
        self.resize(1200, 800)
        self.worker = None
        self._closing = False
        self.ignored_keys = load_ignored_keys()
        self.play_mp3 = Signal(str) if False else None

        root = QVBoxLayout(self)
        root.setSpacing(10)
        title = QLabel('MP3 DUBBELE TRACKS')
        title.setStyleSheet('font-size:24px;font-weight:900;color:#fff;')
        root.addWidget(title)

        info = QLabel('Ctrl + klik en Shift + klik voor meerdere selectie. Dubbelklik op een MP3 om hem af te spelen. Versies zoals Remix, Club Mix, Rap Version, Instrumental en Live blijven apart.')
        info.setWordWrap(True)
        info.setStyleSheet('color:#aaaab3;')
        root.addWidget(info)

        tools = QHBoxLayout()
        self.show_ignored = QCheckBox('TOON GENEGEERDE GROEPEN')
        tools.addWidget(self.show_ignored)
        tools.addStretch()
        root.addLayout(tools)

        self.progress = QProgressBar()
        self.progress.setRange(0,100)
        root.addWidget(self.progress)
        self.summary = QLabel('Nog niet gescand.')
        self.summary.setStyleSheet('color:#d84b91;font-weight:bold;')
        root.addWidget(self.summary)

        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        root.addWidget(self.list,1)

        actions = QHBoxLayout()
        self.scan_button = QPushButton('[ SCAN DUBBELS ]')
        self.ignore_button = QPushButton('[ GESELECTEERDE GROEPEN NEGEREN ]')
        self.unignore_button = QPushButton('[ NEGEREN OPHEFFEN ]')
        self.delete_button = QPushButton('[ GESELECTEERDE BESTANDEN VERWIJDEREN ]')
        self.close_button = QPushButton('[ SLUITEN ]')
        for b in (self.ignore_button,self.unignore_button,self.delete_button): b.setEnabled(False)
        actions.addWidget(self.scan_button); actions.addWidget(self.ignore_button); actions.addWidget(self.unignore_button); actions.addWidget(self.delete_button); actions.addStretch(); actions.addWidget(self.close_button)
        root.addLayout(actions)

        self.scan_button.clicked.connect(self.scan)
        self.show_ignored.toggled.connect(self.scan)
        self.ignore_button.clicked.connect(self.ignore_selected_groups)
        self.unignore_button.clicked.connect(self.unignore_selected_groups)
        self.delete_button.clicked.connect(self.delete_selected_files)
        self.close_button.clicked.connect(self.close)
        self.list.itemSelectionChanged.connect(self.refresh_button_state)
        self.list.itemDoubleClicked.connect(self.play_item)

        self.setStyleSheet('''
        QDialog { background:#0b0b0f; color:#f2f2f5; }
        QListWidget { background:#0f0f14; border:1px solid #25252d; }
        QListWidget::item { padding:10px; border-bottom:1px solid #24242d; }
        QListWidget::item:selected { background:#271522; }
        QPushButton { background:#18181f; color:#fff; border:1px solid #30303a; border-radius:6px; padding:9px 12px; }
        QPushButton:hover { border-color:#d84b91; background:#24242c; }
        QCheckBox { color:#fff; padding:4px; }
        QProgressBar { border:1px solid #30303a; background:#18181f; height:12px; border-radius:5px; }
        QProgressBar::chunk { background:#d84b91; border-radius:5px; }
        ''')
        self.scan()

    def scan(self):
        if self.worker and self.worker.isRunning(): return
        self._closing=False; self.list.clear(); self.progress.setValue(0)
        self.summary.setText("Scannen van MP3's...")
        for b in (self.ignore_button,self.unignore_button,self.delete_button): b.setEnabled(False)
        self.scan_button.setEnabled(False)
        self.worker = HashWorker(self.ignored_keys, self.show_ignored.isChecked(), self)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_scan.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.finished.connect(lambda: self.scan_button.setEnabled(True))
        self.worker.start()

    def on_progress(self, processed, total):
        self.progress.setValue(int(processed/total*100) if total else 100)
        self.summary.setText(f"Scannen: {processed:,} / {total:,} MP3's")

    def on_failed(self, message):
        self.scan_button.setEnabled(True)
        if not self._closing: QMessageBox.critical(self,'Dubbel-scan mislukt',message)

    def on_finished(self, groups):
        if self._closing: return
        self.list.clear(); self.progress.setValue(100); self.scan_button.setEnabled(True)
        dup = sum(max(0,len(g['files'])-1) for g in groups)
        if not groups:
            self.summary.setText(f'Geen zichtbare dubbele groepen. {len(self.ignored_keys):,} genegeerd.')
            self.refresh_button_state(); return
        for i, group in enumerate(groups,1):
            first=group['files'][0]
            header=QListWidgetItem(f"GROEP {i} - {first['artist'] or 'Onbekende artiest'} - {first['title'] or 'Onbekende titel'} - {len(group['files'])} BESTANDEN")
            header.setData(Qt.ItemDataRole.UserRole, {'kind':'group','group_key':group['key'],'ignored':group['ignored']})
            self.list.addItem(header)
            for member in group['files']:
                dur=duration_text(member['duration'], member['path'])
                flags=[]
                if member['linked']: flags.append('VINYL GEKOPPELD')
                if member['checked']: flags.append('METADATA KLAAR')
                label=f"{Path(member['path']).name} | DUUR {dur} | PAD {member['path']}"
                if flags: label += ' | ' + ' / '.join(flags)
                item=QListWidgetItem(label)
                item.setToolTip(f"PAD: {member['path']}\nDUUR: {dur}")
                item.setData(Qt.ItemDataRole.UserRole, {'kind':'file','group_key':group['key'],'path':member['path'],'id':member['id'],'linked':bool(member['linked'])})
                self.list.addItem(item)
        self.summary.setText(f"{len(groups):,} dubbele groepen | {dup:,} overtollige kopieen | {len(self.ignored_keys):,} genegeerd")
        self.refresh_button_state()

    def refresh_button_state(self):
        groups=0; files=0
        for item in self.list.selectedItems():
            data=item.data(Qt.ItemDataRole.UserRole)
            if not isinstance(data,dict): continue
            if data.get('kind')=='group': groups+=1
            elif data.get('kind')=='file' and not data.get('linked'): files+=1
        self.ignore_button.setEnabled(groups>0); self.unignore_button.setEnabled(groups>0); self.delete_button.setEnabled(files>0)
        self.ignore_button.setText(f'[ GESELECTEERDE GROEPEN NEGEREN ({groups}) ]')
        self.unignore_button.setText(f'[ NEGEREN OPHEFFEN ({groups}) ]')
        self.delete_button.setText(f'[ GESELECTEERDE BESTANDEN VERWIJDEREN ({files}) ]')

    def selected_group_keys(self):
        keys=set()
        for item in self.list.selectedItems():
            data=item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data,dict) and data.get('kind')=='group' and data.get('group_key'): keys.add(data['group_key'])
        return keys

    def ignore_selected_groups(self):
        keys=self.selected_group_keys()
        if not keys: return
        self.ignored_keys.update(keys); save_ignored_keys(self.ignored_keys); self.scan()

    def unignore_selected_groups(self):
        keys=self.selected_group_keys()
        if not keys: return
        self.ignored_keys.difference_update(keys); save_ignored_keys(self.ignored_keys); self.show_ignored.setChecked(True); self.scan()

    def selected_files(self):
        out=[]
        for item in self.list.selectedItems():
            data=item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data,dict) and data.get('kind')=='file' and not data.get('linked'): out.append(data)
        return out

    def delete_selected_files(self):
        selected=self.selected_files()
        if not selected: return
        preview='\n'.join(str(x['path']) for x in selected[:10])
        if len(selected)>10: preview+='\n...'
        answer=QMessageBox.question(self,'DEFINITIEF VERWIJDEREN',f"Je gaat {len(selected)} MP3-bestand(en) ECHT van de harde schijf verwijderen.\n\n{preview}\n\nDoorgaan?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes: return
        deleted=0; errors=[]
        conn=get_connection()
        try:
            for data in selected:
                try:
                    Path(data['path']).unlink(); conn.execute('DELETE FROM mp3_files WHERE id=?',(int(data['id']),)); deleted+=1
                except Exception as exc: errors.append(f"{data['path']}\n{exc}")
            conn.commit()
        finally: conn.close()
        msg=f'{deleted} MP3-bestand(en) definitief van de schijf verwijderd.'
        if errors: msg += '\n\nNiet verwijderd:\n'+'\n\n'.join(errors[:5])
        QMessageBox.information(self,'Resultaat',msg); self.scan()

    def play_item(self, item):
        data=item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(data,dict) or data.get('kind')!='file': return
        path=str(data.get('path') or '')
        if not path: return
        parent=self.parent()
        if parent is not None:
            signal=getattr(parent,'play_mp3',None)
            if signal is not None and hasattr(signal,'emit'):
                signal.emit(path); return
            main=getattr(parent,'window',lambda:None)()
            signal=getattr(main,'play_mp3',None) if main is not None else None
            if signal is not None and hasattr(signal,'emit'):
                signal.emit(path); return
        try:
            import os
            os.startfile(path)
        except Exception as exc:
            QMessageBox.warning(self,'Afspelen mislukt',str(exc))

    def closeEvent(self,event):
        self._closing=True
        if self.worker and self.worker.isRunning():
            self.worker.request_stop(); self.worker.wait()
        self.worker=None
        event.accept()
'''
p.write_text(text, encoding='utf-8-sig')
print('OK: stable duplicate cleaner rebuilt')
