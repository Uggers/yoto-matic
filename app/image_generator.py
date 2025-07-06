import requests
from PIL import Image, ImageDraw
import io

# --- Constants for Printing ---
DPI = 300
# A4 Paper in pixels at 300 DPI (210mm x 297mm)
A4_WIDTH_PX = int(8.27 * DPI)  # 2480
A4_HEIGHT_PX = int(11.69 * DPI) # 3508

# Standard Credit Card/Yoto Card size in pixels at 300 DPI (85.6mm x 54mm)
CARD_WIDTH_PX = int(3.37 * DPI)   # 1011
CARD_HEIGHT_PX = int(2.125 * DPI) # 638

# Layout
MARGIN_PX = int(0.5 * DPI) # ~0.5 inch margin
SPACING_PX = int(0.2 * DPI) # ~0.2 inch spacing between cards
CORNER_RADIUS = int(0.15 * DPI) # ~0.15 inch corner radius

def create_rounded_mask(size, radius):
    """Creates a mask with rounded corners."""
    mask = Image.new('L', size, 0) # 'L' is for 8-bit grayscale
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + size, radius=radius, fill=255)
    return mask

def generate_print_sheet(image_urls):
    """
    Takes a list of up to 9 image URLs and generates a printable A4 sheet.
    """
    # Create the blank A4 canvas
    a4_sheet = Image.new('RGB', (A4_WIDTH_PX, A4_HEIGHT_PX), 'white')

    # Create the rounded corner mask once
    card_size = (CARD_WIDTH_PX, CARD_HEIGHT_PX)
    mask = create_rounded_mask(card_size, CORNER_RADIUS)
    
    # Process up to 9 images
    for i, url in enumerate(image_urls[:9]):
        if not url:
            continue
            
        try:
            # Download the image
            response = requests.get(url, stream=True)
            response.raise_for_status()
            card_image = Image.open(io.BytesIO(response.content)).convert('RGB')
        except Exception as e:
            print(f"Could not download or open image {url}: {e}")
            # Create a placeholder for failed images
            card_image = Image.new('RGB', card_size, 'lightgrey')
            draw = ImageDraw.Draw(card_image)
            draw.text((50, 50), "Image\nFailed\nto Load", fill="black")

        # Resize the downloaded image to fit the card dimensions perfectly
        # We use 'cover' logic (Image.LANCZOS is for high-quality downsampling)
        card_image = card_image.resize(card_size, Image.Resampling.LANCZOS)
        
        # Apply the rounded corner mask
        card_image.putalpha(mask)

        # Calculate position in the 3x3 grid
        row = i // 3
        col = i % 3
        
        x = MARGIN_PX + col * (CARD_WIDTH_PX + SPACING_PX)
        y = MARGIN_PX + row * (CARD_HEIGHT_PX + SPACING_PX)

        # Paste the rounded card onto the A4 sheet
        # The final argument is the mask itself, which handles transparency
        a4_sheet.paste(card_image, (x, y), card_image)

    # Save the final sheet to a memory buffer
    img_io = io.BytesIO()
    a4_sheet.save(img_io, 'PNG', quality=100)
    img_io.seek(0)
    
    return img_io