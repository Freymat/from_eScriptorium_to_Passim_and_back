import os
import time
from datetime import timedelta, datetime
import argparse

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
    file.write(
        f"Spark parameters: n_cores={n_cores}, mem={mem} GB, driver_mem={driver_mem} GB\n"
    )
    file.write(f"Levenshtein ratio treshold: {levenshtein_threshold}\n")
    file.write("\n")

# Argparse setup
parser = argparse.ArgumentParser(description="Pipeline for processing OCR data")
parser.add_argument(
    "--import_document_from_eSc",
    action="store_true",
    help="Import document from eScriptorium",
)
parser.add_argument(
    "--prepare_data_for_passim", action="store_true", help="Prepare data for Passim"
)
parser.add_argument(
    "--compute_alignments_with_passim",
    action="store_true",
    help="Compute alignments with Passim",
)
parser.add_argument(
    "--create_xmls_from_passim_results",
    action="store_true",
    help="Process Passim's alignment results",
)
parser.add_argument(
    "--compiling_results_summary",
    action="store_true",
    help="Summarize results in tsv files",
)
parser.add_argument(
    "--export_xmls_to_eSc", action="store_true", help="Export results to eScriptorium"
)
parser.add_argument("--run_all", action="store_true", help="Run all steps")
parser.add_argument("--no_import", action="store_true", help="Skip the xml from eScriptorium import step")
parser.add_argument("--no_export", action="store_true", help="Skip the xml export to eScriptorium step")

args = parser.parse_args()

# The Pipeline

# Step 1. Import a document from eScriptorium
if args.import_document_from_eSc and not args.no_import:
    from src.fetch_xmls_from_eSc import initiate_xml_export

    start_time = time.time()
    initiate_xml_export(doc_pk)
    duration = time.time() - start_time
    save_timings_to_file("Step 1 (import document from eScriptorium)", duration)

# Step 2. Extract textblocks from the OCR results
if args.prepare_data_for_passim or args.run_all:
    from src.prepare_data_for_passim import build_passim_input

    start_time = time.time()
    build_passim_input(
        xmls_from_eSc_path,
        ocr_lines_dict_path,
        GT_texts_directory_path,
        input_passim_path,
    )
    duration = time.time() - start_time
    save_timings_to_file("Step 2 (prepare OCR lines for Passim)", duration)

# Step 3. Run Passim
if args.compute_alignments_with_passim or args.run_all:
    from src.compute_alignments_with_passim import run_command_and_save_output

    start_time = time.time()
    run_command_and_save_output(command_passim, output_passim_path)
    duration = time.time() - start_time
    save_timings_to_file("Step 3 (Passim computation)", duration)

# Step 4. Process the results
# Extract Passim results, select relevant alignments and update altos xml files for eScriptorium.
if args.create_xmls_from_passim_results or args.run_all:
    from src.process_alignment_results import process_passim_results

    start_time = time.time()
    process_passim_results(
        passim_out_json_path,
        lines_dict_with_alg_GT_path,
        xmls_from_eSc_path,
        xmls_for_eSc_path,
        levenshtein_threshold,
    )
    duration = time.time() - start_time
    save_timings_to_file("Step 4 (xmls update with alignments from Passim)", duration)

# Step 5. Summarize the results in tsv files
if args.compiling_results_summary or args.run_all:
    from src.build_results_summary_tsv import create_tsvs

    start_time = time.time()
    create_tsvs(alignment_register_path, doc_pk, display_n_best_gt, n_best_gt)
    duration = time.time() - start_time
    save_timings_to_file("Step 5 (Tsv with results creation)", duration)

# Step 6. Export the results to eScriptorium
if (args.export_xmls_to_eSc or args.run_all) and not args.no_export:
    from src.export_results_to_eSc import zip_alignment_files, import_zip_to_eSc

    start_time = time.time()
    zip_alignment_files(xmls_for_eSc_path, add_timestamp=True)
    import_zip_to_eSc(xmls_for_eSc_path)
    duration = time.time() - start_time
    save_timings_to_file("Step 6 (xmls export to eSc)", duration)
