from pathlib import Path

p = Path("gui/mp3_showcase_page.py")
text = p.read_text(encoding="utf-8-sig")

if "self.body_layout = body" in text:
    text = text.replace(
        "        self.body_layout = body\n",
        "        body = QHBoxLayout()\n        self.body_layout = body\n",
        1,
    )
elif "body.setSpacing(" in text and "body = QHBoxLayout()" not in text:
    text = text.replace(
        "        body.setSpacing(",
        "        body = QHBoxLayout()\n        self.body_layout = body\n        body.setSpacing(",
        1,
    )

p.write_text(text, encoding="utf-8-sig")
print("OK: MP3 Showcase body-layout hersteld.")
