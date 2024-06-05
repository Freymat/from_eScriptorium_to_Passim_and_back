import os
import sys
import json
import zipfile
from datetime import datetime
import requests

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from paths import alignment_register_path
from config import doc_pk
from credentials import root_url, headersbrief


def zip_alignment_files(xmls_for_eSc_path, add_timestamp=False):
    """
    Compress the XML files in the 'xmls_for_eSc' folder into ZIP files, one for each GT_id.
    The ZIP files will be sent to the eScriptorium instance.

    Parameters:
    xmls_for_eSc_path (str): Path to the folder containing XML files to compress.
    add_timestamp (bool): Whether to add a timestamp to the ZIP file names.
    """
    timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")

    alignment_register = os.path.join(
        alignment_register_path, "alignment_register.json"
    )

    if not os.path.exists(alignment_register_path):
        print(f"Error: Directory '{alignment_register_path}' does not exist.")
        return

    if not os.path.isfile(alignment_register):
        print(
            f"Error: File 'alignment_register.json' not found in '{alignment_register_path}'."
        )
        return

    with open(alignment_register, "r") as file_handler:
        alignment_register_data = json.load(file_handler)

    for entry in alignment_register_data:
        id2 = entry["GT_id"]
        output_folder = os.path.join(xmls_for_eSc_path, id2)
        id2_without_extension = os.path.splitext(id2)[0]
        zip_file_name = f"{id2_without_extension}.zip"

        if add_timestamp:
            zip_file_name = f"{id2_without_extension}{timestamp}.zip"

        zip_file_path = os.path.join(xmls_for_eSc_path, zip_file_name)

        if not os.path.exists(output_folder):
            print(
                f"Error: Directory '{output_folder}' does not exist for GT_id '{id2}'."
            )
            continue

        with zipfile.ZipFile(zip_file_path, "w") as zipf:
            for root, _, files in os.walk(output_folder):
                for file in files:
                    zipf.write(
                        os.path.join(root, file),
                        arcname=os.path.relpath(
                            os.path.join(root, file), output_folder
                        ),
                    )

        print(f"XML files in {output_folder} compressed in {zip_file_path}")


def import_xml(doc_pk, dirname, fname, name):
    """
    e.g. import_xml(3221,r'/content/','export_doc3221_trial_alto_202302231124.zip')
    """
    data = {"name": name, "document": doc_pk, "task": "import-xml"}
    file = os.path.join(dirname, fname)
    import_url = f"{root_url}/api/documents/{doc_pk}/imports/"

    with open(file, "rb") as fh:
        file_handler = {"upload_file": fh}
        res = requests.post(
            import_url, headers=headersbrief, data=data, files=file_handler
        )
        print(res.status_code, res.content)
        return res


def import_zip_to_eSc(xmls_for_eSc_path):
    """
    Import the ZIP file to eScriptorium.

    Parameters:
    xmls_for_eSc_path (str): Path to the directory containing ZIP files to import.
    """
    for zip_filename in os.listdir(xmls_for_eSc_path):
        if zip_filename.endswith(".zip"):
            # Build the full path to the ZIP file
            zip_file_path = os.path.join(xmls_for_eSc_path, zip_filename)

            # name of the alignment file
            name = zip_filename.split(".")[0]

            # Import in eScriptorium
            success = import_xml(doc_pk, xmls_for_eSc_path, zip_filename, name)

            if success:
                print(
                    f"{zip_filename} has been successfully imported into eScriptorium."
                )
            else:
                print(f"Error: Failed to import {zip_filename} into eScriptorium.")

    print(
        f"Link to the document in eScriptorium: https://msia.escriptorium.fr/document/{doc_pk}/images/"
    )
