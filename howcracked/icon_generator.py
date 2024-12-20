from PIL import Image, ImageDraw, ImageFont
import os
from functools import lru_cache
from datetime import datetime

@lru_cache(maxsize=100)
def generate_icon(level):
    """
    Generate an RPG-style icon for the given level.
    """
    # Define icon size and colors
    size = (100, 100)
    background_color = (255, 255, 255)
    text_color = (0, 0, 0)

    # Create a blank image
    image = Image.new('RGB', size, background_color)
    draw = ImageDraw.Draw(image)

    # Load a font
    font = ImageFont.load_default()

    # Draw text
    text = level[:2]  # Use first 2 letters of the level for simplicity
    text_width, text_height = draw.textsize(text, font=font)
    text_position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
    draw.text(text_position, text, fill=text_color, font=font)

    # Save the image to a temporary file
    temp_dir = "icons_cache"
    os.makedirs(temp_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    file_path = os.path.join(temp_dir, f"{level}_{timestamp}.png")
    image.save(file_path)

    return file_path

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