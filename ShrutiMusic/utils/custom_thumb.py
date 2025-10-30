from PIL import Image, ImageDraw, ImageFont
import os
import aiohttp
import asyncio

# Configurable defaults
DEFAULT_FONT_PATH = None  # contoh: "ShrutiMusic/static/fonts/DejaVuSans-Bold.ttf"
DEFAULT_FONT_SIZE = 34
NEW_TEXT = "Capricorn Music"
POS_X = 18
POS_Y = 18
COVER_FILL = (20, 20, 20, 255)     # kotak penutup RGBA
TEXT_FILL = (255, 255, 255, 255)   # putih
MAX_TEXT_WIDTH_RATIO = 0.45

def _load_font(path, size):
    try:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
    except Exception:
        pass
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()

def _auto_scale_font(draw, text, font_path, init_size, max_width):
    size = init_size
    font = _load_font(font_path, size)
    w, h = draw.textsize(text, font=font)
    while w > max_width and size > 8:
        size -= 1
        font = _load_font(font_path, size)
        w, h = draw.textsize(text, font=font)
    return font, w, h

async def download_image(url: str, dest_path: str):
    # simple helper to download a url to a local path
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(dest_path, "wb") as f:
                        f.write(data)
                    return dest_path
    except Exception:
        return None
    return None

async def gen_custom_thumb(vidid: str, src_thumb_url: str = None, out_dir: str = "downloads/thumbnails", text: str = None, font_path: str = None) -> str:
    """
    Generate a custom thumbnail file with replaced text.
    - vidid: unique id to name output file
    - src_thumb_url: optional original thumbnail url; if None, use default static image if available
    - out_dir: where to save generated thumbnail
    - text: overriding text (default: "Capricorn Music")
    - font_path: optional ttf path
    Returns path to saved image (jpg) or raises exception.
    """
    os.makedirs(out_dir, exist_ok=True)
    text = text or NEW_TEXT
    font_path = font_path or DEFAULT_FONT_PATH
    out_file = os.path.join(out_dir, f"{vidid}_capricorn.jpg")

    # If already exists, return cached
    if os.path.exists(out_file):
        return out_file

    # Prepare source image: download thumbnail if provided, else use a bundled fallback if exists
    src_path = None
    if src_thumb_url:
        tmp_path = os.path.join(out_dir, f"{vidid}_src.jpg")
        downloaded = await download_image(src_thumb_url, tmp_path)
        if downloaded:
            src_path = tmp_path

    if not src_path:
        # try static fallback in repo
        fallback = os.path.join("ShrutiMusic", "static", "default_thumb.jpg")
        if os.path.exists(fallback):
            src_path = fallback
        else:
            # create a simple dark background image
            img = Image.new("RGBA", (1280, 720), (30, 30, 30, 255))
            img.convert("RGB").save(out_file, quality=85)
            return out_file

    # Open image and edit
    img = Image.open(src_path).convert("RGBA")
    width, height = img.size
    draw = ImageDraw.Draw(img)

    max_text_width = int(width * MAX_TEXT_WIDTH_RATIO)
    font, text_w, text_h = _auto_scale_font(draw, text, font_path, DEFAULT_FONT_SIZE, max_text_width)

    padding_x = int(text_h * 0.6)
    padding_y = int(text_h * 0.35)

    box_x0 = max(0, POS_X - padding_x)
    box_y0 = max(0, POS_Y - padding_y)
    box_x1 = min(width, POS_X + text_w + padding_x)
    box_y1 = min(height, POS_Y + text_h + padding_y)

    cover = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cover_draw = ImageDraw.Draw(cover)
    cover_draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill=COVER_FILL)

    img = Image.alpha_composite(img, cover)
    draw = ImageDraw.Draw(img)
    draw.text((POS_X, POS_Y), text, font=font, fill=TEXT_FILL)

    img.convert("RGB").save(out_file, quality=90)
    # cleanup tmp src if downloaded
    try:
        if src_path and src_path.endswith("_src.jpg"):
            os.remove(src_path)
    except Exception:
        pass

    return out_file
