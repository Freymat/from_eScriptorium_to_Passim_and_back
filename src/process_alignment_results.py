import os
import sys
import json
import re
import Levenshtein

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config import eSc_connexion

from paths import (
    ocr_lines_dict_path,
    lines_dict_with_alg_GT_path,
    alignment_register_path,
)
from src.utils import load_all_parts_infos


def build_list_from_passim_outputs(passim_out_json_path):
    """
    Gather the Passim outputs from jsons into a list of dictionaries.
    """
    # List to store data from all JSON files
    out_passim_list = []

    # Loop through each file in the directory
    for file in os.listdir(passim_out_json_path):
        if file.endswith(".json"):
            file_path = os.path.join(passim_out_json_path, file)
            # Open the JSON file and load its content as a list of dictionaries
            with open(file_path, "r", encoding="utf-8") as json_file:
                data = [json.loads(line) for line in json_file]
                out_passim_list.extend(data)
    print(f"Number of blocks to be processed:{len(out_passim_list)}")
    return out_passim_list


def list_GT_from_passim_output(out_passim_list):
    """
    Get the GT present in Passim alignment results.
    """
    GT_ids = list(
        set(
            [
                wit["id"]
                for textblock in out_passim_list
                for line in textblock["lines"]
                for wit in line.get("wits", [])
            ]
        )
    )
    return GT_ids


def clean_alg_text(alg_text):
    """
    Clean the text from the alignment.
    """
    # clean the alignment text
    # Replace '-' (45) with '', but avoid empty lines
    alg_text = alg_text.replace("-", "") if alg_text.replace("-", "") else alg_text
    # Replace '-' (8208) with '-' (45)
    alg_text = alg_text.replace(chr(8208), "-")
    # Remove leading and trailing spaces, but avoid empty lines
    alg_text = alg_text.strip() if alg_text.strip() else alg_text
    return alg_text


def extract_passim_results(passim_out_json_path):
    """
    Extracts the Passim alignments results and build a dictionary for each GT.
    The dictionaries are updates of the ocr_lines_dict.json file.
    For each ocr line where Passim found a GT, the GT is added with (among others) the following informations:
    - the cleaned text of the GT (leading and trailing spaces removed, '-' (45) replaced with '', '-' (8208) replaced with '-' (45))
    - the Levenshtein ratio between the GT text and the OCR text
    - the position of the first aligned character in the GT text
    """

    # Gather Passim's results in a list
    out_passim_list = build_list_from_passim_outputs(passim_out_json_path)

    # list of GTs found in alignments:
    GT_ids = list_GT_from_passim_output(out_passim_list)
    # print(f"list of GTs found in alignments: {GT_ids}")

    # Iterate over GT_ids, and update the ocr_lines_dict with the GT alignment text
    for GT_id in GT_ids:
        # print(f"--- Processing of GT {GT_id} ---")

        # Load dictionary containing OCR line-splitting information
        with open(ocr_lines_dict_path, "r", encoding="utf-8") as json_file:
            ocr_lines_dict = json.load(json_file)

        # Iterate over out_passim_list dictionaries
        for textblock in out_passim_list:

            # Extract the filename and textblock_id
            textblock_id = re.sub(
                r".*(eSc_textblock_[a-f0-9]+).*", r"\1", textblock["id"]
            )
            filename = re.sub(r".*" + textblock_id + "_(.*)", r"\1", textblock["id"])

            for line in textblock["lines"]:
                begin_index = line["begin"]
                # Check if the current GT_id is present in the wits of the line
                for wit in line.get("wits", []):
                    if wit["id"] == GT_id:
                        alg_text = wit["alg"]
                        alg_text = clean_alg_text(alg_text)
                        GT_start = wit["begin"]
                        GT_length = len(wit["text"])

                        # Find the corresponding line in the OCR dictionary
                        for part in ocr_lines_dict:
                            if part["filename"] == filename:
                                for block in part["ocr_blocks"]:
                                    if block["text_block_id"] == textblock_id:
                                        for ocr_line in block["ocr_lines"]:
                                            if ocr_line["start"] == begin_index:
                                                # Update the OCR line with the GT alignment text
                                                ocr_line["alg_GT"] = alg_text
                                                ocr_line["GT_id"] = GT_id
                                                ocr_line["GT_start"] = GT_start
                                                ocr_line["GT_len"] = GT_length
                                                lev_ratio = Levenshtein.ratio(
                                                    alg_text, ocr_line["text"]
                                                )
                                                ocr_line["levenshtein_ratio"] = round(
                                                    lev_ratio, 3
                                                )
                                                break  # No need to continue searching once found

        # Save a JSON file for each GT_id
        os.makedirs(lines_dict_with_alg_GT_path, exist_ok=True)
        file_path = os.path.join(
            lines_dict_with_alg_GT_path, f"lines_dict_with_alg_{GT_id}.json"
        )
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(ocr_lines_dict, json_file, ensure_ascii=False, indent=4)
        # print(f"    File {file_path} saved.")


# Parsing XML files and updating text content with GT alignments


def save_alignment_register_to_json(alignment_register):
    """
    Save the alignment register in a JSON file.
    The alignment register is a list of dictionaries, each dictionary contains informations about the alignment of a GT, for a given XML file.
    Utilized for having a global view of the alignment results, and for further analysis (tsv export of the results, etc.)
    """
    os.makedirs(alignment_register_path, exist_ok=True)
    register_file_path = os.path.join(
        alignment_register_path, "alignment_register.json"
    )
    with open(register_file_path, "w", encoding="utf-8") as json_file:
        json.dump(alignment_register, json_file, ensure_ascii=False, indent=4)
    return alignment_register


def get_xml_files_with_alignment(lines_dict, GT_id):
    """Get XML files containing alignments for a given ID."""
    xml_files_with_alg = set()
    for part in lines_dict:
        for block in part["ocr_blocks"]:
            for line in block["ocr_lines"]:
                if line.get("alg_GT") and line["GT_id"] == GT_id:
                    xml_files_with_alg.add(part["filename"])
    return list(xml_files_with_alg)


# We don't insert the function load_all_parts_infos in this function to avoid multiple requests
def get_pk_from_filename(all_parts_infos, filename):
    """
    Function to get the pk and the title in eScriptorium of a part from its filename.
    Parameters:
    - all_parts_infos: list of dictionaries containing informations about the parts.
    requested from the eScriptorium API. This dictionnary is requested (all_parts_infos = get_all_parts(doc_pk))
    from the eScriptorium API outisde of this function to avoid multiple requests.
    - filename of the image. Extension should be .jpg, but the function
    handles the case where the extension is missing or different.
    """
    filename, extension = os.path.splitext(filename)
    for item in all_parts_infos:
        if item["filename"] == filename + ".jpg":
            return (item["pk"], item["title"])
    return (None, None)


def count_aligned_line_clusters(lines_dict, filename, levenshtein_threshold):
    """
    Count the number of aligned lines in each cluster for a given GT.
    A cluster is a group of successive aligned lines.
    """
    clusters = []
    successive_aligned_lines = 0

    # Browse each part of the line dictionary
    for part in lines_dict:
        if part["filename"] != filename:
            continue
        # Browse each OCR block in the current section
        for block in part["ocr_blocks"]:

            # Browse each OCR line in the current block
            for line in block["ocr_lines"]:
                if (
                    line.get("alg_GT")
                    and line["levenshtein_ratio"] >= levenshtein_threshold
                ):
                    # Increments the counter of successive aligned lines
                    successive_aligned_lines += 1
                else:
                    # If the successive lines counter is greater than 0, add the number of lines to the cluster
                    if successive_aligned_lines > 0:
                        clusters.append(successive_aligned_lines)
                    # Reset counter
                    successive_aligned_lines = 0

            # If a block ends with successive aligned lines, add them as well.
            if successive_aligned_lines > 0:
                clusters.append(successive_aligned_lines)
                successive_aligned_lines = 0

    return clusters


def process_alignment_xml_as_txt(
    lines_dict_with_alg_GT_path,
    xmls_for_eSc_path,
    xmls_from_eSc_path,
    levenshtein_threshold,
):
    """Process the alignment of the GT on the OCR text lines and save the modified XML files in a ZIP archive."""

    # Load all parts informations, to get the pk and the title of the part from its filename
    # This allows better identification of the parts in the eScriptorium interface
    
    if eSc_connexion:
        all_parts_infos = load_all_parts_infos()

    alignment_register = []

    for json_file in os.listdir(lines_dict_with_alg_GT_path):
        if json_file.endswith(".json"):
            with open(
                os.path.join(lines_dict_with_alg_GT_path, json_file),
                "r",
                encoding="utf-8",
            ) as json_file_handler:
                lines_dict = json.load(json_file_handler)
            id2 = re.sub(r"lines_dict_with_alg_(.*).json", r"\1", json_file)
            output_folder = os.path.join(xmls_for_eSc_path, id2)
            os.makedirs(output_folder, exist_ok=True)

            xml_files_with_alg = get_xml_files_with_alignment(lines_dict, id2)

            for xml_file in os.listdir(xmls_from_eSc_path):
                if xml_file.endswith(".xml"):
                    if os.path.splitext(xml_file)[0] not in xml_files_with_alg:
                        continue
                    # Create a list of tuples with all detected alignments for the current GT
                    # If, the alignment is considered valid  with a Levenshtein ratio above the threshold
                    # the GT will be added to the XML file
                    # Otherwise, the content of the OCR line will be updated to an empty string

                    line_ids_with_GT = [
                        (line["line_id"], line["alg_GT"], line["levenshtein_ratio"])
                        for part in lines_dict
                        if part["filename"] == os.path.splitext(xml_file)[0]
                        for block in part["ocr_blocks"]
                        for line in block["ocr_lines"]
                        if line.get("alg_GT") and line["GT_id"] == id2
                    ]

                    with open(
                        os.path.join(xmls_from_eSc_path, xml_file), encoding="utf-8"
                    ) as xml_file_handler:
                        xml_as_txt = xml_file_handler.read()

                    line_count = 0

                    xml_text_lines = re.findall(
                        r'<TextLine ID=".*?".*?</TextLine>', xml_as_txt, re.DOTALL
                    )
                    for xml_text_line in xml_text_lines:
                        xml_text_line_id = re.search(
                            r'<TextLine ID="(.*?)"', xml_text_line
                        ).group(1)
                        if xml_text_line_id not in [
                            line_id for line_id, _, _ in line_ids_with_GT
                        ]:
                            updated_content = re.sub(
                                r'<String CONTENT=".*?"',
                                '<String CONTENT=""',
                                xml_text_line,
                            )
                            xml_as_txt = xml_as_txt.replace(
                                xml_text_line, updated_content
                            )
                        else:
                            for (
                                text_line_id,
                                alg_GT,
                                levenshtein_ratio,
                            ) in line_ids_with_GT:
                                if text_line_id == xml_text_line_id:
                                    string_content_match = re.search(
                                        r'<String CONTENT="(.*?)"', xml_text_line
                                    )
                                    if string_content_match:
                                        if levenshtein_ratio >= levenshtein_threshold:
                                            new_content = f'CONTENT="{alg_GT}"'
                                            line_count += 1
                                        else:
                                            new_content = 'CONTENT=""'
                                        xml_as_txt = xml_as_txt.replace(
                                            string_content_match.group(0),
                                            f"<String {new_content}",
                                        )

                    if line_count > 0:
                        filename = os.path.splitext(xml_file)[0]                        
                        aligned_clusters_size = count_aligned_line_clusters(
                            lines_dict, filename, levenshtein_threshold
                        )

                        if eSc_connexion:
                            part_pk, part_title = get_pk_from_filename(all_parts_infos, filename)
                        else:
                            part_pk, part_title = None, None

                        alignment_register.append(
                            {
                                "filename": xml_file,
                                "part_pk": part_pk,
                                "part_title": part_title,
                                "levenshtein_threshold": levenshtein_threshold,
                                "total_aligned_lines_count": line_count,
                                "aligned_clusters_size": aligned_clusters_size,
                                "GT_id": id2,
                            }
                        )


                    output_file_path = os.path.join(output_folder, xml_file)
                    with open(output_file_path, "w", encoding="utf-8") as output_file:
                        output_file.write(xml_as_txt)

    save_alignment_register_to_json(alignment_register)

    return alignment_register


def process_passim_results(
    passim_out_json_path,
    lines_dict_with_alg_GT_path,
    xmls_from_eSc_path,
    xmls_for_eSc_path,
    levenshtein_threshold,
):
    """
    This global function processes the Passim results and updates the XML alto files with the GT alignment.
    - Extracts the Passim alignment results
    - Parse the XML files from eScriptorium, and update the OCR lines with the GT alignment
    if the levenshtein ratio between the OCR and GT textblocks containing the lines is above a given threshold.
    - Save the updated XML files in a ZIP archive, ready to be sent to eScriptorium.
    Parameters:
    passim_out_json_path (str): Path to the directory containing the Passim output JSON files
    lines_dict_with_alg_GT_path (str): Path to the directory containing the dictionaries with the alignment of the different GT, for each OCR line
    xmls_from_eSc_path (str): Path to the directory containing the alto files from eScriptorium
    xmls_for_eSc_path (str): Path to the output directory, where the new alto files (and zip) will be saved
    """

    # Extract the Passim alignment results
    extract_passim_results(passim_out_json_path)

    if eSc_connexion:
        # Load the informations about the parts of the document
        all_parts_infos = load_all_parts_infos()

    # Parse the XML files from eScriptorium, and update the OCR lines with the GT alignment if the levenshtein ratio is above a given threshold
    process_alignment_xml_as_txt(
        lines_dict_with_alg_GT_path,
        xmls_for_eSc_path,
        xmls_from_eSc_path,
        levenshtein_threshold,
    )
