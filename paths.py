import os

# PATHES

# Absolute path of the project's root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Directory for the digital editions (GT texts)
# Concatenated txt files
GT_texts_directory_path = os.path.join(project_root, "data", "raw", "digital_editions")

# Directory for the XMLs alto files from eScriptorium (OCR results)
xmls_from_eSc_path = os.path.join(project_root, "data", "raw", "xmls_from_eSc")

# path to the dictionary that will contain the extracted textblocks from OCR
ocr_lines_dict_path = os.path.join(
    project_root, "data", "processed", "ocr_lines_dict", "ocr_lines_dict.json"
)

# path for the JSON file used as input for Passim
input_passim_path = os.path.join(
    project_root, "data", "processed", "json_for_passim", "passim_input.json"
)

# Directory where the output of Passim will be stored
output_passim_path = os.path.join(project_root, "data", "processed", "passim_output")

# Folder where Passim stores the alignment results (json files)
passim_out_json_path = os.path.join(
    project_root, "data", "processed", "passim_output", "out.json"
)

# Output directory containing the processed alto files and zip ready to be imported in eScriptorium
xmls_for_eSc_path = os.path.join(project_root, "data", "output", "xmls_for_eSc")

# Directory containing the dictionaries with the alignment of the GT for each OCR line
lines_dict_with_alg_GT_path = os.path.join(
    project_root, "data", "processed", "lines_dict_with_alg_GT"
)

# Directory containing the informations about all parts of the document, fetched from eScriptorium API.
all_parts_infos_path = os.path.join(
    project_root, "data", "processed", "eSc_parts_infos"
)

# Directory containing a summary of the alignment results, for each part of the document, for each GT, for the chosen Levenshtein threshold: the total number of aligned lines, and the size of each alignment cluster.
alignment_register_path = os.path.join(
    project_root, "data", "output", "alignment_register"
)

# Directory containing tsv files synthesizing the alignment results
results_summary_tsv_path = os.path.join(
    project_root, "data", "output", "results_summary_tsv"
)

# Directory containting the backup of the pipeline results
backup_path = os.path.join(project_root, "results_backups")

# Directory containing the timings of the pipeline steps
timings_path = os.path.join(project_root, "data", "output", "pipeline_timings")
