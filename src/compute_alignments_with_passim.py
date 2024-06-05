import os
import sys
import subprocess

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config import n, n_cores, mem, driver_mem
from paths import input_passim_path, output_passim_path


# Check if output_passim_path exists, if not create it


def create_output_passim_folder():
    if not os.path.exists(output_passim_path):
        os.makedirs(output_passim_path)
    return output_passim_path


create_output_passim_folder()

command_passim = f"SPARK_SUBMIT_ARGS='--master local[{n_cores}] --executor-memory {mem}G --driver-memory {driver_mem}G' seriatim --docwise --floating-ngrams --fields ref --filterpairs 'ref = 1 AND ref2 = 0' --all-pairs --complete-lines -n {n} {input_passim_path} {output_passim_path}"


def run_command_and_save_output(command, output_dir):
    """
    Exécute une commande shell, capture la sortie standard et les erreurs, et les enregistre dans des fichiers.

    :param command: La commande shell à exécuter.
    :param output_dir: Le chemin du dossier où enregistrer la sortie et les erreurs.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, "passim_output.log")
    error_file = os.path.join(output_dir, "passim_output.err")

    try:
        # Opens output and error files
        with open(output_file, "w", encoding="utf-8") as stdout_file, open(
            error_file, "w", encoding="utf-8"
        ) as stderr_file:
            # Executes command and redirects output and errors
            result = subprocess.run(
                command, shell=True, stdout=stdout_file, stderr=stderr_file, text=True
            )

        # Optional: Displays the command return code
        print(f"Command executed with return code: {result.returncode}")
        print(f"Logs and results saved in: {output_dir}")
        return result.returncode

    except Exception as e:
        print(f"An error occurred while executing the command: {e}")
        return None
