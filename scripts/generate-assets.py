from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1] / "frontend"
PUBLIC = ROOT / "public"
OG_DIR = PUBLIC / "og"
OG_DIR.mkdir(parents=True, exist_ok=True)

FONT_DIR = Path("C:/Windows/Fonts")
GEORGIA = str(FONT_DIR / "georgia.ttf")
GEORGIA_ITALIC = str(FONT_DIR / "georgiai.ttf")
SANS = str(FONT_DIR / "segoeui.ttf")
SANS_SEMIBOLD = str(FONT_DIR / "seguisb.ttf")
SANS_BOLD = str(FONT_DIR / "segoeuib.ttf")

CANVAS = "#f5f3ec"
SURFACE = "#fffdf7"
INK = "#11150f"
SOFT = "#3f463c"
MUTED = "#687064"
LINE = "#d8d5ca"
ACCENT = "#d94f2b"
SUCCESS = "#246b4a"
SUCCESS_SOFT = "#e1f0e8"


def font(path: str, size: int):
    return ImageFont.truetype(path, size)


def logo_mark(draw: ImageDraw.ImageDraw, x: int, y: int, size: int, fill: str = ACCENT):
    radius = int(size * 0.24)
    draw.rounded_rectangle((x, y, x + size, y + size), radius=radius, fill=fill)
    cx = x + size / 2
    stroke = max(3, int(size * 0.075))
    top = y + size * 0.24
    bottom = y + size * 0.68
    draw.line((cx, top, cx, bottom), fill=CANVAS, width=stroke)
    draw.line(
        (cx - size * 0.14, bottom - size * 0.14, cx, bottom),
        fill=CANVAS,
        width=stroke,
    )
    draw.line(
        (cx + size * 0.14, bottom - size * 0.14, cx, bottom),
        fill=CANVAS,
        width=stroke,
    )
    draw.line(
        (x + size * 0.26, y + size * 0.76, x + size * 0.74, y + size * 0.76),
        fill=CANVAS,
        width=stroke,
    )


def make_apple_icon():
    scale = 4
    size = 180
    image = Image.new("RGB", (size * scale, size * scale), ACCENT)
    draw = ImageDraw.Draw(image)
    logo_mark(draw, 0, 0, size * scale, ACCENT)
    # The mark's foreground is canvas-coloured; increase contrast with white.
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overdraw = ImageDraw.Draw(overlay)
    logo_mark(overdraw, 0, 0, size * scale, ACCENT)
    image = image.resize((size, size), Image.Resampling.LANCZOS)
    image.save(PUBLIC / "apple-touch-icon.png", optimize=True)


def make_og():
    scale = 2
    width, height = 1200, 630
    image = Image.new("RGB", (width * scale, height * scale), CANVAS)
    draw = ImageDraw.Draw(image)

    # Quiet grid, only in the background.
    grid = 72 * scale
    for x in range(0, width * scale, grid):
        draw.line((x, 0, x, height * scale), fill="#ece8de", width=1)
    for y in range(0, height * scale, grid):
        draw.line((0, y, width * scale, y), fill="#ece8de", width=1)

    margin = 78 * scale
    logo_mark(draw, margin, 62 * scale, 46 * scale)
    draw.text(
        (margin + 62 * scale, 64 * scale),
        "clipwell",
        font=font(SANS_BOLD, 31 * scale),
        fill=INK,
    )
    draw.text(
        (margin + 63 * scale, 99 * scale),
        "PUBLIC MEDIA, SAVED CLEANLY",
        font=font(SANS_BOLD, 10 * scale),
        fill=MUTED,
    )

    # Top-right badge.
    badge_text = "7 PLATFORM ROUTES"
    badge_font = font(SANS_BOLD, 11 * scale)
    badge_w = draw.textlength(badge_text, font=badge_font)
    badge_x = width * scale - margin - badge_w - 34 * scale
    badge_y = 68 * scale
    draw.rounded_rectangle(
        (badge_x, badge_y, badge_x + badge_w + 34 * scale, badge_y + 32 * scale),
        radius=16 * scale,
        fill=SURFACE,
        outline=LINE,
        width=1 * scale,
    )
    draw.ellipse(
        (
            badge_x + 13 * scale,
            badge_y + 13 * scale,
            badge_x + 19 * scale,
            badge_y + 19 * scale,
        ),
        fill=SUCCESS,
    )
    draw.text(
        (badge_x + 25 * scale, badge_y + 8 * scale),
        badge_text,
        font=badge_font,
        fill=SOFT,
    )

    draw.text(
        (margin, 155 * scale),
        "Save the video.",
        font=font(GEORGIA, 78 * scale),
        fill=INK,
    )
    draw.text(
        (margin, 245 * scale),
        "Skip the noise.",
        font=font(GEORGIA_ITALIC, 78 * scale),
        fill=ACCENT,
    )

    draw.multiline_text(
        (margin, 374 * scale),
        "Public video, audio and captions from seven\nmajor platforms. Real formats only.",
        font=font(SANS, 24 * scale),
        fill=SOFT,
        spacing=12 * scale,
    )

    # Product-style card, not a fake statistic.
    card_x = 735 * scale
    card_y = 140 * scale
    card_w = 385 * scale
    card_h = 350 * scale
    draw.rounded_rectangle(
        (card_x + 7 * scale, card_y + 9 * scale, card_x + card_w + 7 * scale, card_y + card_h + 9 * scale),
        radius=14 * scale,
        fill="#e5e1d6",
    )
    draw.rounded_rectangle(
        (card_x, card_y, card_x + card_w, card_y + card_h),
        radius=14 * scale,
        fill=SURFACE,
        outline=LINE,
        width=1 * scale,
    )

    pad = 24 * scale
    draw.text(
        (card_x + pad, card_y + pad),
        "UNIVERSAL DOWNLOADER",
        font=font(SANS_BOLD, 10 * scale),
        fill=ACCENT,
    )
    draw.text(
        (card_x + pad, card_y + 43 * scale),
        "Paste a public link",
        font=font(GEORGIA, 29 * scale),
        fill=INK,
    )

    input_y = card_y + 98 * scale
    draw.rounded_rectangle(
        (card_x + pad, input_y, card_x + card_w - pad, input_y + 50 * scale),
        radius=7 * scale,
        fill="#f5f3ec",
        outline=LINE,
        width=1 * scale,
    )
    draw.text(
        (card_x + pad + 16 * scale, input_y + 15 * scale),
        "youtube.com/watch?v=…",
        font=font(SANS, 14 * scale),
        fill=MUTED,
    )
    paste_w = 52 * scale
    draw.rounded_rectangle(
        (
            card_x + card_w - pad - paste_w - 6 * scale,
            input_y + 6 * scale,
            card_x + card_w - pad - 6 * scale,
            input_y + 44 * scale,
        ),
        radius=5 * scale,
        fill=INK,
    )
    draw.text(
        (card_x + card_w - pad - paste_w + 4 * scale, input_y + 15 * scale),
        "Paste",
        font=font(SANS_SEMIBOLD, 11 * scale),
        fill=CANVAS,
    )

    detect_y = input_y + 68 * scale
    draw.rounded_rectangle(
        (card_x + pad, detect_y, card_x + pad + 130 * scale, detect_y + 25 * scale),
        radius=12 * scale,
        fill=SUCCESS_SOFT,
    )
    draw.ellipse(
        (
            card_x + pad + 11 * scale,
            detect_y + 10 * scale,
            card_x + pad + 16 * scale,
            detect_y + 15 * scale,
        ),
        fill=SUCCESS,
    )
    draw.text(
        (card_x + pad + 23 * scale, detect_y + 5 * scale),
        "YouTube detected",
        font=font(SANS_SEMIBOLD, 10 * scale),
        fill=SUCCESS,
    )

    formats = [("1080p", "Full HD"), ("720p", "HD"), ("360p", "Standard")]
    row_y = detect_y + 48 * scale
    for index, (quality, note) in enumerate(formats):
        top = row_y + index * 44 * scale
        draw.rounded_rectangle(
            (card_x + pad, top, card_x + card_w - pad, top + 35 * scale),
            radius=6 * scale,
            fill="#f5f3ec" if index else "#f7e4dc",
            outline=LINE if index else "#e9b7a8",
            width=1 * scale,
        )
        if index == 0:
            draw.ellipse(
                (
                    card_x + pad + 11 * scale,
                    top + 14 * scale,
                    card_x + pad + 19 * scale,
                    top + 22 * scale,
                ),
                fill=ACCENT,
            )
        else:
            draw.ellipse(
                (
                    card_x + pad + 11 * scale,
                    top + 14 * scale,
                    card_x + pad + 19 * scale,
                    top + 22 * scale,
                ),
                outline=MUTED,
                width=1 * scale,
            )
        draw.text(
            (card_x + pad + 28 * scale, top + 10 * scale),
            quality,
            font=font(SANS_BOLD, 12 * scale),
            fill=INK,
        )
        draw.text(
            (card_x + pad + 85 * scale, top + 11 * scale),
            note,
            font=font(SANS, 10 * scale),
            fill=MUTED,
        )
        draw.text(
            (card_x + card_w - pad - 44 * scale, top + 11 * scale),
            "MP4",
            font=font(SANS_BOLD, 9 * scale),
            fill=MUTED,
        )

    # Footer line.
    footer_y = 560 * scale
    draw.line((margin, footer_y, width * scale - margin, footer_y), fill=LINE, width=1 * scale)
    draw.text(
        (margin, footer_y + 18 * scale),
        "YouTube  ·  Instagram  ·  TikTok  ·  Twitch  ·  X  ·  Facebook  ·  Kick",
        font=font(SANS_SEMIBOLD, 13 * scale),
        fill=MUTED,
    )
    draw.text(
        (width * scale - margin - 125 * scale, footer_y + 18 * scale),
        "PUBLIC LINKS ONLY",
        font=font(SANS_BOLD, 11 * scale),
        fill=SUCCESS,
    )

    image = image.resize((width, height), Image.Resampling.LANCZOS)
    image.save(OG_DIR / "clipwell-og.png", optimize=True)


if __name__ == "__main__":
    make_apple_icon()
    make_og()
    print("Generated apple-touch-icon.png and og/clipwell-og.png")
