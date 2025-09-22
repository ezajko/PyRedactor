#!/usr/bin/env python3
# Licensed under GPLV3.0
# (c) 2025 Ernedin Zajko


import io, os, sys, re, glob
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger
from copy import deepcopy
from datetime import datetime
import json
import hashlib
from appdirs import user_data_dir
import pytesseract
import pypdfium2 as pdfium


class ImageContainer:
    """Container for images of PDF pages"""

    zoom_factor = 100

    def __init__(self, image, size=(0, 0), rectangles=None):
        self.image = image
        self.size = size
        self.height_in_pt = size[0]
        self.width_in_pt = size[1]
        self.scaled_image = self.image

        # list of rectangles [[start_cords, end_coords, color], ...]
        self.rectangles = list() if rectangles == None else rectangles

    def increaseZoom(self, number=20):
        """Zoom in image. Returns new zoom_factor"""
        ImageContainer.zoom_factor += number
        if ImageContainer.zoom_factor > 240:
            ImageContainer.zoom_factor = 240
        else:
            self.scaleImage()
        return [ImageContainer.zoom_factor]

    def decreaseZoom(self, number=20):
        """Zoom out of image. Returns new zoom_factor"""
        ImageContainer.zoom_factor -= number
        if ImageContainer.zoom_factor < 20:
            ImageContainer.zoom_factor = 20
        else:
            self.scaleImage()
        return [ImageContainer.zoom_factor]

    def scaleImage(self):
        """Scale original size image for display in Graph element."""
        width, height = self.image.size
        newwidth = int(width * ImageContainer.zoom_factor / 100)
        newheight = int(height * ImageContainer.zoom_factor / 100)
        self.scaled_image = self.image.resize(
            (newwidth, newheight), resample=Image.LANCZOS
        )

    def undo(self):
        """Go back in history. Remove last rectangle."""
        if len(self.rectangles) > 0:
            self.rectangles.pop()
        return self

    def data(self):
        """Return bytes of scaled image."""
        with io.BytesIO() as output:
            self.scaled_image.save(output, format="PNG")
            data = output.getvalue()
            return data

    def jpg(self, image=None, image_quality=85, scale=1):
        """Return bytes of compressed image"""
        with io.BytesIO() as output:
            image_to_save = (
                image
                if scale == 1
                else image.resize(
                    (int(image.width * scale), int(image.height * scale)),
                    resample=Image.LANCZOS,
                )
            )
            image_to_save.save(
                output, format="JPEG", quality=image_quality, optimize=True
            )
            data = output.getvalue()
        return data

    def refresh(self):
        """Update the scaled image and return self"""
        self.scaleImage()
        return self

    def finalizedImage(self, format="PIL", image_quality=100, scale=1):
        """Return a copy of the imported image with all the rectangles and in the requested format."""
        final_image = self.drawRectanglesOnImage(self.image.copy())
        if format in ("JPEG", "JPG"):
            return self.jpg(final_image.convert("RGB"), image_quality, scale)
        else:
            return final_image

    def drawRectanglesOnImage(self, image):
        """Draw the rectangles in self.rectangles on image"""
        draw = ImageDraw.Draw(image)

        for rectangle in self.rectangles:
            draw.rectangle(xy=[rectangle[0], rectangle[1]], fill=rectangle[2])
        return image

    def addRectangle(self, start_point, end_point, fill="black"):
        """Add a rectangle to the rectangles list"""
        try:
            # Normalize coordinates to ensure x1 >= x0 and y1 >= y0
            x0, y0 = start_point
            x1, y1 = end_point
            
            # Ensure proper ordering
            left = min(x0, x1)
            right = max(x0, x1)
            top = min(y0, y1)
            bottom = max(y0, y1)
            
            start_point = (left, top)
            end_point = (right, bottom)

            factor = ImageContainer.zoom_factor / 100

            computed_startpoint_x = int((start_point[0]) / factor)
            computed_startpoint_y = int((start_point[1]) / factor)

            computed_endpoint_x = int((end_point[0]) / factor)
            computed_endpoint_y = int((end_point[1]) / factor)

            start_point_in_original = (computed_startpoint_x, computed_startpoint_y)
            end_point_in_original = (computed_endpoint_x, computed_endpoint_y)

            self.rectangles.append(
                (start_point_in_original, end_point_in_original, fill)
            )

        except ValueError:
            pass
        return self


def exportRectangles(pages):
    """Creates a list of all rectangles"""
    rectangles = []
    for page in pages:
        # Process rectangles to make them JSON serializable
        processed_page_rectangles = []
        for rect in page.rectangles:
            if isinstance(rect, (list, tuple)) and len(rect) == 3:
                start_point, end_point, color = rect
                # Convert tuples to lists for JSON serialization
                processed_start = list(start_point) if isinstance(start_point, tuple) else start_point
                processed_end = list(end_point) if isinstance(end_point, tuple) else end_point
                processed_color = str(color)  # Ensure color is a string
                processed_page_rectangles.append([processed_start, processed_end, processed_color])
            else:
                # Handle any unexpected rectangle format
                processed_page_rectangles.append(str(rect))
        rectangles.append(processed_page_rectangles)
    
    contains_rectangles = [True if len(item) > 0 else False for item in rectangles]
    if any(contains_rectangles):
        return rectangles
    else:
        return None


def deleteAllRectangles(pages):
    """Delete rectangles on all pages"""
    for page in pages:
        page.rectangles = []
    # deleteWorkfile() # This should be handled by the UI layer


def toBytes(image):
    """Convert PIL image to String (base64 encoded PNG)"""
    with io.BytesIO() as output:
        image.save(output, format="PNG")
        return output.getvalue()


def encodeFilepath(filepath):
    hash_object = hashlib.md5(filepath.encode())
    hex_dig = hash_object.hexdigest()
    return hex_dig


def deleteOldestFiles(directory_path, file_limit=25):
    try:
        # Create a list of all files in the directory
        files = glob.glob(os.path.join(directory_path, "*"))

        # Check if there are more than 'file_limit' files
        if len(files) > file_limit:
            # Sort files by creation time
            sorted_files = sorted(files, key=os.path.getctime)

            # Delete the oldest files until only 'file_limit' files remain
            for file in sorted_files[:-file_limit]:
                try:
                    os.remove(file)
                except Exception as e:
                    print(f"Error deleting file {file}: {e}")
    except Exception as e:
        print(f"Error in deleteOldestFiles: {e}")


def saveWorkfile(
    file_path, images, current_page, fill_color, output_quality, history_length
):
    try:
        import json  # Import json to ensure it's available
        datadir = user_data_dir("PyRedactor", "digidigital")
        rectangles = exportRectangles(images)
        if rectangles != None:
            workfile_name = encodeFilepath(file_path)
            work_data = {
                "rectangles": rectangles,
                "pages": len(images),
                "current_page": current_page,
                "fill_color": fill_color,
                "output_quality": output_quality,
            }
            if not os.path.exists(datadir):
                os.makedirs(datadir, exist_ok=True)
            with open(os.path.join(datadir, workfile_name), "w", encoding="utf-8") as f:
                json.dump(work_data, f, ensure_ascii=False, indent=4)
            deleteOldestFiles(datadir, history_length)
            return True
        else:
            deleteWorkfile(file_path)
            return True
    except Exception as e:
        print(f"Error in saveWorkfile: {e}")
        import traceback
        traceback.print_exc()
        return False


def deleteWorkfile(file_path):
    datadir = user_data_dir("PyRedactor", "digidigital")
    try:
        workfile = os.path.join(datadir, encodeFilepath(file_path))
        if os.path.isfile(workfile):
            os.remove(workfile)
    except Exception as e:
        print(f"Error deleting workfile: {e}")
        pass


def loadWorkfile(file_path):
    datadir = user_data_dir("PyRedactor", "digidigital")
    try:
        workfile_name = encodeFilepath(file_path)
        workfile = os.path.join(datadir, workfile_name)
        if os.path.isfile(workfile):
            import json  # Import json to ensure it's available
            with open(workfile, "r", encoding="utf-8") as f:
                work_data = json.load(f)
            return work_data
        else:
            return None
    except Exception as e:
        print(f"Error loading workfile: {e}")
        return None
