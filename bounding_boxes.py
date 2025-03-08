import os
import cv2
import glob
import argparse
import numpy as np


def visualize_annotations_in_directory(image_dir, label_dir=None, output_dir=None, filter_classes=None):
    """
    Draw bounding boxes on all images in a directory and allow navigation between them.

    Args:
        image_dir: Directory containing the images
        label_dir: Directory containing the label files (if None, will look in same dir as images)
        output_dir: Directory to save annotated images (if None, won't save)
        filter_classes: List of class IDs to display (if None, show all classes)
    """
    # Class definitions - match those in annotation tool
    class_map = {
        "0": "0-levedura",
        "1": "1-fungo",
        "2": "2-micro-alga"
    }

    # Get all image files
    image_files = sorted(glob.glob(os.path.join(image_dir, "*.jpg")) +
                         glob.glob(os.path.join(image_dir, "*.png")))

    if not image_files:
        print(f"No image files found in {image_dir}")
        return

    current_idx = 0
    total_images = len(image_files)

    # Track which classes to show (initialize all as visible)
    class_visibility = {cls_id: True for cls_id in class_map.keys()}

    if filter_classes:
        # Initialize with only specified classes visible
        class_visibility = {cls_id: (cls_id in filter_classes) for cls_id in class_map.keys()}

    while True:
        img_path = image_files[current_idx]
        img = cv2.imread(img_path)
        if img is None:
            print(f"Error: Could not load image {img_path}")
            current_idx = (current_idx + 1) % total_images
            continue

        h, w = img.shape[:2]

        # Find matching label file
        base_name = os.path.splitext(os.path.basename(img_path))[0]
        if label_dir:
            label_path = os.path.join(label_dir, f"{base_name}.txt")
        else:
            label_path = os.path.join(os.path.dirname(img_path), f"{base_name}.txt")

        # Count visible annotations for each class
        class_counts = {cls_id: 0 for cls_id in class_map.keys()}
        total_visible = 0

        # Draw boxes if annotations exist
        annotations = []
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                annotations = f.readlines()

            # Draw each annotation
            box_idx = 0
            for ann in annotations:
                parts = ann.strip().split()
                if len(parts) == 5:  # YOLO format: class x_center y_center width height
                    cls, x_center, y_center, box_w, box_h = parts

                    # Skip if class is filtered out
                    if not class_visibility.get(cls, True):
                        continue

                    # Update class counts
                    class_counts[cls] = class_counts.get(cls, 0) + 1
                    total_visible += 1

                    # Convert normalized coordinates to pixel values
                    x_center = float(x_center) * w
                    y_center = float(y_center) * h
                    box_w = float(box_w) * w
                    box_h = float(box_h) * h

                    # Calculate corner points
                    x1 = int(x_center - box_w / 2)
                    y1 = int(y_center - box_h / 2)
                    x2 = int(x_center + box_w / 2)
                    y2 = int(y_center + box_h / 2)

                    # Get class color (different for each class)
                    color_map = {
                        "0": (0, 255, 0),  # Green for levedura
                        "1": (0, 0, 255),  # Red for fungo
                        "2": (255, 0, 0)  # Blue for micro-alga
                    }
                    color = color_map.get(cls, (0, 255, 0))

                    # Draw rectangle
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

                    # Get class name for display
                    class_name = class_map.get(cls, f"Class {cls}")

                    # Add class name and identification number
                    cv2.putText(img, f"{class_name} #{box_idx + 1}", (x1, y1 - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

                    box_idx += 1

        # Add count and navigation information
        y_offset = 30
        cv2.putText(img, f"Total visible: {total_visible}", (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

        y_offset += 30

        # Show count for each class
        for cls_id, cls_name in class_map.items():
            count = class_counts.get(cls_id, 0)
            visibility = "✓" if class_visibility.get(cls_id, True) else "✗"
            color = (0, 255, 0) if class_visibility.get(cls_id, True) else (0, 0, 255)

            cv2.putText(img, f"{visibility} {cls_name}: {count}", (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
            y_offset += 30

        cv2.putText(img, f"Image: {current_idx + 1}/{total_images} - {os.path.basename(img_path)}",
                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

        y_offset += 30
        cv2.putText(img, "Controls: 'n'=next, 'p'=prev, 'q'=quit, '0'-'9'=toggle class",
                    (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

        # Save if output directory specified
        if output_dir and 'save_current' in locals() and save_current:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"annotated_{os.path.basename(img_path)}")
            cv2.imwrite(output_path, img)
            print(f"Saved annotated image to {output_path}")
            save_current = False

        # Display the image
        scale = min(1.0, min(1200 / w, 800 / h))
        if scale < 1.0:
            img_display = cv2.resize(img, (int(w * scale), int(h * scale)))
        else:
            img_display = img.copy()

        cv2.imshow("Annotated Images - Navigation", img_display)

        # Handle keyboard input
        key = cv2.waitKey(0) & 0xFF

        if key == ord('q'):  # Quit
            break
        elif key == ord('n'):  # Next image
            current_idx = (current_idx + 1) % total_images
        elif key == ord('p'):  # Previous image
            current_idx = (current_idx - 1) % total_images
        elif key == ord('s'):  # Save current image
            save_current = True
        elif key >= ord('0') and key <= ord('9'):  # Toggle class visibility
            cls_id = chr(key)
            if cls_id in class_visibility:
                class_visibility[cls_id] = not class_visibility[cls_id]
        elif key == ord('a'):  # Show all classes
            for cls_id in class_visibility:
                class_visibility[cls_id] = True

    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description='Visualize YOLO annotations on images')
    parser.add_argument('--image_dir', required=True, help='Directory containing images')
    parser.add_argument('--label_dir', help='Directory containing labels (if different from image dir)')
    parser.add_argument('--output_dir', help='Directory to save annotated images')
    parser.add_argument('--filter_classes', help='Comma-separated list of class IDs to display (e.g., "0,1")')

    args = parser.parse_args()

    # Parse filter classes
    filter_classes = None
    if args.filter_classes:
        filter_classes = args.filter_classes.split(',')

    visualize_annotations_in_directory(args.image_dir, args.label_dir, args.output_dir, filter_classes)


if __name__ == "__main__":
    main()