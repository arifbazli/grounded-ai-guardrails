#!/usr/bin/env python3
"""Generate the documentation diagrams as plain SVG (stdlib only).

Usage: python3 scripts/make-diagrams.py

Writes docs/images/*.svg. Output is deterministic: re-running produces
byte-identical files, so commit the result after any change here.

Style: dark solid background (readable in light and dark GitHub themes),
rounded cards with an accent color per kind, numbered steps, tier strip.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "images"
W = 1000
SANS = 'font-family="Arial, Helvetica, sans-serif"'
MONO = 'font-family="Consolas, Menlo, monospace"'

BG = "#0b1020"
CARD = "#131c3a"
INK = "#f1f5f9"
MUTED = "#94a3b8"
EDGE = "#64748b"
# kind -> (accent, tag text)
KIND = {
    "data": ("#94a3b8", "DATA"),
    "script": ("#22d3ee", "SCRIPT"),
    "ai": ("#fbbf24", "CLOUD LLM"),
    "verify": ("#34d399", "SCRIPT + LLM"),
}
CHAR_MONO = 6.8
CHAR_SANS = 6.7


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Canvas:
    def __init__(self, title, subtitle, height):
        self.h = height
        self.out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {height}" '
            f'width="{W}" height="{height}" role="img">',
            f'  <title>{esc(title)}</title>',
            '  <defs>',
            '    <radialGradient id="glow" cx="12%" cy="0%" r="90%">',
            '      <stop offset="0%" stop-color="#312e81" stop-opacity="0.55"/>',
            f'      <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>',
            '    </radialGradient>',
            '    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto">',
            f'      <path d="M 0 1 L 9 5 L 0 9 z" fill="{EDGE}"/>',
            '    </marker>',
            '  </defs>',
            f'  <rect x="0" y="0" width="{W}" height="{height}" fill="{BG}"/>',
            f'  <rect x="0" y="0" width="{W}" height="{height}" fill="url(#glow)"/>',
            f'  <text x="40" y="46" {SANS} font-size="22" font-weight="bold" fill="{INK}">{esc(title)}</text>',
            f'  <text x="40" y="68" {SANS} font-size="13" fill="{MUTED}">{esc(subtitle)}</text>',
        ]
        self.cards = {}

    def card(self, key, kind, x, y, w, h, step, title, lines):
        for text, size, per in [(title, 14, CHAR_SANS)] + [(s, 11, CHAR_MONO) for s in lines]:
            if len(text) * per * size / 12 > w - 28:
                raise SystemExit(f"text overflows card {key!r}: {text!r}")
        accent, tag = KIND[kind]
        self.cards[key] = (x, y, w, h)
        o = self.out
        o.append(f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" ry="14" '
                 f'fill="{CARD}" stroke="{accent}" stroke-opacity="0.65" stroke-width="1.4"/>')
        o.append(f'  <rect x="{x + 14}" y="{y}" width="{w - 28}" height="3" rx="1.5" ry="1.5" fill="{accent}"/>')
        o.append(f'  <circle cx="{x + 24}" cy="{y + 27}" r="11" fill="{accent}"/>')
        o.append(f'  <text x="{x + 24}" y="{y + 31.5}" text-anchor="middle" {SANS} font-size="12" '
                 f'font-weight="bold" fill="{BG}">{step}</text>')
        tw = int(len(tag) * 6.4 + 14)
        o.append(f'  <rect x="{x + w - tw - 12}" y="{y + 17}" width="{tw}" height="19" rx="9.5" ry="9.5" '
                 f'fill="{accent}" fill-opacity="0.16"/>')
        o.append(f'  <text x="{x + w - 12 - tw / 2:.1f}" y="{y + 30}" text-anchor="middle" {SANS} '
                 f'font-size="9" font-weight="bold" letter-spacing="0.6" fill="{accent}">{tag}</text>')
        o.append(f'  <text x="{x + 16}" y="{y + 62}" {SANS} font-size="14" font-weight="bold" '
                 f'fill="{INK}">{esc(title)}</text>')
        for i, line in enumerate(lines):
            o.append(f'  <text x="{x + 16}" y="{y + 82 + 16 * i}" {MONO} font-size="11" '
                     f'fill="{MUTED}">{esc(line)}</text>')

    def arrow(self, a, b):
        ax, ay, aw, ah = self.cards[a]
        bx, by, bw, bh = self.cards[b]
        y = ay + ah / 2
        self.out.append(f'  <path d="M {ax + aw + 4} {y:.1f} L {bx - 4} {y:.1f}" fill="none" stroke="{EDGE}" '
                        f'stroke-width="2" stroke-linecap="round" marker-end="url(#arrow)"/>')

    def wrap_arrow(self, a, b):
        """Elbow from the bottom of a, left across the gap, to the top of b."""
        ax, ay, aw, ah = self.cards[a]
        bx, by, bw, bh = self.cards[b]
        x1, y1 = ax + aw / 2, ay + ah + 4
        x2, y2 = bx + bw / 2, by - 4
        my = (y1 + y2) / 2
        self.out.append(f'  <path d="M {x1:.1f} {y1:.1f} L {x1:.1f} {my:.1f} L {x2:.1f} {my:.1f} '
                        f'L {x2:.1f} {y2:.1f}" fill="none" stroke="{EDGE}" stroke-width="2" '
                        f'stroke-linecap="round" stroke-linejoin="round" marker-end="url(#arrow)"/>')

    def tiers(self, y):
        self.out.append(f'  <text x="40" y="{y}" {SANS} font-size="11" font-weight="bold" '
                        f'letter-spacing="1.2" fill="{MUTED}">EVERY CONTROL ENDS IN ONE TIER</text>')
        items = (("#34d399", "grounded", "vendor quote found, judged SUPPORTED"),
                 ("#fbbf24", "catalog-default", "opinionated baseline, not vendor-backed"),
                 ("#94a3b8", "excluded", "not applicable here, reason recorded"))
        w, gap = 288, 24
        for i, (color, name, text) in enumerate(items):
            x = 40 + i * (w + gap)
            self.out.append(f'  <rect x="{x}" y="{y + 14}" width="{w}" height="64" rx="12" ry="12" '
                            f'fill="{CARD}" stroke="{color}" stroke-opacity="0.65" stroke-width="1.4"/>')
            self.out.append(f'  <circle cx="{x + 22}" cy="{y + 36}" r="6" fill="{color}"/>')
            self.out.append(f'  <text x="{x + 38}" y="{y + 41}" {SANS} font-size="14" font-weight="bold" '
                            f'fill="{INK}">{name}</text>')
            if len(text) * 6.3 > w - 28:
                raise SystemExit(f"tier text overflows: {text!r}")
            self.out.append(f'  <text x="{x + 16}" y="{y + 63}" {SANS} font-size="11.5" '
                            f'fill="{MUTED}">{esc(text)}</text>')

    def legend(self):
        x, y = 40, self.h - 22
        for kind in ("data", "script", "ai", "verify"):
            accent, tag = KIND[kind]
            self.out.append(f'  <circle cx="{x + 5}" cy="{y - 4}" r="5" fill="{accent}"/>')
            self.out.append(f'  <text x="{x + 16}" y="{y}" {SANS} font-size="11" fill="{MUTED}">{tag.lower()}</text>')
            x += 28 + len(tag) * 7
        self.out.append(f'  <text x="{x + 10}" y="{y}" {SANS} font-size="11" fill="{MUTED}">'
                        'model setting names (for example JUDGE_MODEL) are shown on each LLM step</text>')

    def svg(self):
        return "\n".join(self.out + ["</svg>"]) + "\n"


def row(c, keys_specs, y, h, w=156, gap=30, x0=50, first_step=1):
    keys = []
    for i, (key, kind, title, lines) in enumerate(keys_specs):
        c.card(key, kind, x0 + i * (w + gap), y, w, h, first_step + i, title, lines)
        keys.append(key)
    for a, b in zip(keys, keys[1:]):
        c.arrow(a, b)
    return keys


def overview():
    c = Canvas("From app profile to a grounded policy",
               "Models propose. Scripts and a second model verify. Nothing unverified is shown as vendor-backed.",
               430)
    row(c, [
        ("profile", "data", "App profile", ["sanitized JSON", "no secrets"]),
        ("select", "script", "Select controls", ["select-controls.py", "70-control catalog"]),
        ("propose", "ai", "Propose values", ["7 specialists", "SPECIALIST_MODEL"]),
        ("verify", "verify", "Verify", ["value check", "quote on the page", "JUDGE_MODEL"]),
        ("out", "data", "Policy folder", ["policy.json", "tests, reports", "Bedrock, NeMo"]),
    ], y=96, h=124)
    c.tiers(262)
    c.legend()
    return c


def guardrail():
    c = Canvas("Guardrail policy generator",
               "scripts/guardrail.py: ten steps, from a sanitized profile to an advisory policy.", 490)
    top = row(c, [
        ("profile", "data", "App profile", ["sanitized JSON", "no secrets"]),
        ("select", "script", "Select controls", ["select-controls.py", "70-control catalog"]),
        ("spec", "ai", "7 specialists", ["one per category", "SPECIALIST_MODEL"]),
        ("values", "script", "Value check", ["type, range, enum", "number in quote"]),
        ("quote", "script", "Quote check", ["quote on fetched", "vendor page"]),
    ], y=92, h=120)
    bottom = row(c, [
        ("judge", "ai", "Judge", ["other model family", "JUDGE_MODEL"]),
        ("asm", "ai", "Assembler", ["writes tests", "REVIEWER_MODEL"]),
        ("rev", "ai", "Reviewer", ["review.json", "REVIEWER_MODEL"]),
        ("check", "script", "Policy check", ["check-policy.py", "schema, tiers, tests"]),
        ("files", "data", "Outputs", ["policy.json, tests", "exceptions.md", "Bedrock, NeMo"]),
    ], y=272, h=120, first_step=6)
    c.wrap_arrow(top[-1], bottom[0])
    c.legend()
    return c


def briefing():
    c = Canvas("Docs briefing",
               "scripts/run.sh: a Prisma Cloud / Cortex Cloud question in, a source-cited briefing out.", 290)
    row(c, [
        ("q", "data", "Question", ["run.sh \"...\"", "start pages: seeds/"]),
        ("res", "ai", "Researcher", ["facts and quotes", "RESEARCH_MODEL"]),
        ("ver", "verify", "Verify", ["quote on the page", "JUDGE_MODEL"]),
        ("wri", "ai", "Writer", ["supported facts only", "WRITER_MODEL"]),
        ("out", "data", "Briefing", ["check-briefing.sh", "outputs/<run>.md"]),
    ], y=96, h=124)
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
