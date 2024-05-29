import os
import sys
import json
import zipfile


# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config import *

def zip_alignment_files(xmls_for_eSc_path):
    """
    Compress the XML files in the 'xmls_for_eSc' folder into ZIP files, one for each GT_id.
    The ZIP files will be sent to the eScriptorium instance.
    """
    alignment_register = os.path.join(alignment_register_path, "alignment_register.json")

    if not os.path.exists(alignment_register_path):
        print(f"Error: Directory '{alignment_register_path}' does not exist.")
        return

    if not os.path.isfile(alignment_register):
        print(f"Error: File 'alignment_register.json' not found in '{alignment_register_path}'.")
        return

    with open(alignment_register, 'r') as file_handler:
        alignment_register = json.load(file_handler)

    for entry in alignment_register:
        id2 = entry['GT_id']
        output_folder = os.path.join(xmls_for_eSc_path, id2)
        zip_file_name = f"{id2}_alignment.zip"
        zip_file_path = os.path.join(xmls_for_eSc_path, zip_file_name)

        if not os.path.exists(output_folder):
            print(f"Error: Directory '{output_folder}' does not exist for GT_id '{id2}'.")
            continue

        with zipfile.ZipFile(zip_file_path, 'w') as zipf:
            for root, _, files in os.walk(output_folder):
                for file in files:
                    zipf.write(os.path.join(root, file), arcname=file)
        print(f"XML files in {output_folder} compressed in {zip_file_path}")

if __name__ == "__main__":
    zip_alignment_files(xmls_for_eSc_path)



