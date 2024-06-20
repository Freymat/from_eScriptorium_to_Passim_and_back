import os
import sys
import json
import re
import Levenshtein
import concurrent.futures


# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config import eSc_connexion, n_cores

from paths import (
    ocr_lines_dict_path,
    lines_dict_with_alg_GT_path,
    alignment_register_path,
    passim_out_json_path,
)
from src.utils import load_all_parts_infos


def process_single_passim_output_json(file):
    """
    Process a single Passim output JSON file.
    This function is used in a parallelized context.
    """
    data = []
    file_path = os.path.join(passim_out_json_path, file)
    with open(file_path, "r", encoding="utf-8") as json_file:
        for line in json_file:
            data.append(json.loads(line))
    # print(data)
    return data


def build_list_from_passim_outputs(passim_out_json_path):
    """
    Gather the Passim outputs from jsons into a list of dictionaries.
    """
    # List to store data from all JSON files
    out_passim_list = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=n_cores) as executor:
        # Filter only JSON files
        json_files = [
            file for file in os.listdir(passim_out_json_path) if file.endswith(".json")
        ]
        # Submit each JSON file for processing
        futures = [
            executor.submit(
                process_single_passim_output_json,
                os.path.join(passim_out_json_path, file),
            )
            for file in json_files
        ]
        # Collect results
        for future in concurrent.futures.as_completed(futures):
            out_passim_list.extend(future.result())

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


def process_single_GT(GT_id, out_passim_list, ocr_lines_dict):
    """
    Process a single GT_id and update the OCR lines dictionary with GT alignment information.
    This function is used in a parallelized context.
    """
    for textblock in out_passim_list:
        textblock_id = re.sub(r".*(eSc_textblock_[a-f0-9]+).*", r"\1", textblock["id"])
        filename = re.sub(r".*" + textblock_id + "_(.*)", r"\1", textblock["id"])
        # print(f"Processing textblock {textblock_id} in file {filename}")
        for line in textblock["lines"]:
            begin_index = line["begin"]
            for wit in line.get("wits", []):
                if wit["id"] == GT_id:
                    alg_text = wit["alg"]
                    alg_text = clean_alg_text(alg_text)
                    GT_start = wit["begin"]
                    GT_length = len(wit["text"])
                    # print(f"Updating OCR lines with GT alignment: GT_start={GT_start}, GT_length={GT_length}, alg_text={alg_text}")
                    for part in ocr_lines_dict:
                        if part["filename"] == filename:
                            for block in part["ocr_blocks"]:
                                if block["text_block_id"] == textblock_id:
                                    for ocr_line in block["ocr_lines"]:
                                        if ocr_line["start"] == begin_index:
                                            # print(f"Found matching OCR line: {ocr_line}")
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
                                            break
    
    
    # Save a JSON file for the current GT_id
    if not os.path.exists(lines_dict_with_alg_GT_path):
        os.makedirs(lines_dict_with_alg_GT_path)

    file_path = os.path.join(
        lines_dict_with_alg_GT_path, f"lines_dict_with_alg_{GT_id}.json"
    )
    with open(file_path, "w", encoding="utf-8") as json_file:
        json.dump(ocr_lines_dict, json_file, ensure_ascii=False, indent=4)


def extract_passim_results(passim_out_json_path):
    """
    Extracts the Passim alignments results and updates dictionaries for each GT.
    The dictionaries are updates of the ocr_lines_dict.json file.
    For each OCR line where Passim found a GT, the GT is added with (among others) the following information:
    - the cleaned text of the GT (leading and trailing spaces removed, '-' (45) replaced with '', '-' (8208) replaced with '-' (45))
    - the Levenshtein ratio between the GT text and the OCR text
    - the position of the first aligned character in the GT text
    """

    # Gather Passim's results in a list
    out_passim_list = build_list_from_passim_outputs(passim_out_json_path)

    # list of GTs found in alignments:
    GT_ids = list_GT_from_passim_output(out_passim_list)
    # print(f"list of GTs found in alignments: {GT_ids}")

    # Load dictionary containing OCR line-splitting information
    with open(ocr_lines_dict_path, "r", encoding="utf-8") as json_file:
        ocr_lines_dict = json.load(json_file)

    # Process each GT_id in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_cores) as executor:
        futures = [
            executor.submit(process_single_GT, GT_id, out_passim_list, ocr_lines_dict)
            for GT_id in GT_ids
        ]
        for future in concurrent.futures.as_completed(futures):
            # No need to collect results as the updates are done in place
            pass


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

def clean_alg_GT_before_xml_update(text):
    text = re.sub(r'\u0026', '&amp;', text)  # & -> &amp;
    text = re.sub(r'\u0022', '&quot;', text)  # " -> &quot;
    text = re.sub(r'\u0027', '&apos;', text)  # ' -> &apos;
    text = re.sub(r'\u003C', '&lt;', text)  # < -> &lt;
    text = re.sub(r'\u003E', '&gt;', text)  # > -> &gt;
    return text


def process_single_dict_with_alg(
    json_file,
    lines_dict_with_alg_GT_path,
    xmls_for_eSc_path,
    xmls_from_eSc_path,
    levenshtein_threshold,
    eSc_connexion
):
    # Load the JSON file
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

    local_alignment_register = []

    for xml_file in os.listdir(xmls_from_eSc_path):
        if xml_file.endswith(".xml"):
            if os.path.splitext(xml_file)[0] not in xml_files_with_alg:
                continue
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
                    xml_as_txt = xml_as_txt.replace(xml_text_line, updated_content)
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
                                    # replace characters that could cause problems in XML
                                    cleaned_alg_GT = clean_alg_GT_before_xml_update(alg_GT)
                                    new_content = f'CONTENT="{cleaned_alg_GT}"'
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
                    all_parts_infos = load_all_parts_infos()
                    part_pk, part_title = get_pk_from_filename(
                        all_parts_infos, filename
                    )
                else:
                    part_pk, part_title = None, None

                local_alignment_register.append(
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

    return local_alignment_register

def process_alignment_xml_as_txt(
    lines_dict_with_alg_GT_path,
    xmls_for_eSc_path,
    xmls_from_eSc_path,
    levenshtein_threshold,
):
    if eSc_connexion:
        all_parts_infos = load_all_parts_infos()

    json_files = [
        f for f in os.listdir(lines_dict_with_alg_GT_path) if f.endswith(".json")
    ]

    alignment_register = []

    with concurrent.futures.ProcessPoolExecutor(max_workers=n_cores) as executor:
        futures = {
            executor.submit(
                process_single_dict_with_alg,
                json_file,
                lines_dict_with_alg_GT_path,
                xmls_for_eSc_path,
                xmls_from_eSc_path,
                levenshtein_threshold,
                eSc_connexion
            ): json_file for json_file in json_files
        }

        for future in concurrent.futures.as_completed(futures):
            json_file = futures[future]
            try:
                result = future.result()
                if result:
                    alignment_register.extend(result)
                else:
                    print(f"No alignment data returned for {json_file}")
            except Exception as e:
                print(f"Exception for {json_file}: {e}")

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
