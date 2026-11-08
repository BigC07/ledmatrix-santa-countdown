"""Santa's Countdown: the scenes.

Every scene is a pure function of (days, phase, width): the same arguments
always give the same pixels, so a frame can be redrawn from any thread and
tested without a display. `phase` is an integer animation step; each scene
cycles its moving parts on it (legs, a blinking nose, falling snow, chasing
lights, elves tossing presents), and the caller decides how fast it advances.

All the art is drawn here, in code: no image files.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

H = 32  # every scene is drawn 32 rows high; the plugin scales for taller panels

# ── palette ────────────────────────────────────────────────────────────────
PAL = {
    "R": (220, 0, 0), "r": (120, 0, 0), "W": (255, 255, 255), "w": (190, 190, 200),
    "S": (255, 190, 150), "k": (0, 0, 0), "Y": (255, 200, 0), "y": (180, 130, 0),
    "B": (130, 75, 30), "b": (95, 55, 20), "T": (200, 160, 100), "N": (255, 30, 30),
    "n": (110, 0, 0), "G": (0, 170, 0), "g": (0, 110, 0), "O": (255, 120, 0),
    "P": (200, 0, 200), "C": (0, 160, 255), "L": (230, 150, 70),
}
BULBS = [PAL["R"], PAL["G"], PAL["Y"], PAL["C"], PAL["P"], PAL["O"]]
WHITE, GOLD, GREEN, RED = (255, 255, 255), (255, 200, 0), (0, 200, 0), (255, 0, 0)

# ── fonts ──────────────────────────────────────────────────────────────────
_FONT_NAME = "PressStart2P-Regular.ttf"
_fonts: Dict[int, ImageFont.ImageFont] = {}


def _font_path() -> Optional[Path]:
    here = Path(__file__).resolve().parent
    for base in (Path.cwd(), here.parent.parent, here.parent.parent.parent):
        p = base / "assets" / "fonts" / _FONT_NAME
        if p.exists():
            return p
    return None


def font(size: int) -> ImageFont.ImageFont:
    if size not in _fonts:
        path = _font_path()
        try:
            _fonts[size] = ImageFont.truetype(str(path), size) if path else ImageFont.load_default()
        except OSError:
            _fonts[size] = ImageFont.load_default()
    return _fonts[size]


# ── sprites ────────────────────────────────────────────────────────────────
_sprite_cache: Dict[Tuple[str, ...], Image.Image] = {}


def sprite(rows: List[str], subs: Optional[Dict[str, Tuple[int, int, int]]] = None) -> Image.Image:
    key = tuple(rows) + tuple(sorted((subs or {}).items()))
    im = _sprite_cache.get(key)
    if im is None:
        pal = dict(PAL, **(subs or {}))
        w = max(len(r) for r in rows)
        im = Image.new("RGBA", (w, len(rows)), (0, 0, 0, 0))
        px = im.load()
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch in pal:
                    px[x, y] = tuple(pal[ch]) + (255,)
        _sprite_cache[key] = im
    return im


def paste(img: Image.Image, sp: Image.Image, x: int, y: int) -> None:
    img.paste(sp, (x, y), sp)


_DEER_TOP = [
    "..........T.T...",
    "...........TT...",
    "..........TTTT..",
    "..........bbb..q",
    "..........bkbbNN",
    "...........bb..q",
    "W.bbbbbbbbbbb...",
    ".bbbbbbbbbbbb...",
    "..bbbbbbbbbb....",
]
DEER_LEGS = (
    ["..b.b....b.b....",
     ".b...b..b...b..."],      # stretched out, mid-gallop
    ["...bb.....bb....",
     "...b.b....b.b..."],      # tucked
)

SLEIGH_BODY = [
    "Y.....................Y.",
    "YYYYYYYYYYYYYYYYYYYYYYY.",
    "RRRRRRRRRRRRRRRRRRRRRR..",
    ".RRRRRRRRRRRRRRRRRRRR...",
    "..RRRRRRRRRRRRRRRRRR....",
    "...Y...........Y........",
    "YYYYYYYYYYYYYYYYYYYYYYY.",
    ".......................Y",
]
# A big Santa ("make him bigger", 2026-11-08): 8 wide, 12 rows, facing the
# reindeer, his belt on the sleigh's rim.
SANTA = [
    ".W......",
    ".RR.....",
    "..RRR...",
    "..RRRR..",
    ".WWWWWW.",
    ".SSSSkS.",
    ".SSSSSS.",
    "WWWWWWWW",
    ".WWWWWW.",
    "RRWWWWRR",
    "RRRRRRRR",
    "bbbYYbbb",
]
# His waving arm, (x, y, char) over SANTA: up, the hand swinging in, then out.
SANTA_WAVE = (
    [(8, 10, "R"), (9, 9, "R"), (9, 8, "R"), (9, 7, "R"), (9, 6, "S"), (10, 6, "S")],
    [(8, 10, "R"), (9, 9, "R"), (10, 8, "R"), (11, 7, "R"), (11, 6, "S"), (12, 6, "S")],
)
#: Santa sits forward of the tower of presents with a gap ("move Santa up in
#: the sleigh just a little bit, not attached to the packages").
SANTA_X = 10
SLEIGH_RIM = len(SANTA) - 1      # the body's first row, in the sleigh sprite


# The tower, bottom to top: (width, height, box, ribbon). 21 rows of presents.
TOWER = ((7, 5, PAL["G"], PAL["R"]), (6, 4, PAL["C"], WHITE), (7, 3, PAL["P"], PAL["Y"]),
         (5, 3, PAL["R"], WHITE), (6, 3, PAL["Y"], PAL["R"]), (4, 3, PAL["G"], WHITE))


def present_tower(img: Image.Image, x: int, base: int, phase: int) -> None:
    """Presents stacked from row `base` up, in the back of the sleigh; the top
    three boxes teeter a pixel or two to the side on alternate steps."""
    d = ImageDraw.Draw(img)
    y = base
    for i, (w, h, box, rib) in enumerate(TOWER):
        lean = (0, 0, 0, 1, 1, 2)[i] if phase % 2 else 0
        bx = x + (7 - w) // 2 + lean
        top = y - h + 1
        d.rectangle([bx, top, bx + w - 1, y], fill=box)
        cx = bx + w // 2
        d.line([(cx, top), (cx, y)], fill=rib)
        d.line([(bx, top + h // 2), (bx + w - 1, top + h // 2)], fill=rib)
        y = top - 1
    cx = x + 3 + (2 if phase % 2 else 0)
    d.point([(cx - 1, y), (cx + 1, y), (cx, y)], fill=PAL["Y"])     # a bow on top


def sleigh(pose: int) -> Image.Image:
    """The sleigh with Santa in it, waving: 24 wide, the rim on row SLEIGH_RIM."""
    santa = [list(r) + ["."] * 6 for r in SANTA]
    for x, y, ch in SANTA_WAVE[pose % 2]:
        santa[y][x] = ch
    rows = [["."] * 24 for _ in range(SLEIGH_RIM)] + [list(r) for r in SLEIGH_BODY]
    for y, row in enumerate(santa):
        for x, ch in enumerate(row):
            if ch != "." and SANTA_X + x < 24:
                rows[y][SANTA_X + x] = ch
    return sprite(["".join(r) for r in rows])

SNOWMAN = [
    "....kkkkk....",
    "....kkkkk....",
    "...kkkkkkk...",
    "....WWWWW....",
    "...WkWWWkW...",
    "...WWWOOOW...",
    "....WWWWW....",
    "...RRRRRRR...",
    "....WWWRRW...",
    "..WWWWkWWRW..",
    "..WWWWWWWWW..",
    "..WWWWkWWWW..",
    "..WWWWWWWWW..",
    "...WWWWWWW...",
    "..WWWWWWWWW..",
    ".WWWWWkWWWWW.",
    ".WWWWWWWWWWW.",
    ".WWWWWWWWWWW.",
    "..WWWWWWWWW..",
    "...WWWWWWW...",
]

GINGER_TOP = [
    "....LLLL....",
    "...LLLLLL...",
    "...LkLLkL...",
    "...LLLLLL...",
    "...LWWWWL...",
    "....LLLL....",
]
GINGER_ARMS = (
    ["LLLLLLLLLLLL",
     "LWLLLRLLLLWL"],          # arms out
    ["W..LLLLLL..W",
     "LLLLLRLLLLLL"],          # arms up, waving
)
GINGER_BODY = [
    "...LLLLLL...",
    "...LLRLLL...",
    "...LLLLLL...",
    "...LLRLLL...",
    "..LLL..LLL..",
    "..LL....LL..",
    ".WLL....LLW.",
    ".LL......LL.",
]


ELF_HAT = (
    ["........Y..",
     ".......GG..",
     "......GGG..",
     ".....GGG...",
     "....GGGG...",
     "...GGGGGG..",
     "..WWWWWWW.."],
    [".........Y.",
     "........GG.",
     "......GGG..",
     ".....GGG...",
     "....GGGG...",
     "...GGGGGG..",
     "..WWWWWWW.."],           # the hat's tip swings and the bell jingles
)
ELF_FACE = [
    "..SSSSSSS..",
    "SSSkSSSkSSS",             # pointy ears
    "..SSSRSSS..",
    "...SSSSS...",
]
ELF_BODY = (
    ["..GGGYGGG..",
     ".GGGGGGGGG.",
     "SGGGGYGGGGS",            # hands down
     ".GkkkYkkkG."],
    ["SGGGGYGGGGS",            # hands up, catching
     ".GGGGGGGGG.",
     ".GGGGYGGGG.",
     ".GkkkYkkkG."],
)
ELF_LEGS = [
    "..GGGGGGG..",
    "..RR...RR..",
    "..WW...WW..",
    "..RR...RR..",
    ".bbb...bbb.",
]


def elf(pose: int) -> Image.Image:
    return sprite(ELF_HAT[pose % 2] + ELF_FACE + ELF_BODY[pose % 2] + ELF_LEGS)


RUDOLPH = (255, 0, 0)          # full red, always lit: a dim blink step vanished on the panel
RUDOLPH_GLOW = (255, 110, 90)


def reindeer(pose: int, rudolph: bool = False, glow: bool = False) -> Image.Image:
    """A reindeer; Rudolph has a 2-pixel nose that is always lit, with a glow
    above and below it that blinks."""
    rows = _DEER_TOP + DEER_LEGS[pose % 2]
    if not rudolph:
        return sprite([r.replace("N", "k").replace("q", ".") for r in rows])
    if not glow:
        rows = [r.replace("q", ".") for r in rows]
    return sprite(rows, {"N": RUDOLPH, "q": RUDOLPH_GLOW})


def snowman(wave: int) -> Image.Image:
    rows = list(SNOWMAN)
    if wave % 2:
        rows[7] = "...RRRRRRR.B"     # right arm raised
        rows[8] = "....WWWRRWB."
        rows[10] = "B.WWWWWWWWW.."
        rows[11] = ".BWWWWkWWWW.."
    else:
        rows[10] = "B.WWWWWWWWW.B"
        rows[11] = ".BWWWWkWWWWB."
    return sprite(rows)


def gingerbread(pose: int) -> Image.Image:
    return sprite(GINGER_TOP + GINGER_ARMS[pose % 2] + GINGER_BODY)


# ── texture: stars, snow ───────────────────────────────────────────────────
# Drawn LAST, over the finished card, and only where the card is dark for a
# pixel all round: so the sky fills the whole width, including between and
# after the words, and never touches a letter or the art. (Drawn first, the
# words' cleared margin wiped it from the words to the edge -- "some of the
# snow was just on half the card", 2026-11-08.)
def _clear_around(base, w: int, x: int, y: int) -> bool:
    if not (0 <= x < w and 0 <= y < H):
        return False
    for yy in range(max(0, y - 1), min(H, y + 2)):
        for xx in range(max(0, x - 1), min(w, x + 2)):
            if base[xx, yy] != (0, 0, 0):
                return False
    return True


def stars(img: Image.Image, n: int, seed: int, phase: int) -> None:
    rnd = random.Random(seed)
    base = img.copy().load()
    px = img.load()
    w = img.width
    for i in range(n):
        x, y = rnd.randrange(w), rnd.randrange(H)
        if _clear_around(base, w, x, y):
            v = (60, 120, 200)[(i + phase) % 3]
            px[x, y] = (v, v, v)


def snow(img: Image.Image, n: int, seed: int, phase: int, floor: int = H) -> None:
    rnd = random.Random(seed)
    base = img.copy().load()
    px = img.load()
    w = img.width
    for _ in range(n):
        x0, y0 = rnd.randrange(w), rnd.randrange(floor)
        big = rnd.random() < 0.2
        drift = rnd.choice((-1, 0, 1))
        y = (y0 + phase * (2 if big else 1)) % floor
        x = (x0 + drift * (phase // 2)) % w
        if big:
            dots, colour = [(x, y), (x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], (200, 220, 255)
        else:
            dots, colour = [(x, y)], (220, 230, 255)
        for dx, dy in dots:
            if _clear_around(base, w, dx, dy):
                px[dx, dy] = colour


# ── text ───────────────────────────────────────────────────────────────────
def _draw(img: Image.Image) -> ImageDraw.ImageDraw:
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    return d


def text_width(s: str, size: int) -> int:
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    return int(d.textlength(s, font=font(size)))


class Words:
    """What a scene says: the count (or the day itself) and two short lines.

    Three sizes, tried in order until one fits beside the art: the number with
    both lines (0), the number with one word (1), the number alone (2).
    """

    def __init__(self, days: int, top: str, bottom: str):
        self.days = days
        if days <= 0:
            self.big, self.top, self.bottom, self.word = "", "MERRY", "CHRISTMAS!", "XMAS!"
        else:
            self.big = str(days)
            self.top = top if days != 1 else top.replace("DAYS", "DAY")
            self.bottom = bottom
            self.word = "DAY" if days == 1 else "DAYS"

    def _lines(self, level: int) -> List[str]:
        if level == 0:
            return [self.top, self.bottom]
        if level == 1 or not self.big:
            return [self.word]
        return []

    def width(self, level: int = 0) -> int:
        big = text_width(self.big, 16) if self.big else 0
        lines = self._lines(level)
        gap = 5 if big and lines else 0
        return big + gap + max([text_width(t, 8) for t in lines] or [0])

    def draw(self, img: Image.Image, x: int, colours, level: int = 0) -> int:
        """Clears a margin round the words, draws them at x; returns the right edge.

        colours = (big, top, bottom)."""
        right = x + self.width(level)
        ImageDraw.Draw(img).rectangle([x - 2, 4, right + 1, 28], fill=(0, 0, 0))
        d = _draw(img)
        if self.big:
            d.text((x, 8), self.big, font=font(16), fill=colours[0])
            x += text_width(self.big, 16) + 5
        lines = self._lines(level)
        if len(lines) == 2:
            d.text((x, 7), lines[0], font=font(8), fill=colours[1])
            d.text((x, 18), lines[1], font=font(8), fill=colours[2])
        elif lines:
            d.text((x, 12), lines[0], font=font(8), fill=colours[1])
        return right


def place_words(img: Image.Image, words: Words, art_right: int, colours) -> int:
    """The words after the art, as large as fits; the number over the art if nothing does.

    Returns the words' right edge."""
    w = img.width
    for level in (0, 1, 2):
        if art_right + 6 + words.width(level) <= w:
            return words.draw(img, art_right + 6, colours, level)
    return words.draw(img, max(2, w - words.width(2) - 1), colours, 2)


def spare(img: Image.Image, right: int, need: int, count: int = 1, gap: int = 4) -> List[int]:
    """Where up to `count` decorations `need` wide fit after `right`, centred in
    the space left on the card. Empty when not even one fits: the owner's
    complaint was a black right-hand side, so every scene fills it when it can.
    """
    room = img.width - right - 2
    n = min(count, (room + gap) // (need + gap)) if room >= need else 0
    if n <= 0:
        return []
    span = n * need + (n - 1) * gap
    x0 = right + 1 + (room - span) // 2
    return [x0 + i * (need + gap) for i in range(n)]


def light_string(img: Image.Image, phase: int, bottom: bool = False) -> None:
    """A string of bulbs across the card, chasing; along the bottom it hangs upward."""
    d = ImageDraw.Draw(img)
    w = img.width
    sag = [1 + int(2.5 * (1 - abs(((x % 32) - 16) / 16.0))) for x in range(w)]
    ys = [H - 1 - y for y in sag] if bottom else sag
    d.line(list(zip(range(w), ys)), fill=(0, 90, 0))
    shift = 3 if bottom else 0
    for i, x in enumerate(range(4, w, 8)):
        on = (i + phase + shift) % 3 != 0
        c = BULBS[(i + phase + shift) % len(BULBS)] if on else (40, 40, 40)
        y = ys[x]
        if bottom:
            d.rectangle([x, y - 3, x + 1, y - 1], fill=c)
        else:
            d.rectangle([x, y + 1, x + 1, y + 3], fill=c)


# ── the scenes ─────────────────────────────────────────────────────────────
def scene_sleigh(days: int, phase: int, width: int) -> Image.Image:
    img = Image.new("RGB", (width, H))
    words = Words(days, "DAYS", "TILL CHRISTMAS")
    team = 4 if width >= 192 else (1 if width >= 96 else 0)
    x = 2
    sleigh_y = 15 + (phase % 2)
    paste(img, sleigh(phase), x, sleigh_y + 7 - SLEIGH_RIM)   # the rim stays on sleigh_y + 7
    present_tower(img, x, sleigh_y + 6, phase)
    right = x + 24
    if team:
        dx = x + 26
        last = None
        for i in range(team):
            rudolph = i == team - 1
            y = 13 - i * 2 + ((phase + i) % 2)
            paste(img, reindeer(phase + i, rudolph, phase % 2 == 0), dx, y)
            last = (dx, y)
            dx += 17
        d = ImageDraw.Draw(img)
        d.line([(x + 22, sleigh_y + 7), (last[0] + 12, last[1] + 7)], fill=PAL["y"])
        right = dx
    place_words(img, words, right, (GOLD, WHITE, GREEN))
    if width >= 192:  # the moon, after the words: their margin would bite it
        d = ImageDraw.Draw(img)
        d.ellipse([width - 18, 2, width - 5, 15], fill=(255, 240, 170))
        d.ellipse([width - 22, 0, width - 9, 13], fill=(0, 0, 0))
    stars(img, width // 6, 1, phase)
    return img


def scene_snowman(days: int, phase: int, width: int) -> Image.Image:
    img = Image.new("RGB", (width, H))
    words = Words(days, "SNOWY DAYS", "TILL CHRISTMAS")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 30, width - 1, 31], fill=(235, 240, 255))    # the ground, not a snow colour
    paste(img, snowman(phase), 4, 10)
    right = 18
    place_words(img, words, right, ((0, 200, 255), WHITE, (0, 200, 255)))
    if width >= 192:
        paste(img, snowman(phase + 1), width - 17, 10)
    snow(img, width // 4, 2, phase, floor=29)
    return img


def _tree(img: Image.Image, x: int, phase: int) -> int:
    """A tree with blinking ornaments and a twinkling star; returns its right edge."""
    d = ImageDraw.Draw(img)
    cx = x + 11
    for top, half, bottom in ((4, 5, 11), (8, 8, 18), (13, 11, 27)):
        d.polygon([(cx, top), (cx - half, bottom), (cx + half, bottom)], fill=PAL["G"])
    d.rectangle([cx - 2, 28, cx + 2, 31], fill=PAL["B"])
    star = PAL["Y"] if phase % 2 == 0 else WHITE
    d.point([(cx, 1), (cx - 1, 2), (cx, 2), (cx + 1, 2), (cx, 3)], fill=star)
    spots = [(cx - 1, 8), (cx + 2, 12), (cx - 4, 15), (cx + 4, 17), (cx - 6, 22),
             (cx + 1, 21), (cx + 7, 24), (cx - 2, 25)]
    for i, (sx, sy) in enumerate(spots):
        c = BULBS[(i + phase) % len(BULBS)]
        d.rectangle([sx, sy, sx + 1, sy + 1], fill=c)
    return x + 23


def _present(img: Image.Image, x: int, w: int, h: int, box, ribbon, lift: int) -> None:
    d = ImageDraw.Draw(img)
    top = H - h - lift
    d.rectangle([x, top, x + w - 1, H - 1 - lift], fill=box)
    cx = x + w // 2
    d.rectangle([cx - 1, top, cx, H - 1 - lift], fill=ribbon)
    d.rectangle([x, top + h // 2, x + w - 1, top + h // 2 + 1], fill=ribbon)
    d.point([(cx - 3, top - 2), (cx - 2, top - 1), (cx + 2, top - 2), (cx + 1, top - 1),
             (cx - 2, top - 3), (cx + 1, top - 3)], fill=ribbon)


PRESENTS = ((12, 10, PAL["R"], PAL["Y"]), (9, 14, PAL["C"], WHITE),
            (14, 7, PAL["G"], PAL["R"]), (8, 9, PAL["P"], PAL["Y"]))


def scene_presents(days: int, phase: int, width: int) -> Image.Image:
    img = Image.new("RGB", (width, H))
    words = Words(days, "DAYS", "TILL PRESENTS!")
    x = _tree(img, 2, phase) + 1
    count = 4 if width >= 192 else (2 if width >= 96 else 0)
    for i, (w, h, box, rib) in enumerate(PRESENTS[:count]):
        _present(img, x, w, h, box, rib, 2 if phase % count == i else 0)
        x += w + 1
    right = place_words(img, words, x, (RED, WHITE, GREEN))
    for tx in spare(img, right, 23):
        _tree(img, tx, phase + 1)
    stars(img, width // 10, 3, phase)
    return img


def scene_gingerbread(days: int, phase: int, width: int) -> Image.Image:
    img = Image.new("RGB", (width, H))
    words = Words(days, "DAYS", "TILL CHRISTMAS")
    count = 3 if width >= 192 else 1
    x = 4
    for i in range(count):
        up = (phase + i) % 2
        paste(img, gingerbread(phase + i), x, 10 - 2 * up)
        x += 16
    right = place_words(img, words, x - 2, (PAL["L"], WHITE, PAL["L"]))
    for j, gx in enumerate(spare(img, right, 12, count=3)):
        up = (phase + j + 1) % 2
        paste(img, gingerbread(phase + j + 1), gx, 10 - 2 * up)
    stars(img, width // 6, 4, phase)
    return img


def scene_lights(days: int, phase: int, width: int) -> Image.Image:
    """Lights along the top and bottom, the number flashing colours digit by
    digit, and the words stretched to the right edge, every letter flashing."""
    img = Image.new("RGB", (width, H))
    light_string(img, phase)
    light_string(img, phase, bottom=True)
    d = _draw(img)
    if days <= 0:
        line, big = "MERRY CHRISTMAS!", ""
    else:
        big = str(days)
        line = ("DAY" if days == 1 else "DAYS") + " TILL CHRISTMAS"
    x = 4
    for j, ch in enumerate(big):
        d.text((x, 8), ch, font=font(16), fill=BULBS[(phase * 2 + j * 3) % len(BULBS)])
        x += text_width(ch, 16)
    if big:
        x += 6
    if x + text_width(line, 8) > width:
        line = line.split(" TILL")[0] if big else "XMAS!"
    if x + text_width(line, 8) > width:
        line = ""
    if not line:
        return img
    # Stretch the line to end 3px from the edge: the spare room goes between
    # the letters, so the words fill the card.
    chars = list(line)
    gaps = max(1, len(chars) - 1)
    spare_px = min(max(0, width - 3 - x - text_width(line, 8)), 6 * gaps)
    i = phase
    for n, ch in enumerate(chars):
        cx = x + sum(text_width(c, 8) for c in chars[:n]) + spare_px * n // gaps
        if ch != " ":
            d.text((cx, 12), ch, font=font(8), fill=BULBS[i % len(BULBS)])
            i += 1
    return img


BOOT = (110, 110, 120)   # grey, not black: black is an unlit LED and the boots vanished


def _santa_legs(d: ImageDraw.ImageDraw, x: int, phase: int) -> None:
    """Santa stuck in a chimney whose top is x..x+11 at row 15: his coat at the
    rim and both legs in the air, kicking in turn -- one up while the other
    drops 4 rows."""
    d.rectangle([x + 1, 11, x + 10, 14], fill=PAL["R"])         # his coat
    d.rectangle([x + 1, 14, x + 10, 14], fill=WHITE)            # fur trim
    for j, lx in enumerate((x + 2, x + 7)):
        top = 0 if (phase + j) % 2 == 0 else 4
        d.rectangle([lx, top + 3, lx + 2, 11], fill=PAL["R"])    # trousers
        d.rectangle([lx, top + 2, lx + 2, top + 2], fill=WHITE)  # cuff
        d.rectangle([lx, top, lx + 2, top + 1], fill=BOOT)       # boot
        toe = lx - 1 if j == 0 else lx + 3                       # toes point out
        d.point((toe, top + 1), fill=BOOT)


def scene_chimney(days: int, phase: int, width: int) -> Image.Image:
    img = Image.new("RGB", (width, H))
    words = Words(days, "DAYS", "TILL SANTA COMES!")
    d = ImageDraw.Draw(img)
    hw = 44 if width >= 128 else 30                 # the house, small so Santa reads
    cx = 27 if hw == 44 else 14                     # the chimney's left edge
    brick, mortar = (170, 60, 40), (110, 40, 30)
    d.rectangle([cx, 16, cx + 11, 27], fill=brick)
    for yy in (19, 22, 25):
        d.line([(cx, yy), (cx + 11, yy)], fill=mortar)
    apex = hw // 2
    d.polygon([(0, 31), (0, 27), (apex, 19), (hw, 27), (hw, 31)], fill=(120, 30, 30))
    d.line([(0, 27), (apex, 19), (hw, 27)], fill=WHITE)
    glow = (255, 200, 80) if phase % 4 else (255, 170, 60)
    wx = 7 if hw == 44 else 5
    d.rectangle([wx, 27, wx + 6, 31], fill=glow)
    d.line([(wx + 3, 27), (wx + 3, 31)], fill=(120, 30, 30))
    d.line([(wx, 29), (wx + 6, 29)], fill=(120, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([cx - 1, 15, cx + 12, 16], fill=WHITE)          # snow on the rim
    _santa_legs(d, cx, phase)
    right = place_words(img, words, max(hw, cx + 13) + 2, (RED, WHITE, GOLD))
    for mx in spare(img, right, 12):
        d = ImageDraw.Draw(img)
        d.ellipse([mx, 4, mx + 11, 15], fill=(255, 240, 170))
        d.ellipse([mx - 4, 2, mx + 7, 13], fill=(0, 0, 0))
    snow(img, width // 6, 5, phase)
    return img


def scene_elves(days: int, phase: int, width: int) -> Image.Image:
    img = Image.new("RGB", (width, H))
    words = Words(days, "DAYS", "ELVES ARE BUSY!")
    count = 3 if width >= 192 else 1
    x = 3
    gifts = ((PAL["R"], PAL["Y"]), (PAL["C"], WHITE))
    for i in range(count):
        hop = (phase + i) % 2
        paste(img, elf(phase + i), x, 10 - 2 * hop)
        x += 12
        if i < count - 1:
            # a present tossed between two elves: up on one step, down the next
            box, rib = gifts[i % 2]
            up = 8 if (phase + i) % 2 else 2
            _present(img, x, 8, 7, box, rib, up)
            x += 10
    right = place_words(img, words, x, (PAL["G"], WHITE, PAL["R"]))
    spot = spare(img, right, 12)
    if spot:
        ex = spot[0]
        hop = (phase + 1) % 2
        paste(img, elf(phase + 1), ex, 10 - 2 * hop)
        _throw(img, x - 2, ex - 3, phase)
    snow(img, width // 8, 6, phase)
    return img


THROW_STEPS = 8   # steps for one throw across the card; then the next present


def _throw(img: Image.Image, left: int, right: int, phase: int) -> None:
    """A present thrown in a high arc from the left elves to the elf on the right,
    over the words. Always left to right: each throw is a new present, in the
    next colour (the owner, 2026-11-08: "throw the package from the left to the
    right elf")."""
    k = phase % THROW_STEPS
    t = k / (THROW_STEPS - 1)
    box, rib = THROWN[(phase // THROW_STEPS) % len(THROWN)]
    x = int(round(left + (right - left) * t))
    lift = int(round(4 + 22 * math.sin(math.pi * t)))   # the present's bottom, rows up
    _present(img, x - 3, 7, 6, box, rib, min(lift, H - 9))


THROWN = ((PAL["P"], PAL["Y"]), (PAL["R"], WHITE), (PAL["C"], PAL["Y"]), (PAL["Y"], PAL["R"]))


# ── the workshop: elves building a present, one step at a time ────────────
BUILD_STEPS = 8   # bottom, sides, box, lid, ribbon down, ribbon across, bow, done
WOOD, WOOD_DARK = (150, 90, 40), (100, 60, 25)
HAMMER_HEAD = (150, 150, 160)
BUILT = ((PAL["R"], PAL["Y"]), (PAL["C"], WHITE), (PAL["G"], PAL["R"]), (PAL["P"], PAL["Y"]))


def _build(d: ImageDraw.ImageDraw, x: int, phase: int) -> None:
    """The present on the bench, x..x+11, its bottom on row 24, as far along as
    this step of the build."""
    k = phase % BUILD_STEPS
    box, rib = BUILT[(phase // BUILD_STEPS) % len(BUILT)]
    w, full = 12, 9
    h = (2, 5, full, full, full, full, full, full)[k]
    top = 25 - h
    d.rectangle([x, top, x + w - 1, 24], fill=box)
    if k >= 3:                                   # the lid
        lid = tuple(min(255, c + 70) for c in box)
        d.rectangle([x - 1, top, x + w, top + 1], fill=lid)
    cx = x + w // 2
    if k >= 4:                                   # ribbon down
        d.rectangle([cx - 1, top, cx, 24], fill=rib)
    if k >= 5:                                   # ribbon across
        d.rectangle([x, top + 4, x + w - 1, top + 5], fill=rib)
    if k >= 6:                                   # the bow
        d.point([(cx - 3, top - 2), (cx - 2, top - 1), (cx + 2, top - 2), (cx + 1, top - 1),
                 (cx - 2, top - 3), (cx + 1, top - 3), (cx - 1, top - 1), (cx, top - 1)], fill=rib)
    if k == 7:                                   # done: it sparkles
        d.point([(x - 3, top - 2), (x + w + 2, top - 1), (x - 2, top + 4),
                 (x + w + 3, top + 5), (cx, top - 6)], fill=WHITE)


def _hammer(d: ImageDraw.ImageDraw, phase: int, box_x: int, box_top: int) -> None:
    """The left elf's hammer: raised over his shoulder on one step, and on the
    next swung level into the side of the box, sparks flying where it lands."""
    steel, steel_dark = (185, 185, 195), (120, 120, 130)
    if phase % 2:
        # raised: hands up at row 22, the handle tilted back, the head on top
        d.line([(11, 21), (14, 15)], fill=WOOD)
        d.line([(12, 21), (15, 15)], fill=WOOD_DARK)
        d.rectangle([12, 12, 18, 14], fill=steel)
        d.rectangle([12, 14, 18, 14], fill=steel_dark)
    else:
        # striking: hands down at row 24, the handle level, the head on the box
        y = min(max(box_top + 1, 18), 21)     # above the bench (row 25), even for a low box
        d.line([(12, y + 1), (box_x - 5, y + 1)], fill=WOOD)
        d.rectangle([box_x - 4, y - 2, box_x - 2, y + 3], fill=steel)
        d.rectangle([box_x - 4, y - 2, box_x - 4, y + 3], fill=steel_dark)
        d.point([(box_x - 1, y - 4), (box_x + 1, y - 3), (box_x - 2, y - 5),
                 (box_x, y + 5), (box_x + 2, y - 1)], fill=PAL["Y"])


def scene_workshop(days: int, phase: int, width: int) -> Image.Image:
    img = Image.new("RGB", (width, H))
    words = Words(days, "DAYS LEFT", "TO MAKE TOYS!")
    d = ImageDraw.Draw(img)
    k = phase % BUILD_STEPS
    # the bench
    d.rectangle([13, 25, 46, 26], fill=WOOD)
    d.rectangle([14, 27, 15, 31], fill=WOOD_DARK)
    d.rectangle([44, 27, 45, 31], fill=WOOD_DARK)
    box_x = 24
    _build(d, box_x, phase)
    # the hammering elf on the left: busy while the box goes together
    hammering = k < 4
    paste(img, elf(1 if (hammering and phase % 2) or k == 7 else 0), 1, 11 - (2 if k == 7 else 0))
    if hammering:
        h = (2, 5, 9, 9)[k]
        _hammer(d, phase, box_x, 25 - h)
    # the wrapping elf on the right: hands up while the ribbon and bow go on,
    # and both hop when it is done
    wrapping = 4 <= k <= 6
    hop = 2 if k == 7 else 0
    paste(img, elf(1 if wrapping or k == 7 else 0), 47, 11 - hop)
    if wrapping:
        # the ribbon runs from the wrapping elf's raised hand to the box
        _, rib = BUILT[(phase // BUILD_STEPS) % len(BUILT)]
        d.line([(47, 22), (box_x + 12, 18 + (phase % 2) * 2)], fill=rib)
    right = place_words(img, words, 58, (PAL["G"], WHITE, GOLD))
    # finished presents piling up on the right, when there is room
    pile = spare(img, right, 18)
    if pile:
        px = pile[0]
        _present(img, px, 8, 7, PAL["R"], PAL["Y"], 0)
        _present(img, px + 9, 8, 9, PAL["C"], WHITE, 0)
        _present(img, px + 4, 7, 6, PAL["G"], PAL["R"], 9)
    stars(img, width // 10, 7, phase)
    return img


# The order they take turns in. The two elf cards never come back to back,
# including round the wrap from chimney to sleigh (the owner, 2026-11-08).
SCENES: Dict[str, Callable[[int, int, int], Image.Image]] = {
    "sleigh": scene_sleigh,
    "elves": scene_elves,
    "snowman": scene_snowman,
    "presents": scene_presents,
    "gingerbread": scene_gingerbread,
    "workshop": scene_workshop,
    "lights": scene_lights,
    "chimney": scene_chimney,
}
#: Scenes too alike to show one after the other.
ELF_SCENES = frozenset({"elves", "workshop"})


def render(name: str, days: int, phase: int, width: int, height: int = H) -> Image.Image:
    """One frame of a scene, width x height. Taller panels get it scaled up whole,
    but never so far that fewer than 64 columns are left to draw in (a 64x64 panel
    shows the 64-wide card, centred, rather than a cramped 32-wide one doubled)."""
    scale = max(1, min(height // H, width // 64))
    img = SCENES[name](days, phase, max(1, width // scale))
    if scale > 1:
        img = img.resize((img.width * scale, H * scale), Image.NEAREST)
    if img.size != (width, height):
        canvas = Image.new("RGB", (width, height))
        canvas.paste(img, (0, max(0, (height - img.height) // 2)))
        img = canvas
    return img
