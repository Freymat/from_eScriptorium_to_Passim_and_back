import os
import time
from datetime import timedelta, datetime

from paths import *
from config import *

# You can configure the pipeline by changing the parameters in the config.py file.

# Function to save results in a text file
def save_timings_to_file(step_name, duration):
    # Ensure the directory exists
    if not os.path.exists(timings_path):
        os.makedirs(timings_path)
    
    formatted_duration = str(timedelta(seconds=duration))
    with open(os.path.join(timings_path, "timings.txt"), "a") as file:
        file.write(f"{step_name}: {formatted_duration}\n")

# Save current information to file
current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Ensure the directory exists
if not os.path.exists(timings_path):
    os.makedirs(timings_path)

with open(os.path.join(timings_path, "timings.txt"), "w") as file:
    file.write(f"Current date: {current_date}\n")
    file.write(f"doc_pk: {doc_pk}\n")
    file.write(f"Passim n-grams: {n}\n")
    file.write(f"Spark parameters: n_cores={n_cores}, mem={mem} GB, driver_mem={driver_mem} GB\n")    
    file.write(f"Levenshtein ratio treshold: {levenshtein_threshold}\n")
    file.write("\n")

# Complete Pipeline

# Step 1. Import a document from eScriptorium
# The archive file has to be unzipped in the data/raw/xmls_from_eSc' folder.
# from src.fetch_xmls_from_eSc import initiate_xml_export
# if __name__ == "__main__":
#     initiate_xml_export(doc_pk)

# Step 2. Extract textblocks from the OCR results
from src.prepare_data_for_passim import build_passim_input
if __name__ == "__main__":
    start_time = time.time()
    build_passim_input(xmls_from_eSc_path, ocr_lines_dict_path, GT_texts_directory_path, input_passim_path)
    duration = time.time() - start_time
    save_timings_to_file("Step 2 (prepare OCR lines for Passim)", duration)

# Step 3. Run Passim
from src.compute_alignments_with_passim import *
if __name__ == "__main__":
    start_time = time.time()
    run_command_and_save_output(command_passim, output_passim_path)
    duration = time.time() - start_time
    save_timings_to_file("Step 3 (Passim computation)", duration)

# Step 4. Process the results
# Extract Passim results, select relevant alignments and update altos XML files for eScriptorium.
from src.process_alignment_results import *
if __name__ == "__main__":
    start_time = time.time()
    process_passim_results(passim_out_json_path, lines_dict_with_alg_GT_path, xmls_from_eSc_path, xmls_for_eSc_path, levenshtein_threshold)
    duration = time.time() - start_time
    save_timings_to_file("Step 4 (XMLs update with alignments)", duration)

# Step 5. Summarize the results in tsv files
from src.build_results_summary_tsv import *
if __name__ == "__main__":
    start_time = time.time()
    create_tsvs(alignment_register_path, doc_pk, display_n_best_gt, n_best_gt)
    duration = time.time() - start_time
    save_timings_to_file("Step 5 (Tsv with results creation)", duration)

   
# Step 6. Optional: export the results to eScriptorium
# from src.export_results_to_eSc import *
# if __name__ == "__main__":
#     start_time = time.time()
#     zip_alignment_files(xmls_for_eSc_path, add_timestamp=True)
#     import_zip_to_eSc(xmls_for_eSc_path)
#     duration = time.time() - start_time
#     save_timings_to_file("Step 5 (XMLs export to eSc)", duration)

print("Pipeline completed.")