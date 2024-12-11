import os
import time

from PIL import Image
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    if file and allowed_file(file.filename):
        # Generate a secure filename
        filename = secure_filename(file.filename)
        # Extract file extension
        file_ext = os.path.splitext(filename)[1]
        # Append current timestamp to the filename
        timestamp = int(time.time())
        new_filename = f"{os.path.splitext(filename)[0]}_{timestamp}{file_ext}"
        # Create the full file path
        file_path = os.path.join(UPLOAD_FOLDER, new_filename).replace('\\', '/')

        # Open the image using Pillow
        img = Image.open(file)
        # Resize the image to 150x150
        img = img.resize((150, 150), Image.LANCZOS)
        # Save the resized image
        img.save(file_path)

        return file_path
    return None

def delete_file(file_path):
    """
    Deletes the specified file if it exists.

    :param file_path: The full path of the file to delete.
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"File {file_path} deleted successfully.")
        else:
            print(f"File {file_path} does not exist or was already deleted.")
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")