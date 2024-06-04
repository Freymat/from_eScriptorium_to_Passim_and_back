import os
import time
from datetime import timedelta, datetime
import argparse


from paths import (
    timings_path,
    xmls_from_eSc_path,
    ocr_lines_dict_path,
    GT_texts_directory_path,
    input_passim_path,
    output_passim_path,
    passim_out_json_path,
    xmls_for_eSc_path,
    lines_dict_with_alg_GT_path,
    alignment_register_path,
)
from config import (
    doc_pk,
    n,
    n_cores,
    mem,
    driver_mem,
    levenshtein_threshold,
    display_n_best_gt,
    n_best_gt,
)

from src.fetch_xmls_from_eSc import initiate_xml_export
from src.prepare_data_for_passim import build_passim_input
from src.compute_alignments_with_passim import (
    command_passim,
    run_command_and_save_output,
)
from src.process_alignment_results import process_passim_results
from src.build_results_summary_tsv import create_tsvs
from src.export_results_to_eSc import zip_alignment_files, import_zip_to_eSc
from src.make_clean import clean_pipeline_from_zero, keep_xmls_from_esc_and_clean, keep_passim_results_and_clean
from src.backup_results import backup_pipeline_results


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
parser = argparse.ArgumentParser(description="Pipeline for massive matching between OCR-extracted texts and known digital editions to produce large quantities of ground truth for training OCR models.")

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
parser.add_argument(
    "--no_import",
    action="store_true",
    help="Skip the xml from eScriptorium import step",
)
parser.add_argument(
    "--no_export", action="store_true", help="Skip the xml export to eScriptorium step"
)

parser.add_argument(
    "--clean_all",
    action="store_true",
    help="Clean the pipeline from zero",
)

parser.add_argument(
    "--clean_except_xmls",
    action="store_true",
    help="Clean the pipeline, except the XMLs from eScriptorium",
)

parser.add_argument(
    "--clean_except_passim",
    action="store_true",
    help="Clean the pipeline, except the Passim results",
)

parser.add_argument(
    "--backup_results",
    action="store_true",
    help="Backup the pipeline results",
)

args = parser.parse_args()


# The Pipeline

# Step 1. Import a document from eScriptorium
if args.import_document_from_eSc and not args.no_import:

    start_time = time.time()
    initiate_xml_export(doc_pk)
    duration = time.time() - start_time
    save_timings_to_file("Step 1 (import document from eScriptorium)", duration)

# Step 2. Extract textblocks from the OCR results
if args.prepare_data_for_passim or args.run_all:

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

    start_time = time.time()
    run_command_and_save_output(command_passim, output_passim_path)
    duration = time.time() - start_time
    save_timings_to_file("Step 3 (Passim computation)", duration)

# Step 4. Process the results
# Extract Passim results, select relevant alignments and update altos xml files for eScriptorium.
if args.create_xmls_from_passim_results or args.run_all:

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

    start_time = time.time()
    create_tsvs(alignment_register_path, doc_pk, display_n_best_gt, n_best_gt)
    duration = time.time() - start_time
    save_timings_to_file("Step 5 (Tsv with results creation)", duration)

# Step 6. Export the results to eScriptorium
if (args.export_xmls_to_eSc or args.run_all) and not args.no_export:

    start_time = time.time()
    zip_alignment_files(xmls_for_eSc_path, add_timestamp=True)
    import_zip_to_eSc(xmls_for_eSc_path)
    duration = time.time() - start_time
    save_timings_to_file("Step 6 (xmls export to eSc)", duration)

# Tool: Clean the pipeline

if args.clean_all:
    clean_pipeline_from_zero()

if args.clean_except_xmls:
    keep_xmls_from_esc_and_clean()

if args.clean_except_passim:
    keep_passim_results_and_clean()

# Tool: backup the pipeline results

if args.backup_results:
    backup_pipeline_results()
