from PIL import Image, ImageDraw, ImageFont
import os
from functools import lru_cache
from datetime import datetime

@lru_cache(maxsize=100)
def generate_icon(level):
    """
    Generate an RPG-style icon for the given level.
    """
    try:
        # Define icon size and colors
        size = (200, 200)
        background_color = (255, 255, 255)
        text_color = (0, 0, 0)

        # Create a blank image
        image = Image.new('RGB', size, background_color)
        draw = ImageDraw.Draw(image)

        # Load a font
        try:
            font = ImageFont.load_default()
        except IOError:
            raise Exception("Font file not found.")

        # Define fighting components
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

        # Draw text and component
        text = level[:2]  # Use first 2 letters of the level for simplicity
        component = components.get(level, "✨")
        combined_text = f"{text}\n{component}"
        text_bbox = draw.textbbox((0, 0), combined_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
        draw.text(text_position, combined_text, fill=text_color, font=font)

        # Save the image to a temporary file
        temp_dir = "icons_cache"
        os.makedirs(temp_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        file_path = os.path.join(temp_dir, f"{level}_{timestamp}.png")
        image.save(file_path)

        return file_path
    except Exception as e:
        print(f"Error generating icon for level {level}: {e}")
        return None

def clear_icon_cache():
    """
    Clear the icon cache.
    """
    generate_icon.cache_clear()
    temp_dir = "icons_cache"
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)