import os
import sys
import json
import polars as pl

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.utils import load_all_parts_infos
from paths import alignment_register_path, results_summary_tsv_path
from config import eSc_connexion, levenshtein_threshold, n, doc_pk


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


def create_tsv_total_aligned_lines(alignment_register):
    """
    Create a TSV file creates a TSV file with aligned lines counts for each GT and image.
    Takes the alignment register (list of dictionnaries) as input.
    """
    data = load_alignment_register(alignment_register)

    # Create a Polars DataFrame from data
    df = pl.DataFrame(data)

    # Group by filename and GT_id, then give the max value total_aligned_lines_count for each group.
    grouped_df = df.group_by(["filename", "GT_id"]).agg(
        pl.max("total_aligned_lines_count").alias("total_aligned_lines")
    )

    # Sort data by filename and total_aligned_lines_sum in descending order
    sorted_df = grouped_df.sort(
        by=["filename", "total_aligned_lines"], descending=[False, True]
    )

    # Find the GT_id with the largest total_aligned_lines_sum for each filename and keep the value.
    result_df = sorted_df.group_by("filename").agg(
        pl.col("GT_id")
        .first()
        .alias("GT_id_Top1"),  # Renommer la colonne GT_id en GT_id_Top1
        pl.col("total_aligned_lines").first().alias("total_aligned_lines"),
    )

    # Ajouter une colonne pour chaque GT_id avec le nombre de total_aligned_lines_count pour chaque filename
    pivot_df = grouped_df.pivot(
        values="total_aligned_lines", index="filename", columns="GT_id"
    )

    # Joindre les deux DataFrames
    final_df = result_df.join(pivot_df, on="filename", how="left")

    # Export the DataFrame as a TS fileV

    if not os.path.exists(results_summary_tsv_path):
        os.makedirs(results_summary_tsv_path)

    output_file_path = os.path.join(
        results_summary_tsv_path,
        f"results_based_on_total_alg_lines_doc_pk_{doc_pk}_n{n}_lev_{levenshtein_threshold}.tsv",
    )
    final_df.write_csv(output_file_path, separator="\t")


def create_tsv_max_cluster_length(alignment_register):
    """
    Create a TSV file creates a TSV file with aligned lines counts for each GT and image.
    Takes the alignment register (list of dictionnaries) as input.
    """
    data = load_alignment_register(alignment_register)

    # Create a Polars DataFrame from data
    df = pl.DataFrame(data)

    # create a new column with the max value of 'aligned_clusters_size' for each row
    df_with_max_cluster_size = df.with_columns(
        pl.col("aligned_clusters_size")
        .map_elements(lambda x: max(x), return_dtype=pl.Int64)
        .alias("max_aligned_clusters_size")
    )

    # Group by filename and GT_id, then give the max value max_aligned_clusters_size for each group.
    grouped_df = df_with_max_cluster_size.group_by(["filename", "GT_id"]).agg(
        pl.max("max_aligned_clusters_size").alias("max_aligned_clusters_size")
    )

    # Sort data by filename and max_aligned_clusters_size in descending order
    sorted_df = grouped_df.sort(
        by=["filename", "max_aligned_clusters_size"], descending=[False, True]
    )

    # Find the GT_id with the largest max_aligned_clusters_size for each filename and keep the value.
    result_df = sorted_df.group_by("filename").agg(
        pl.col("GT_id")
        .first()
        .alias("GT_id_Top1"),  # Renommer la colonne GT_id en GT_id_Top1
        pl.col("max_aligned_clusters_size").first().alias("max_aligned_clusters_size"),
    )

    # Add a column for each GT_id with the number of max_aligned_clusters_size for each filename
    pivot_df = grouped_df.pivot(
        values="max_aligned_clusters_size", index="filename", columns="GT_id"
    )

    # Join the two DataFrames
    final_df = result_df.join(pivot_df, on="filename", how="left")

    # Export DataFrame as TSV file

    if not os.path.exists(results_summary_tsv_path):
        os.makedirs(results_summary_tsv_path)

    output_file_path = os.path.join(
        results_summary_tsv_path,
        f"results_based_on_max_cluster_length_doc_pk_{doc_pk}_n{n}_lev_{levenshtein_threshold}.tsv",
    )
    final_df.write_csv(output_file_path, separator="\t")
