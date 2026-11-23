#!/usr/bin/env python3
"""Generate the documentation diagrams as plain SVG (stdlib only).

Usage: python3 scripts/make-diagrams.py

Writes docs/images/overview.svg, guardrail-flow.svg and briefing-flow.svg.
Output is deterministic: re-running produces byte-identical files, so commit
the result after any change here.

All three diagrams share one style and one vocabulary: the same colors per
kind (data, script, cloud LLM), the same step names, and the same green
"Verify" bracket for the quote check plus the judge.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "images"
W = 1000
SANS = 'font-family="Segoe UI, Arial, Helvetica, sans-serif"'
MONO = 'font-family="Consolas, Menlo, monospace"'

INK = "#0f172a"
SUB = "#334155"
LINE = "#475569"
VERIFY = "#047857"
# kind -> (border / tag text, header tint, tag)
KIND = {
    "data":   ("#475569", "#e2e8f0", "DATA"),
    "script": ("#1d4ed8", "#dbeafe", "SCRIPT"),
    "ai":     ("#b45309", "#fde68a", "CLOUD LLM"),
    "verify": ("#047857", "#d1fae5", "SCRIPT + LLM"),
}
# approximate glyph widths in px, used to refuse text that would overflow
W_TITLE, W_SUB, W_MONO = 9.0, 7.1, 7.9


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Canvas:
    def __init__(self, title, subtitle, height):
        self.h, self.cards = height, {}
        self.o = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
            f'width="{W}" height="{height}" role="img">',
            f'  <title>{esc(title)}</title>',
            '  <defs>',
            '    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" '
            'markerHeight="8" orient="auto">',
            f'      <path d="M 0 1 L 9 5 L 0 9 z" fill="{LINE}"/>',
            '    </marker>',
            '  </defs>',
            f'  <rect x="0" y="0" width="{W}" height="{height}" fill="#ffffff"/>',
            f'  <text x="32" y="44" {SANS} font-size="24" font-weight="bold" fill="{INK}">{esc(title)}</text>',
            f'  <text x="32" y="70" {SANS} font-size="15" fill="{SUB}">{esc(subtitle)}</text>',
        ]
        self.under = len(self.o)  # zones are inserted here, below cards and arrows

    # -- elements -----------------------------------------------------------
    def lane(self, y, h, label):
        self.o.append(f'  <rect x="16" y="{y}" width="{W - 32}" height="{h}" rx="14" ry="14" '
                      f'fill="#f8fafc" stroke="#cbd5e1" stroke-width="1"/>')
        self.o.append(f'  <text x="32" y="{y + 24}" {SANS} font-size="13" font-weight="bold" '
                      f'letter-spacing="1" fill="{SUB}">{esc(label)}</text>')

    def card(self, key, kind, x, y, w, h, title, lines, step=None):
        if len(title) * W_TITLE > w - 24:
            raise SystemExit(f"title overflows card {key!r}: {title!r}")
        for s in lines:
            if len(s) * (W_MONO if s.startswith("`") else W_SUB) > w - 24:
                raise SystemExit(f"text overflows card {key!r}: {s!r}")
        border, tint, tag = KIND[kind]
        self.cards[key] = (x, y, w, h)
        o = self.o
        o.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" ry="12" '
                 f'fill="#ffffff" stroke="{border}" stroke-width="2"/>')
        o.append(f'  <path d="M {x + 12} {y + 1} H {x + w - 12} Q {x + w - 1} {y + 1} {x + w - 1} {y + 12} '
                 f'V {y + 30} H {x + 1} V {y + 12} Q {x + 1} {y + 1} {x + 12} {y + 1} Z" fill="{tint}"/>')
        label = f"{step}  {tag}" if step is not None else tag
        o.append(f'  <text x="{x + 12}" y="{y + 21}" {SANS} font-size="12" font-weight="bold" '
                 f'letter-spacing="0.8" fill="{border}">{esc(label)}</text>')
        o.append(f'  <text x="{x + 12}" y="{y + 54}" {SANS} font-size="16" font-weight="bold" '
                 f'fill="{INK}">{esc(title)}</text>')
        for i, s in enumerate(lines):
            mono = s.startswith("`")
            s = s.strip("`")
            font = MONO if mono else SANS
            o.append(f'  <text x="{x + 12}" y="{y + 76 + 18 * i}" {font} font-size="13" '
                     f'fill="{SUB}">{esc(s)}</text>')

    def _box(self, key):
        return self.cards[key]

    def arrow(self, a, b):
        ax, ay, aw, ah = self._box(a)
        bx, by, bw, bh = self._box(b)
        if bx >= ax + aw:            # to the right
            x1, y1, x2, y2 = ax + aw, ay + ah / 2, bx, by + bh / 2
            mx = (x1 + x2) / 2
            d = f"M {x1 + 3:.1f} {y1:.1f} C {mx:.1f} {y1:.1f}, {mx:.1f} {y2:.1f}, {x2 - 4:.1f} {y2:.1f}"
        else:                        # below
            x1, y1, x2, y2 = ax + aw / 2, ay + ah, bx + bw / 2, by
            d = f"M {x1:.1f} {y1 + 3:.1f} L {x2:.1f} {y2 - 4:.1f}"
        self.o.append(f'  <path d="{d}" fill="none" stroke="{LINE}" stroke-width="2.2" '
                      f'stroke-linecap="round" marker-end="url(#arrow)"/>')

    def wrap(self, a, b):
        """Elbow from the bottom of a back to the top of b on the next row."""
        ax, ay, aw, ah = self._box(a)
        bx, by, bw, bh = self._box(b)
        x1, y1, x2, y2 = ax + aw / 2, ay + ah + 3, bx + bw / 2, by - 4
        my = (y1 + y2) / 2
        self.o.append(f'  <path d="M {x1:.1f} {y1:.1f} V {my:.1f} H {x2:.1f} V {y2:.1f}" fill="none" '
                      f'stroke="{LINE}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" '
                      f'marker-end="url(#arrow)"/>')

    def zone(self, first, last, label):
        """Green panel behind a run of cards: the shared Verify stage."""
        x1, y1, _, h = self._box(first)
        x2 = self._box(last)[0] + self._box(last)[2]
        z = [f'  <rect x="{x1 - 14}" y="{y1 - 38}" width="{x2 - x1 + 28}" height="{h + 52}" rx="16" ry="16" '
             f'fill="#ecfdf5" stroke="{VERIFY}" stroke-width="2" stroke-dasharray="7 5"/>',
             f'  <text x="{x1}" y="{y1 - 14}" {SANS} font-size="13" font-weight="bold" letter-spacing="1" '
             f'fill="{VERIFY}">{esc(label)}</text>']
        self.o[self.under:self.under] = z

    def legend(self):
        x, y = 32, self.h - 20
        for kind in ("data", "script", "ai"):
            border, tint, tag = KIND[kind]
            tw = len(tag) * 8 + 18
            self.o.append(f'  <rect x="{x}" y="{y - 15}" width="{tw}" height="21" rx="6" ry="6" '
                          f'fill="{tint}" stroke="{border}" stroke-width="1.5"/>')
            self.o.append(f'  <text x="{x + tw / 2}" y="{y}" text-anchor="middle" {SANS} font-size="12" '
                          f'font-weight="bold" fill="{border}">{tag}</text>')
            x += tw + 10
        self.o.append(f'  <rect x="{x}" y="{y - 15}" width="66" height="21" rx="10.5" ry="10.5" fill="{VERIFY}"/>')
        self.o.append(f'  <text x="{x + 33}" y="{y}" text-anchor="middle" {SANS} font-size="12" '
                      f'font-weight="bold" fill="#ffffff">Verify</text>')
        self.o.append(f'  <text x="{x + 78}" y="{y}" {SANS} font-size="13" fill="{SUB}">'
                      'Verify = quote check on the fetched page + judge from another model family</text>')

    def svg(self):
        return "\n".join(self.o + ["</svg>"]) + "\n"


def row(c, specs, y, h, w, gap, x0, first_step=None):
    keys = []
    for i, (key, kind, title, lines) in enumerate(specs):
        step = None if first_step is None else first_step + i
        c.card(key, kind, x0 + i * (w + gap), y, w, h, title, lines, step)
        keys.append(key)
    for a, b in zip(keys, keys[1:]):
        c.arrow(a, b)
    return keys


def overview():
    c = Canvas("How the repository works",
               "One build step, two tools, one shared Verify stage, all run by docker-agent on Ollama cloud models.",
               640)
    cx, cw = (40, 276, 512, 760), 200
    c.lane(92, 148, "BUILD   (no model calls)")
    row(c, [("tpl", "data", "Templates", ["`templates/`", "scopes and seeds"]),
            ("gen", "script", "Generate configs", ["`gen-configs.py`"]),
            ("agents", "data", "Agent configs", ["`agents/*.yaml`", "run by docker-agent"])],
        y=124, h=104, w=cw, gap=36, x0=cx[0])
    c.lane(256, 148, "GUARDRAIL POLICY GENERATOR")
    c.lane(420, 148, "DOCS BRIEFING   (Prisma Cloud / Cortex Cloud)")
    c.card("gin", "data", cx[0], 288, cw, 104, "App profile", ["sanitized JSON", "+ 70-control catalog"])
    c.card("gtool", "script", cx[1], 288, cw, 104, "guardrail.py", ["select, propose, check"])
    c.card("gout", "data", cx[3], 288, cw, 104, "Policy folder", ["policy.json, tests", "Bedrock, NeMo drafts"])
    c.card("bin", "data", cx[0], 452, cw, 104, "Question", ["+ official start pages"])
    c.card("btool", "script", cx[1], 452, cw, 104, "run.sh", ["research, write, check"])
    c.card("bout", "data", cx[3], 452, cw, 104, "Briefing", ["cited Markdown", "+ evidence.json"])
    c.card("ver", "verify", cx[2], 288, 212, 268, "Verify", ["quote found on the", "fetched vendor page,", "then judged by",
                                                         "`JUDGE_MODEL`", "(other model family)"])
    for a, b in (("gin", "gtool"), ("gtool", "ver"), ("ver", "gout"),
                 ("bin", "btool"), ("btool", "ver"), ("ver", "bout"), ("agents", "ver")):
        c.arrow(a, b)
    c.legend()
    return c


def guardrail():
    c = Canvas("Guardrail policy generator",
               "scripts/guardrail.py: models propose values; only verified values are marked grounded.", 640)
    w, gap, x0 = 200, 36, 46
    r1 = row(c, [("profile", "data", "App profile", ["sanitized JSON", "+ 70-control catalog"]),
                 ("select", "script", "Select controls", ["`select-controls.py`"]),
                 ("spec", "ai", "Specialists", ["7, one per category", "`SPECIALIST_MODEL`"])],
             y=100, h=104, w=w, gap=gap, x0=x0, first_step=1)
    r2 = row(c, [("values", "script", "Value check", ["type, range, enum"]),
                 ("quote", "script", "Quote check", ["quote on the page"]),
                 ("judge", "ai", "Judge", ["supported?", "`JUDGE_MODEL`"])],
             y=284, h=104, w=w, gap=gap, x0=x0, first_step=4)
    r3 = row(c, [("asm", "ai", "Assembler", ["writes tests", "`REVIEWER_MODEL`"]),
                 ("rev", "ai", "Reviewer", ["findings", "`REVIEWER_MODEL`"]),
                 ("check", "script", "Policy check", ["`check-policy.py`"]),
                 ("out", "data", "Policy folder", ["policy.json, tests", "Bedrock, NeMo"])],
             y=468, h=104, w=w, gap=gap, x0=x0, first_step=7)
    c.wrap(r1[-1], r2[0])
    c.wrap(r2[-1], r3[0])
    c.zone("values", "judge", "VERIFY")
    c.legend()
    return c


def briefing():
    c = Canvas("Docs briefing",
               "scripts/run.sh: a Prisma Cloud / Cortex Cloud question in, a briefing that cites every statement out.",
               640)
    w, gap, x0 = 200, 36, 46
    r1 = row(c, [("q", "data", "Question", ["+ official start pages"]),
                 ("res", "ai", "Researcher", ["facts with quotes", "`RESEARCH_MODEL`"])],
             y=100, h=104, w=w, gap=gap, x0=x0, first_step=1)
    r2 = row(c, [("quote", "script", "Quote check", ["quote on the page"]),
                 ("judge", "ai", "Judge", ["supported?", "`JUDGE_MODEL`"])],
             y=284, h=104, w=w, gap=gap, x0=x0, first_step=3)
    r3 = row(c, [("wri", "ai", "Writer", ["supported facts only", "`WRITER_MODEL`"]),
                 ("chk", "script", "Briefing check", ["`check-briefing.sh`"]),
                 ("out", "data", "Briefing", ["cited Markdown", "+ evidence.json"])],
             y=468, h=104, w=w, gap=gap, x0=x0, first_step=5)
    c.wrap(r1[-1], r2[0])
    c.wrap(r2[-1], r3[0])
    c.zone("quote", "judge", "VERIFY")
    c.legend()
    return c


FILES = (("overview.svg", overview), ("guardrail-flow.svg", guardrail), ("briefing-flow.svg", briefing))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, build in FILES:
        path = OUT_DIR / name
        path.write_text(build().svg(), encoding="ascii", newline="\n")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
