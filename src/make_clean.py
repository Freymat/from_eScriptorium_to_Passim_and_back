import os
import sys
import shutil


# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


def clean_folder(folder):
    """
    Clean the specified folder by deleting all its contents, including files and subdirectories.

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
    Clean the output folders.
    """
    # data/input
    clean_folder(xmls_from_eSc_path)

    # data/processed
    processed_folder = os.path.join(project_root, "data", "processed")
    clean_folder(processed_folder)

    # data/output
    output_folder = os.path.join(project_root, "data", "output")
    clean_folder(output_folder)

    print("Pipeline cleaned from zero.")


def keep_xmls_from_esc_and_clean():
    """
    Clean all the pipeline results, except the XMLs altos from eScriptorium.
    This allows to re-run the pipeline, without having to re-import the document from eScriptorium.
    """
    # data/processed
    processed_folder = os.path.join(project_root, "data", "processed")
    clean_folder(processed_folder)

    # data/output
    output_folder = os.path.join(project_root, "data", "output")
    clean_folder(output_folder)

    print("Pipeline cleaned, except the XMLs from eScriptorium.")


def keep_passim_results_and_clean():
    """
    Clean the pipeline results, except the Passim results. This allows to re-run the pipeline from the Passim step, and modify Passim parameters for example.
    """
    # data/processed
    clean_folder(lines_dict_with_alg_GT_path)
    clean_folder(output_passim_path)

    # data/output
    output_folder = os.path.join(project_root, "data", "output")
    clean_folder(output_folder)

    print("Pipeline cleaned, except the Passim results.")
