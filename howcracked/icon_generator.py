from PIL import Image, ImageDraw, ImageFont
import os
from functools import lru_cache
from pathlib import Path

# Stable per-cog cache dir (not dependent on process cwd)
_CACHE_DIR = Path(__file__).resolve().parent / "icons_cache"


@lru_cache(maxsize=100)
def generate_icon(level):
    """
    Generate an RPG-style icon for the given level.
    """
    try:
        size = (200, 200)
        background_color = (255, 255, 255)
        text_color = (0, 0, 0)

        image = Image.new("RGB", size, background_color)
        draw = ImageDraw.Draw(image)

        try:
            font = ImageFont.load_default()
        except IOError:
            raise Exception("Font file not found.")

        components = {
            "On-Crack": "🔥",
            "Butt-Crack-ed": "👊",
            "Un-Cracked": "🛡️",
            "Not So Cracked": "⚔️",
            "Kinda Cracked": "✨",
            "Barely Cracked": "💥",
            "Slightly Cracked": "🔥",
            "Moderately Cracked": "👊",
            "Highly Cracked": "🛡️",
            "Extremely Cracked": "⚔️",
            "Insanely Cracked": "✨",
            "Godly Cracked": "💥",
            "Legendary Cracked": "🔥",
            "Mythical Cracked": "👊",
            "Ultimate Cracked": "🛡️",
            "Ultra Mega Super Cracked": "⚔️",
        }

        text = level[:2]
        component = components.get(level, "✨")
        combined_text = f"{text}\n{component}"
        text_bbox = draw.textbbox((0, 0), combined_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
        draw.text(text_position, combined_text, fill=text_color, font=font)

        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in level)
        file_path = _CACHE_DIR / f"{safe}.png"
        if not file_path.exists():
            image.save(file_path)

        return str(file_path)
    except Exception as e:
        print(f"Error generating icon for level {level}: {e}")
        return None


def clear_icon_cache():
    """
    Clear the icon cache.
    """
    generate_icon.cache_clear()
    if _CACHE_DIR.exists():
        for file in _CACHE_DIR.iterdir():
            if file.is_file():
                try:
                    file.unlink()
                except OSError:
                    pass
