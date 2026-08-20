from pathlib import Path
import re

p = Path(r".\gui\mp3_showcase_page.py")
s = p.read_text(encoding="utf-8-sig")

pattern = re.compile(
    r"""        rest_stylus = QPointF\(cx \+ r \* 1\.03, cy - r \* \.28\)
        play_stylus = QPointF\(cx \+ r \* \.74, cy \+ r \* \.10\)
        stylus = QPointF\(
            rest_stylus\.x\(\) \+ \(play_stylus\.x\(\) - rest_stylus\.x\(\)\) \* self\.arm_progress,
            rest_stylus\.y\(\) \+ \(play_stylus\.y\(\) - rest_stylus\.y\(\)\) \* self\.arm_progress,
        \)
        dx = stylus\.x\(\) - pivot\.x\(\)
        dy = stylus\.y\(\) - pivot\.y\(\)
        length = max\(1\.0, hypot\(dx, dy\)\)
        ux, uy = dx / length, dy / length
        arm_angle = degrees\(atan2\(dy, dx\)\)
""",
    re.MULTILINE
)

replacement = """        # FIXED PHYSICAL ARM LENGTH
        # The stylus moves on an arc around the fixed pivot.
        # This keeps the tonearm physically the same length while playing.
        rest_stylus = QPointF(cx + r * 1.03, cy - r * .28)
        play_stylus = QPointF(cx + r * .74, cy + r * .10)

        rest_dx = rest_stylus.x() - pivot.x()
        rest_dy = rest_stylus.y() - pivot.y()
        play_dx = play_stylus.x() - pivot.x()
        play_dy = play_stylus.y() - pivot.y()

        arm_length = max(1.0, hypot(rest_dx, rest_dy))

        rest_angle = atan2(rest_dy, rest_dx)
        play_angle = atan2(play_dy, play_dx)

        # Shortest rotation from rest position to playing position.
        delta = (
            (play_angle - rest_angle + 3.141592653589793)
            % (2 * 3.141592653589793)
            - 3.141592653589793
        )

        current_angle = rest_angle + delta * self.arm_progress

        # IMPORTANT:
        # Always calculate the stylus from the fixed pivot + fixed radius.
        stylus = QPointF(
            pivot.x() + cos(current_angle) * arm_length,
            pivot.y() + sin(current_angle) * arm_length,
        )

        dx = stylus.x() - pivot.x()
        dy = stylus.y() - pivot.y()
        length = arm_length
        ux, uy = dx / length, dy / length
        arm_angle = degrees(current_angle)
"""

if not pattern.search(s):
    raise SystemExit("FOUT: huidig toonarm-blok niet gevonden. Niets gewijzigd.")

s = pattern.sub(replacement, s, count=1)
p.write_text(s, encoding="utf-8")

print("OK - toonarm heeft nu een vaste fysieke lengte en beweegt in een correcte boog.")
