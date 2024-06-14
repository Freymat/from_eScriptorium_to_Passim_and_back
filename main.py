import os
import time
from datetime import timedelta, datetime
from contextlib import contextmanager
import argparse

from src.utils import test_connection, count_xml_files, count_txt_files

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
    eSc_connexion,
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
from src.make_clean import (
    clean_pipeline_from_zero,
    keep_xmls_from_esc_and_clean,
    keep_passim_results_and_clean,
)
from src.backup_results import backup_pipeline_results


@contextmanager
def time_this_to_file(step_name):
    print(f"Starting {step_name}...")
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        print(f"Finished {step_name}. Duration: {timedelta(seconds=duration)}")
        save_timings_to_file(step_name, duration)


# Test the connection
if eSc_connexion:
    test_connection()
else:
    print("Working without connection to eScriptorium.")


# Function to save results in a text file
def save_timings_to_file(step_name, duration):
    formatted_duration = str(timedelta(seconds=duration))
    with open(os.path.join(timings_path, "timings.txt"), "a") as file:
        file.write(f"{step_name}: {formatted_duration}\n")


# Save the pipeline parameters in a log file
def save_pipeline_parameters():
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.exists(timings_path):
        os.makedirs(timings_path)

    timings_file_path = os.path.join(timings_path, "timings.txt")
    n_xmls_processed = count_xml_files(xmls_from_eSc_path)
    n_txts_processed = count_txt_files(GT_texts_directory_path)

    # Open the file in write mode to overwrite the content
    with open(timings_file_path, "w") as file:
        file.write(f"Current date: {current_date}\n")
        file.write("\n")
        file.write(f"doc_pk: {doc_pk}\n")
        file.write(f"Passim n-grams: {n}\n")
        file.write(
            f"Spark parameters: n_cores={n_cores}, mem={mem} GB, driver_mem={driver_mem} GB\n"
        )
        file.write(f"Levenshtein ratio threshold: {levenshtein_threshold}\n")
        file.write("\n")
        file.write(f"Number of xml files processed (OCR): {n_xmls_processed}\n")
        file.write(
            f"Number of txt files processed (Ground truth texts): {n_txts_processed}\n "
        )
        file.write("\n")


# Argparse setup
parser = argparse.ArgumentParser(
    description="Pipeline for massive matching between OCR-extracted texts and known digital editions to produce large quantities of ground truth for training OCR models."
)

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


# Save the pipeline parameters at the start if we are not only backing up results
if not args.backup_results:
    save_pipeline_parameters()

# The Pipeline

# Step 1. Import a document from eScriptorium
if args.import_document_from_eSc and not args.no_import:
    with time_this_to_file("Step 1 (import document from eScriptorium)"):
        initiate_xml_export(doc_pk)

# Step 2. Extract textblocks from the OCR results
if args.prepare_data_for_passim or args.run_all:
    with time_this_to_file("Step 2 (prepare OCR lines for Passim)"):
        build_passim_input(
            xmls_from_eSc_path,
            ocr_lines_dict_path,
            GT_texts_directory_path,
            input_passim_path,
        )

# Step 3. Run Passim
if args.compute_alignments_with_passim or args.run_all:
    with time_this_to_file("Step 3 (Passim computation)"):
        print(command_passim)
        run_command_and_save_output(command_passim, output_passim_path)

# Step 4. Process the results
if args.create_xmls_from_passim_results or args.run_all:
    with time_this_to_file("Step 4 (xmls update with alignments from Passim)"):
        process_passim_results(
            passim_out_json_path,
            lines_dict_with_alg_GT_path,
            xmls_from_eSc_path,
            xmls_for_eSc_path,
            levenshtein_threshold,
        )

# Step 5. Summarize the results in tsv files
if args.compiling_results_summary or args.run_all:
    with time_this_to_file("Step 5 (Tsv with results creation)"):
       create_tsvs(alignment_register_path)

# Step 6. Export the results to eScriptorium
if (args.export_xmls_to_eSc or args.run_all) and not args.no_export:
    with time_this_to_file("Step 6 (xmls export to eSc)"):
        zip_alignment_files(xmls_for_eSc_path, add_timestamp=True)
        import_zip_to_eSc(xmls_for_eSc_path)


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
