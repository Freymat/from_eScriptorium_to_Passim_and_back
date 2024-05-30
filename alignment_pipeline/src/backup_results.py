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

from config import *
from paths import *


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
    archive_name = f"{current_date}_doc_pk_{doc_pk}_n_{n}_lev_tresh_{levenshtein_threshold}"

    # Check if the backup folder exists, if not create it
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy necessary directories to the temporary directory
        shutil.copytree(os.path.join(project_root, "data", "output"), os.path.join(temp_dir, "output"))
        shutil.copytree(os.path.join(project_root, "data", "processed"), os.path.join(temp_dir, "processed"))

        # Create the zip archive
        shutil.make_archive(os.path.join(temp_dir, archive_name), 'zip', temp_dir)

        # Move the zip archive to the desired location
        shutil.move(f"{os.path.join(temp_dir, archive_name)}.zip", backup_path)

    # Print the location of the backup
    print(f"Pipeline results backed up in {os.path.join(backup_path, archive_name)}.zip")

if __name__ == "__main__":
    backup_pipeline_results()