import os
import sys
import shutil


# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from paths import (
    xmls_from_eSc_path,
    all_parts_infos_path,
    input_passim_path,
    lines_dict_with_alg_GT_path,
    ocr_lines_dict_path,
    output_passim_path,
    alignment_register_path,
    timings_path,
    results_summary_tsv_path,
    xmls_for_eSc_path,
)


def clean_folder(folder):
    """
    Clean the specified folder by deleting all its contents,
    including files and subdirectories.

    Parameters:
    - folder (str): The path to the folder to be cleaned.
    """
    # Parcours récursif des fichiers et répertoires
    for root, dirs, files in os.walk(folder, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Failed to remove file {file_path}: {e}")
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                shutil.rmtree(dir_path)
            except Exception as e:
                print(f"Failed to remove directory {dir_path}: {e}")


def clean_pipeline_from_zero():
    """
    Clean the complete pipeline.
    """
    try:
        # data/raw/xmls_from_eSc
        clean_folder(xmls_from_eSc_path)

        # data/processed
        processed_folder = [
            all_parts_infos_path,
            os.path.dirname(input_passim_path),
            lines_dict_with_alg_GT_path,
            os.path.dirname(ocr_lines_dict_path),
            output_passim_path,
        ]
        for folder in processed_folder:
            clean_folder(folder)

        # data/output
        output_folder = [
            alignment_register_path,
            timings_path,
            results_summary_tsv_path,
            xmls_for_eSc_path,
        ]
        for folder in output_folder:
            clean_folder(folder)

        print("Pipeline cleaned from zero.")
    except Exception as e:
        print(f"Error cleaning pipeline: {e}")


def keep_xmls_from_esc_and_clean():
    """
    Clean all the pipeline results, except the XMLs altos from eScriptorium.
    This allows to re-run the pipeline, without having to re-import the document from eScriptorium.
    """
    try:
        
        # data/processed
        processed_folder = [
            all_parts_infos_path,
            os.path.dirname(input_passim_path),
            lines_dict_with_alg_GT_path,
            os.path.dirname(ocr_lines_dict_path),
            output_passim_path,
        ]
        for folder in processed_folder:
            clean_folder(folder)

        # data/output
        output_folder = [
            alignment_register_path,
            timings_path,
            results_summary_tsv_path,
            xmls_for_eSc_path,
        ]
        for folder in output_folder:
            clean_folder(folder)

        print("Pipeline cleaned, except the XMLs from eScriptorium.")
    except Exception as e:
        print(f"Error cleaning pipeline: {e}")


def keep_passim_results_and_clean():
    """
    Clean the pipeline results, except the Passim results. This allows to re-run the pipeline from the Passim step, and tune the levenshtein threshold.
    """
    try:
        
        # data/output
        output_folder = [
            alignment_register_path,
            timings_path,
            results_summary_tsv_path,
            xmls_for_eSc_path,
        ]
        for folder in output_folder:
            clean_folder(folder)

        print("Pipeline cleaned, but Passim results are kept.")
    except Exception as e:
        print(f"Error cleaning pipeline: {e}")
