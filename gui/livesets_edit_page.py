from __future__ import annotations

import json
import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LIVESETS_FILE = DATA_DIR / "livesets.json"
COVERS_DIR = DATA_DIR / "liveset_covers"


class LivesetsEditPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items=[]; self.selected=-1; self._build(); self.reload()

    def _build(self):
        root=QVBoxLayout(self); root.setContentsMargins(28,24,28,24); root.setSpacing(12)
        title=QLabel("LIVESETS BEWERKEN"); title.setObjectName("editTitle"); root.addWidget(title)
        sub=QLabel("Beheer titel, artiest, datum, locatie, audio en cover afzonderlijk van de showcase."); sub.setObjectName("editSub"); root.addWidget(sub)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("QScrollArea{border:0;background:transparent;}")
        self.content=QWidget(); form=QVBoxLayout(self.content); form.setContentsMargins(4,16,4,20); form.setSpacing(10); scroll.setWidget(self.content); root.addWidget(scroll,1)
        self.fields={}
        for key,label in [("title","Titel"),("artist","Artiest / DJ"),("date","Datum"),("location","Locatie"),("duration","Duur / tracks"),("audio","Audio")]:
            row=QHBoxLayout(); lab=QLabel(label); lab.setFixedWidth(130); edit=QLineEdit(); self.fields[key]=edit; row.addWidget(lab); row.addWidget(edit,1); form.addLayout(row)
        self.cover=QLabel("GEEN COVER"); self.cover.setObjectName("editCover"); self.cover.setFixedSize(420,236); self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter); form.addWidget(self.cover)
        buttons=QHBoxLayout(); choose=QPushButton("KIES COVER"); choose.clicked.connect(self.choose_cover); save=QPushButton("OPSLAAN"); save.clicked.connect(self.save); delete=QPushButton("VERWIJDER LIVESET"); delete.clicked.connect(self.delete_current); buttons.addWidget(choose); buttons.addWidget(save); buttons.addWidget(delete); form.addLayout(buttons)
        self.setStyleSheet("""
            QLabel#editTitle{color:#fff;font-size:28px;font-weight:900;} QLabel#editSub{color:#858591;font-size:13px;}
            QLineEdit{background:#121217;color:#fff;border:1px solid #30303a;border-radius:8px;padding:10px;}
            QPushButton{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:7px;padding:10px 15px;font-size:12px;font-weight:800;}
            QPushButton:hover{background:#24242c;border-color:#ffcf72;} QLabel#editCover{background:#07070a;color:#666671;border:1px solid #2a2a33;border-radius:7px;}
        """)

    def reload(self):
        try:self.items=json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
        except (OSError,json.JSONDecodeError):self.items=[]
        if self.items:self.select(0)

    def select(self,index):
        self.selected=index; data=self.items[index]
        for k,e in self.fields.items(): e.setText(str(data.get(k) or ""))
        self._show_cover(str(data.get("cover") or ""))

    def choose_cover(self):
        path,_=QFileDialog.getOpenFileName(self,"Kies cover","","Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not path:return
        COVERS_DIR.mkdir(parents=True,exist_ok=True); dest=COVERS_DIR/(f"edit_{abs(hash(Path(path).name))}{Path(path).suffix.lower()}"); shutil.copy2(path,dest); self.fields["cover"].setText(str(dest)); self._show_cover(str(dest))

    def _show_cover(self,path):
        pix=QPixmap(path) if path and Path(path).exists() else QPixmap()
        if pix.isNull():self.cover.setPixmap(QPixmap());self.cover.setText("GEEN COVER");return
        scaled=pix.scaled(self.cover.size(),Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation); x=max(0,(scaled.width()-self.cover.width())//2); y=max(0,(scaled.height()-self.cover.height())//2); self.cover.setText("");self.cover.setPixmap(scaled.copy(x,y,self.cover.width(),self.cover.height()))

    def save(self):
        if self.selected<0:return
        self.items[self.selected]={k:e.text().strip() for k,e in self.fields.items()}
        DATA_DIR.mkdir(parents=True,exist_ok=True); LIVESETS_FILE.write_text(json.dumps(self.items,ensure_ascii=False,indent=2),encoding="utf-8")

    def delete_current(self):
        if self.selected<0:return
        self.items.pop(self.selected); DATA_DIR.mkdir(parents=True,exist_ok=True); LIVESETS_FILE.write_text(json.dumps(self.items,ensure_ascii=False,indent=2),encoding="utf-8"); self.selected=-1
        for e in self.fields.values():e.clear()
        self.cover.setPixmap(QPixmap());self.cover.setText("GEEN COVER")
