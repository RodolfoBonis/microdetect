# convert_tiff.py
import argparse
import os
import glob
from PIL import Image
import cv2
import numpy as np
from tqdm import tqdm


def convert_tiff_to_png(input_dir, output_dir, use_opencv=False, delete_original=False):
    """
    Convert all TIFF images in input_dir to PNG format and save them to output_dir.

    Args:
        input_dir: Directory containing TIFF images
        output_dir: Directory to save PNG images
        use_opencv: Whether to use OpenCV (True) or PIL (False) for conversion
        delete_original: Whether to delete original TIFF files after conversion
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get all TIFF files
    tiff_files = []
    for ext in ['*.tif', '*.tiff']:
        tiff_files.extend(glob.glob(os.path.join(input_dir, ext)))

    if not tiff_files:
        print(f"No TIFF files found in {input_dir}")
        return

    print(f"Found {len(tiff_files)} TIFF files to convert")

    # Set up progress bar
    progress_bar = tqdm(total=len(tiff_files), desc="Converting TIFF to PNG")

    errors = 0
    success = 0

    # Convert each file
    for tiff_path in tiff_files:
        base_name = os.path.basename(tiff_path)
        name_without_ext = os.path.splitext(base_name)[0]
        png_path = os.path.join(output_dir, f"{name_without_ext}.png")

        try:
            if use_opencv:
                # OpenCV approach
                img = cv2.imread(tiff_path, cv2.IMREAD_UNCHANGED)
                if img is None:
                    tqdm.write(f"Failed to read {tiff_path} with OpenCV")
                    errors += 1
                    progress_bar.update(1)
                    continue

                # Normalize if needed (for 16-bit images)
                if img.dtype == np.uint16:
                    dst = np.zeros_like(img)
                    img = cv2.normalize(img, dst, 0.0, 255.0, cv2.NORM_MINMAX)
                    img = img.astype(np.uint8)

                cv2.imwrite(png_path, img)
            else:
                # PIL approach
                with Image.open(tiff_path) as img:
                    img.save(png_path, "PNG")

            # Delete original TIFF file if requested
            if delete_original:
                os.remove(tiff_path)

            success += 1

        except Exception as e:
            tqdm.write(f"Error converting {tiff_path}: {e}")
            errors += 1

        # Update progress bar
        progress_bar.update(1)

    # Close progress bar
    progress_bar.close()
    print(f"Conversion complete: {success} files successfully converted, {errors} errors")


def main():
    parser = argparse.ArgumentParser(description='Convert TIFF images to PNG format')
    parser.add_argument('--input_dir', required=True, help='Directory containing TIFF images')
    parser.add_argument('--output_dir', required=True, help='Directory to save PNG images')
    parser.add_argument('--use_opencv', action='store_true', help='Use OpenCV instead of PIL for conversion')
    parser.add_argument('--delete_original', action='store_true', help='Delete original TIFF files after conversion')

    args = parser.parse_args()

    convert_tiff_to_png(args.input_dir, args.output_dir, args.use_opencv, args.delete_original)


if __name__ == "__main__":
    main()