"""
Create simple icons for the ePetCare Vet Desktop application.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_basic_icon(text, size=(64, 64), background_color=(52, 152, 219),
                     text_color=(255, 255, 255), output_path=None):
    """
    Create a simple icon with the given text.

    Args:
        text: Text to display on the icon (usually a single character)
        size: Icon size in pixels (width, height)
        background_color: Background color as RGB tuple
        text_color: Text color as RGB tuple
        output_path: Path to save the icon to

    Returns:
        Path to the created icon
    """
    # Create a new image with the given size and background color
    # Use RGBA mode for better compatibility with Qt
    img = Image.new('RGBA', size, background_color + (255,))  # Add alpha channel
    draw = ImageDraw.Draw(img)

    # Try to find a font that exists on the system
    font_size = int(size[0] * 0.5)
    font = None

    try:
        # Try common fonts
        for font_name in ['Arial.ttf', 'DejaVuSans.ttf', 'FreeSans.ttf', 'LiberationSans-Regular.ttf']:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except IOError:
                continue
    except Exception:
        pass

    # Fallback to default font if none of the above worked
    if font is None:
        try:
            font = ImageFont.load_default()
        except:
            # If even the default font fails, create a simple shape
            draw.rectangle([size[0] * 0.25, size[1] * 0.25, size[0] * 0.75, size[1] * 0.75],
                        fill=text_color)
            if output_path:
                img.save(output_path)
            return output_path

    # Calculate text position to center it
    if font:
        try:
            # Get text size if supported
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
        except:
            # Estimate text size if not supported
            text_width = font_size * 0.6 * len(text)
            text_height = font_size
    else:
        # Rough estimates if no font available
        text_width = font_size * 0.6 * len(text)
        text_height = font_size

    # Calculate position to center text
    x = (size[0] - text_width) / 2
    y = (size[1] - text_height) / 2

    # Draw text
    try:
        draw.text((x, y), text, font=font, fill=text_color)
    except:
        # If text drawing fails, just draw a rectangle
        draw.rectangle([size[0] * 0.25, size[1] * 0.25, size[0] * 0.75, size[1] * 0.75],
                      fill=text_color)

    # Save the image
    if output_path:
        try:
            # Use optimized PNG settings for better compatibility
            img.save(output_path, 'PNG', optimize=True)
            print(f"Icon saved successfully to {output_path}")
        except Exception as e:
            print(f"Error saving icon to {output_path}: {e}")
            return None

    return output_path

def main():
    """Create icons for the ePetCare Vet Desktop application."""
    # Get the resources directory
    resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')

    # Create the resources directory if it doesn't exist
    os.makedirs(resources_dir, exist_ok=True)

    # Create icons
    icons = {
        'dashboard-icon.png': ('D', (0, 120, 212)),   # Blue
        'patients-icon.png': ('P', (46, 125, 50)),    # Green
        'appointments-icon.png': ('A', (211, 47, 47)), # Red
        'settings-icon.png': ('S', (123, 31, 162)),   # Purple
        'backup-icon.png': ('B', (255, 143, 0)),      # Orange
        'logout-icon.png': ('L', (66, 66, 66)),       # Gray
    }

    for filename, (text, color) in icons.items():
        output_path = os.path.join(resources_dir, filename)

        # Always recreate icons to ensure they're valid
        print(f"Creating icon {filename}...")
        create_basic_icon(text, background_color=color, output_path=output_path)

    print("Icons created successfully!")

if __name__ == "__main__":
    main()