import os
import sys
import json
import concurrent.futures

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.utils import load_all_parts_infos
from paths import ocr_lines_dict_path, results_summary_tsv_path
from config import eSc_connexion, levenshtein_threshold, n, n_cores


def load_alignment_register(alignment_register_path):
    """
    Load the alignment register from the JSON file.
    """
    # Build full path to JSON file
    json_file_path = os.path.join(alignment_register_path, "alignment_register.json")

    if not os.path.exists(json_file_path):
        print(f"The file {json_file_path} doesn't exist.")
        return None

    try:
        with open(json_file_path, "r", encoding="utf-8") as json_file_handler:
            return json.load(json_file_handler)
    except Exception as e:
        print(f"Error reading file {json_file_path}: {e}")
        return None


def create_aligned_counts_by_image(alignment_register):
    """
    Create a dictionary with aligned lines counts for each image and GT.
    This function is used to prepare the data for the TSV file.
    Sorting the datas by image and GT will make it easier to compare the results.
    """
    # Collect all unique GT_ids
    gt_ids = sorted(set(entry["GT_id"] for entry in alignment_register))

    # Initialize a dictionary to hold aligned lines counts for each image
    aligned_counts_by_image = {
        entry["filename"]: {
            gt_id: {"total_aligned_lines_count": 0, "aligned_clusters_size": []}
            for gt_id in gt_ids
        }
        for entry in alignment_register
    }

    # Fill the dictionary
    for entry in alignment_register:
        filename = entry["filename"]
        gt_id = entry["GT_id"]
        total_aligned_lines_count = entry["total_aligned_lines_count"]
        aligned_clusters_size = entry["aligned_clusters_size"]

        aligned_counts_by_image[filename][gt_id][
            "total_aligned_lines_count"
        ] = total_aligned_lines_count
        aligned_counts_by_image[filename][gt_id][
            "aligned_clusters_size"
        ] = aligned_clusters_size

    return aligned_counts_by_image


def identify_top_n_best_gt_based_on_total_alg_lines(aligned_counts_by_image, n_best_gt):
    """
    Identify the n best GTs for each image based on the total number of aligned lines.
    Parameters:
    - aligned_counts_by_image: dictionary with aligned lines counts for each image and GT
    - n_best_gt: number of best GTs to identify
    """
    top_n_best_gt = {}
    for filename, gt_counts in aligned_counts_by_image.items():
        # Sort GTs by total aligned lines count in descending order
        sorted_gt_counts = sorted(
            gt_counts.items(),
            key=lambda x: x[1]["total_aligned_lines_count"],
            reverse=True,
        )
        # Take top n GTs
        top_n_gt_counts = sorted_gt_counts[:n_best_gt]
        top_n_best_gt[filename] = [
            (gt_id, counts["total_aligned_lines_count"])
            for gt_id, counts in top_n_gt_counts
        ]
    return top_n_best_gt


def identify_top_n_best_gt_based_on_biggest_cluster_size(
    aligned_counts_by_image, n_best_gt
):
    """
    Identify the n best GTs for each image based on the size of the biggest cluster.
    A cluster is a group of successive aligned lines.
    Parameters:
    - aligned_counts_by_image: dictionary with aligned lines counts for each image and GT
    - n_best_gt: number of best GTs to identify
    """
    top_n_best_gt = {}
    for filename, gt_counts in aligned_counts_by_image.items():
        # Sort GTs by the size of the biggest cluster in descending order
        sorted_gt_counts = sorted(
            gt_counts.items(),
            key=lambda x: max(x[1]["aligned_clusters_size"], default=0),
            reverse=True,
        )
        # Take top n GTs
        top_n_gt_counts = sorted_gt_counts[:n_best_gt]
        top_n_best_gt[filename] = [
            (gt_id, max(counts["aligned_clusters_size"], default=0))
            for gt_id, counts in top_n_gt_counts
        ]
    return top_n_best_gt


def get_nb_of_ocr_lines_in_file(filename):
    """
    Get the number of OCR lines in the selected region of the document.
    Parameters:
    - filename of the image. Extension should be .jpg, but the function
    handles the case where the extension is missing or different.
    """
    # Load dictionary containing OCR line-splitting information
    with open(ocr_lines_dict_path, "r", encoding="utf-8") as json_file:
        ocr_lines_dict = json.load(json_file)

    filename, extension = os.path.splitext(filename)

    for file in ocr_lines_dict:
        if file["filename"] == filename:
            nb_of_ocr_lines = file["ocr_lines_in_part"]
            break
    return nb_of_ocr_lines


def get_pk_from_filename(all_parts_infos, filename):
    """
    Function to get the pk and the title in eScriptorium of a part from its filename.
    Parameters:
    - all_parts_infos: list of dictionaries containing informations about the parts.
    requested from the eScriptorium API. This dictionnary is requested
    from the eScriptorium API outisde of this function to avoid multiple requests.
    - filename of the image. Extension should be .jpg, but the function
    handles the case where the extension is missing or different.
    """
    filename, extension = os.path.splitext(filename)
    for item in all_parts_infos:
        if item["filename"] == filename + ".jpg":
            return (item["pk"], item["title"])
    return (None, None)


def create_tsv_total_alg_lines(
    aligned_counts_by_image, doc_pk, top_n_best_gt, display_n_best_gt, n_best_gt
):
    """
    Subfunction that creates a TSV file with aligned lines counts for each GT and image.
    If display_n_best_gt is True, include columns for the n best GTs with most aligned lines.
    The TSV is based on the aligned_counts_by_image dictionary.
    """
    # Collect all unique GT_ids
    gt_ids = sorted(
        set(
            gt_id
            for gt_counts in aligned_counts_by_image.values()
            for gt_id in gt_counts.keys()
        )
    )

    # Update TSV header
    tsv_header = "count\tdoc_pk\tfilename\tpart_pk\ttitle\tnb_of_ocr_lines\t"
    if display_n_best_gt:
        tsv_header += (
            "\t".join(
                f"best_GT_{i}_id\tbest_GT_{i}_aligned_lines_count"
                for i in range(1, n_best_gt + 1)
            )
            + "\t"
        )
    tsv_header += "\t".join(gt_ids) + "\n"

    # Create TSV rows
    tsv_rows = ""
    if eSc_connexion:
        all_parts_infos = load_all_parts_infos()
    else:
        doc_pk = "N/A"
    count = 1  # Initialize counter
    for filename, gt_counts in aligned_counts_by_image.items():
        # Retrieve the number of OCR lines in the file
        nb_of_ocr_lines = get_nb_of_ocr_lines_in_file(filename)

        if eSc_connexion:
            # Retrieve PK and title based on filename
            part_pk, title = get_pk_from_filename(all_parts_infos, filename)
        else:
            part_pk, title = None, None

        # Make sure part_pk and title are never None
        part_pk = part_pk if part_pk is not None else "N/A"
        title = title if title is not None else "N/A"

        # Add count, doc_pk, part_pk, title, nb_of_ocr_lines
        row = f"{count}\t{doc_pk}\t{filename}\t{part_pk}\t{title}\t{nb_of_ocr_lines}\t"
        count += 1

        if display_n_best_gt:
            if filename in top_n_best_gt:
                for i in range(1, n_best_gt + 1):
                    if i - 1 < len(top_n_best_gt[filename]):
                        gt_id, aligned_lines_count = top_n_best_gt[filename][i - 1]
                    else:
                        gt_id, aligned_lines_count = "", ""
                    row += f"{gt_id}\t{aligned_lines_count}\t"
            else:
                row += "\t" * (n_best_gt * 2)

        for gt_id in gt_ids:
            total_aligned_lines_count = gt_counts.get(gt_id, {}).get(
                "total_aligned_lines_count", ""
            )
            row += str(total_aligned_lines_count) + "\t"
        tsv_rows += row.strip() + "\n"

    return tsv_header + tsv_rows


def create_tsv_biggest_cluster_size(
    aligned_counts_by_image, doc_pk, top_n_best_gt, display_n_best_gt, n_best_gt
):
    """
    Subfunction that creates a TSV file with the biggest cluster size for each GT and image.
    If display_n_best_gt is True, include columns for the n best GTs with the largest cluster size.
    The TSV is based on the aligned_counts_by_image dictionary.
    """
    # Collect all unique GT_ids
    gt_ids = sorted(
        set(
            gt_id
            for gt_counts in aligned_counts_by_image.values()
            for gt_id in gt_counts.keys()
        )
    )

    # Update TSV header
    tsv_header = "count\tdoc_pk\tfilename\tpart_pk\ttitle\tnb_of_ocr_lines\t"
    if display_n_best_gt:
        tsv_header += (
            "\t".join(
                f"best_GT_{i}_id\tbest_GT_{i}_biggest_cluster_size"
                for i in range(1, n_best_gt + 1)
            )
            + "\t"
        )
    tsv_header += "\t".join(gt_ids) + "\n"

    # Create TSV rows
    tsv_rows = ""
    if eSc_connexion:
        all_parts_infos = load_all_parts_infos()
    else:
        doc_pk = "N/A"
    count = 1  # Initialize counter
    for filename, gt_counts in aligned_counts_by_image.items():
        # Retrieve the number of OCR lines in the file
        nb_of_ocr_lines = get_nb_of_ocr_lines_in_file(filename)

        if eSc_connexion:
            # Retrieve PK and title based on filename
            part_pk, title = get_pk_from_filename(all_parts_infos, filename)
        else:
            part_pk, title = None, None

        # Make sure part_pk and title are never None
        part_pk = part_pk if part_pk is not None else "N/A"
        title = title if title is not None else "N/A"

        # Add count, doc_pk, part_pk, title, nb_of_ocr_lines
        row = f"{count}\t{doc_pk}\t{filename}\t{part_pk}\t{title}\t{nb_of_ocr_lines}\t"
        count += 1

        if display_n_best_gt:
            if filename in top_n_best_gt:
                for i in range(1, n_best_gt + 1):
                    if i - 1 < len(top_n_best_gt[filename]):
                        gt_id, biggest_cluster_size = top_n_best_gt[filename][i - 1]
                    else:
                        gt_id, biggest_cluster_size = "", ""
                    row += f"{gt_id}\t{biggest_cluster_size}\t"
            else:
                row += "\t" * (n_best_gt * 2)

        for gt_id in gt_ids:
            biggest_cluster_size = max(
                gt_counts.get(gt_id, {}).get("aligned_clusters_size", [0]), default=0
            )
            row += str(biggest_cluster_size) + "\t"
        tsv_rows += row.strip() + "\n"

    return tsv_header + tsv_rows


def create_tsv_total_alg_lines_from_alignment_register(
    alignment_register, doc_pk, display_n_best_gt=True, n_best_gt=1
):
    """
    Global function that creates a TSV file with the number of aligned lines for each GT and image.
    This function can give the n best GT for each image.
    Rows: one row per image (filename from the XML file)
    Columns:
    - one column per Ground Truth (GT_ids)
    - one column with the number of aligned lines for the best GT
    - additional columns for n best GTs with most aligned lines (optional)
    """
    aligned_counts_by_image = create_aligned_counts_by_image(alignment_register)
    top_n_best_gt = identify_top_n_best_gt_based_on_total_alg_lines(
        aligned_counts_by_image, n_best_gt
    )
    tsv_content = create_tsv_total_alg_lines(
        aligned_counts_by_image, doc_pk, top_n_best_gt, display_n_best_gt, n_best_gt
    )

    # Ensure the results directory exists
    if not os.path.exists(results_summary_tsv_path):
        os.makedirs(results_summary_tsv_path)

    # Write to file in the results directory
    tsv_file_path = os.path.join(
        results_summary_tsv_path,
        f"results_based_on_total_alg_lines_doc_pk_{doc_pk}_n{n}_lev_{levenshtein_threshold}.tsv",
    )
    with open(tsv_file_path, "w") as tsv_file:
        tsv_file.write(tsv_content)


def create_tsv_biggest_cluster_size_from_alignment_register(
    alignment_register, doc_pk, display_n_best_gt=True, n_best_gt=1
):
    """
    Global function that creates a TSV file with the number of aligned lines for each GT and image.
    This function can give the n best GT for each image.
    Rows: one row per image (filename from the XML file)
    Columns:
    - one column per Ground Truth (GT_ids)
    - one column with the number of aligned lines for the best GT
    - additional columns for n best GTs with most aligned lines (optional)
    """
    aligned_counts_by_image = create_aligned_counts_by_image(alignment_register)
    top_n_best_gt = identify_top_n_best_gt_based_on_biggest_cluster_size(
        aligned_counts_by_image, n_best_gt
    )
    tsv_content = create_tsv_total_alg_lines(
        aligned_counts_by_image, doc_pk, top_n_best_gt, display_n_best_gt, n_best_gt
    )

    # Ensure the results directory exists
    if not os.path.exists(results_summary_tsv_path):
        os.makedirs(results_summary_tsv_path)

    # Write to file in the results directory
    tsv_file_path = os.path.join(
        results_summary_tsv_path,
        f"results_based_on_biggest_cluster_size_doc_pk_{doc_pk}_n{n}_lev_{levenshtein_threshold}.tsv",
    )
    with open(tsv_file_path, "w") as tsv_file:
        tsv_file.write(tsv_content)


def create_tsvs(alignment_register_path, doc_pk, display_n_best_gt, n_best_gt):
    """
    This is the global function that creates the TSV files with the results summary.
    """
    # Load alignment register
    alignment_register = load_alignment_register(alignment_register_path)

    # Create aligned counts by image
    create_aligned_counts_by_image(alignment_register)

    # Définir le nombre maximal de processus en parallèle
    max_workers = n_cores

    # Create a ThreadPoolExecutor with the maximum number of parallel processes
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks to the executor
        future_total = executor.submit(
            identify_top_n_best_gt_based_on_total_alg_lines,
            aligned_counts_by_image,
            n_best_gt,
        )
        future_cluster = executor.submit(
            identify_top_n_best_gt_based_on_biggest_cluster_size,
            aligned_counts_by_image,
            n_best_gt,
        )

        # Retrieve task results
        top_n_best_gt_total = future_total.result()
        top_n_best_gt_cluster = future_cluster.result()

    # Create TSV total aligned lines from alignment register
    create_tsv_total_alg_lines_from_alignment_register(
        alignment_register, doc_pk, top_n_best_gt_total, display_n_best_gt, n_best_gt
    )

    # Create TSV biggest cluster size from alignment register
    create_tsv_biggest_cluster_size_from_alignment_register(
        alignment_register, doc_pk, top_n_best_gt_cluster, display_n_best_gt, n_best_gt
    )

    print(f"TSV files created in {results_summary_tsv_path}.")
