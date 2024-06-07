import os
import sys
import shutil
import zipfile
from datetime import datetime
import tempfile


# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config import doc_pk, n, levenshtein_threshold
from paths import project_root, backup_path


def backup_pipeline_results():
    """
    Backup the pipeline results in a folder and create a zip archive with a specific name format.

    The following parameters will be added automatically to the backup name:
    - doc_pk (str): The document primary key.
    - n (int): Some parameter 'n'.
    - levenshtein_threshold (float): The Levenshtein threshold value.
    """
    # Get current date
    current_date = datetime.now().strftime("%Y%m%d")

    # Create archive name
    archive_name = (
        f"{current_date}_doc_pk_{doc_pk}_n_{n}_lev_tresh_{levenshtein_threshold}"
    )

    # Check if the backup folder exists, if not create it
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy necessary directories to the temporary directory
        shutil.copytree(
            os.path.join(project_root, "data", "output"),
            os.path.join(temp_dir, "output"),
        )
        shutil.copytree(
            os.path.join(project_root, "data", "processed"),
            os.path.join(temp_dir, "processed"),
        )

        # Create the zip archive directly in the backup_path
        archive_path = os.path.join(backup_path, archive_name)
        with zipfile.ZipFile(f"{archive_path}.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)

    print(
        f"Pipeline results backed up in {os.path.join(backup_path, archive_name)}.zip"
    )
