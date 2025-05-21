from PIL import Image
import numpy as np
import argparse

parser = argparse.ArgumentParser(description="Process some arguments.")
parser.add_argument('--type', type=str, required=True, help="Watermark type")
parser.add_argument('filename', type=str, help="The filename to process")

def main():
    args = parser.parse_args()
    
    watermark_type = args.type
    filename = args.filename

    # Load image and ensure it's in RGBA
    input_img = Image.open(filename)
    watermarked_img = input_img.convert('RGBA')
    
    # Define watermark file based on type
    if watermark_type == "center":
        watermark_file = "src/modules/centered.png"
    elif watermark_type == "tile":
        watermark_file = "src/modules/10k.png"
    elif watermark_type == "stretch":
        watermark_file = "src/modules/stretch.png"
    else:
        raise ValueError("Unsupported watermark type. Use 'center', 'tile', or 'stretch'")
        
    watermark = Image.open(watermark_file).convert('RGBA')
    watermark_array = np.array(watermark)
    watermarked_array = np.array(watermarked_img)
    
    # Handle watermark alignment based on type
    if watermark_type == "center":
        img_height, img_width = watermarked_array.shape[:2]
        wm_height, wm_width = watermark_array.shape[:2]
        
        x_offset = (img_width - wm_width) // 2
        y_offset = (img_height - wm_height) // 2
        
        # Define the overlapping region in the image
        start_y = max(0, y_offset)
        end_y = min(img_height, y_offset + wm_height)
        start_x = max(0, x_offset)
        end_x = min(img_width, x_offset + wm_width)
        
        # Corresponding region in the watermark
        wm_start_y = max(0, -y_offset)
        wm_end_y = wm_start_y + (end_y - start_y)
        wm_start_x = max(0, -x_offset)
        wm_end_x = wm_start_x + (end_x - start_x)
        
        # Create full_watermark and assign the overlapping part
        full_watermark = np.zeros_like(watermarked_array)
        full_watermark[start_y:end_y, start_x:end_x] = watermark_array[wm_start_y:wm_end_y, wm_start_x:wm_end_x]
        
    elif watermark_type == "tile":
        img_width, img_height = watermarked_img.size
        watermark = watermark.crop((0, 0, img_width, img_height))
        full_watermark = np.array(watermark)
        
    elif watermark_type == "stretch":
        img_width, img_height = watermarked_img.size
        # Get original watermark dimensions
        wm_width, wm_height = watermark.size
        # Calculate aspect ratio
        aspect_ratio = wm_width / wm_height
        
        # Resize watermark to match image dimensions while preserving aspect ratio
        if img_width / img_height > aspect_ratio:
            # Image is wider relative to watermark
            new_height = img_height
            new_width = int(new_height * aspect_ratio)
        else:
            # Image is taller relative to watermark
            new_width = img_width
            new_height = int(new_width / aspect_ratio)
            
        # Resize watermark
        watermark = watermark.resize((new_width, new_height), Image.LANCZOS)
        watermark_array = np.array(watermark)
        
        # Center the resized watermark
        full_watermark = np.zeros_like(watermarked_array)
        x_offset = (img_width - new_width) // 2
        y_offset = (img_height - new_height) // 2
        full_watermark[y_offset:y_offset+new_height, x_offset:x_offset+new_width] = watermark_array

    # Create result array
    result = np.zeros_like(watermarked_array, dtype=np.uint8)

    # Extract alpha channels as floats
    alpha_out = watermarked_array[:, :, 3].astype(float) / 255.0  # Watermarked image alpha
    alpha_wm = full_watermark[:, :, 3].astype(float) / 255.0      # Watermark alpha

    # Compute original alpha, avoiding division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        alpha_orig = (alpha_out - alpha_wm) / (1 - alpha_wm)
        alpha_orig = np.where(alpha_wm < 1, alpha_orig, 0)
        alpha_orig = np.clip(alpha_orig, 0, 1)

    # Process each color channel
    for c in range(3):
        color_out = watermarked_array[:, :, c].astype(float)
        color_wm = full_watermark[:, :, c].astype(float)

        numerator = color_out * alpha_out - color_wm * alpha_wm
        denominator = alpha_out - alpha_wm

        mask = denominator > 0
        color_orig = np.zeros_like(color_out)
        color_orig[mask] = numerator[mask] / denominator[mask]
        color_orig = np.clip(color_orig, 0, 255)

        result[:, :, c] = color_orig.astype(np.uint8)

    # Set the alpha channel
    result[:, :, 3] = (alpha_orig * 255).astype(np.uint8)

    # Convert result to image
    result_img = Image.fromarray(result)
    
    # Save as PNG first (preserves transparency)
    result_img.save(filename, 'PNG')

if __name__ == "__main__":
    main()