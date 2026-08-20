from pathlib import Path
import re

path = Path("gui/mp3_showcase_page.py")
text = path.read_text(encoding="utf-8-sig")

pattern = re.compile(
    r"    def resizeEvent\(self, event\):\n"
    r".*?(?=    def load_files\(self\):)",
    re.DOTALL,
)

replacement = '''    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Use the REAL layouts that are installed in the widget.
        compact = self.width() < 1100

        # Main area: list above card when narrow, side-by-side when wide.
        self.body.setDirection(
            QBoxLayout.Direction.TopToBottom
            if compact
            else QBoxLayout.Direction.LeftToRight
        )

        # Detail area: cover above metadata when narrow, side-by-side when wide.
        self.top.setDirection(
            QBoxLayout.Direction.TopToBottom
            if compact
            else QBoxLayout.Direction.LeftToRight
        )

        # Never let the detail card keep a width that forces overlap.
        self.detail_card.setMinimumWidth(0)
        self.detail_card.setMaximumWidth(16777215)

        # The list needs no hard width in compact mode.
        if compact:
            self.list.setMinimumWidth(0)
            self.list.setMaximumWidth(16777215)
        else:
            self.list.setMinimumWidth(260)
            self.list.setMaximumWidth(420)

        # Cover scales with the actual detail-card width.
        if compact:
            cover_size = max(150, min(240, self.detail_card.width() - 44))
        else:
            cover_size = max(180, min(340, int(self.detail_card.width() * 0.40)))

        self.cover.setFixedSize(cover_size, cover_size)

        # Controls stay in their own vertical row below the cover/info block.
        self.controls_layout.setDirection(QBoxLayout.Direction.LeftToRight)
        self.controls_layout.setSpacing(8)

'''

if not pattern.search(text):
    raise SystemExit("resizeEvent() niet gevonden in de huidige lokale mp3_showcase_page.py")

text = pattern.sub(replacement, text, count=1)
path.write_text(text, encoding="utf-8-sig")
print("OK: huidige lokale resizeEvent vervangen door stabiele versie.")
