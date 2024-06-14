import os
import sys
import json
import polars as pl

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.utils import load_all_parts_infos
from paths import alignment_register_path, results_summary_tsv_path, ocr_lines_dict_path
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


def prepare_ocr_lines_df(ocr_lines_dict_path):
    """
    Prepare the OCR lines DataFrame before joining it.
    """
    with open(ocr_lines_dict_path, "r") as f:
        data = json.load(f)

    df_ocr_lines = pl.DataFrame(data)

    # add '.xml' to every value in the 'filename' column
    df_ocr_lines = df_ocr_lines.with_columns(
        (pl.col("filename") + ".xml").alias("filename")
    )

    # Drop the 'ocr_blocks' column
    df_ocr_lines = df_ocr_lines.drop("ocr_blocks")

    return df_ocr_lines


def insert_ocr_lines(base_df, df_ocr_lines):
    """
    Insert the number of total ocr lines in the dataframe.
    """

    df_ocr_lines = prepare_ocr_lines_df(ocr_lines_dict_path)
    joined_df = base_df.join(df_ocr_lines, on="filename", how="left", coalesce=True)

    # Reorder columns
    columns_reordered = ["filename", "ocr_lines_in_part"] + [
        col for col in joined_df.columns if col not in ["filename", "ocr_lines_in_part"]
    ]
    joined_df_with_ocr_lines = joined_df.select(columns_reordered)

    return joined_df_with_ocr_lines


def save_df_as_tsv(df, file_name):
    """
    Save a Polars DataFrame as a TSV file.
    """
    # Export the DataFrame as a TS fileV
    if not os.path.exists(results_summary_tsv_path):
        os.makedirs(results_summary_tsv_path)

    output_file_path = os.path.join(
        results_summary_tsv_path,
        f"{file_name}_doc_pk_{doc_pk}_n{n}_lev_{levenshtein_threshold}.tsv",
    )

    df.write_csv(output_file_path, separator="\t")


def insert_infos_from_eSc(base_df, eSc_connexion, doc_pk):
    """
    Insert in the DataFrame the information from eSc: doc_pk, part_pk, title.
    From the all_parts_infos.json file.
    """
    all_parts_infos = load_all_parts_infos()
    df_all_parts_infos = pl.DataFrame(all_parts_infos)

    # keep only the fields: 'pk', filename', 'title'
    df_all_parts_infos = df_all_parts_infos.select(["pk", "filename", "title"])
    print(df_all_parts_infos.head())

    # Rename column 'pk' to 'part_pk
    df_all_parts_infos = df_all_parts_infos.select(
        [(pl.col("pk").alias("part_pk")), "filename", "title"]
    )

    # In the 'filename' column, replace '.jpg' with '.xml'
    df_all_parts_infos = df_all_parts_infos.with_columns(
        [(pl.col("filename").str.replace(".jpg", ".xml")).alias("filename")]
    )

    # Join on the 'filename' column
    joined_df = base_df.join(
        df_all_parts_infos, on="filename", how="left", coalesce=True
    )
    joined_df.head()

    # Add to joined_df a new column 'doc_pk' with the value of doc_pk
    joined_df = joined_df.with_columns(pl.lit(doc_pk).alias("doc_pk"))

    # Reorder columns
    columns_reordered = [
        "filename",
        "doc_pk",
        "part_pk",
        "title",
        "ocr_lines_in_part",
    ] + [
        col
        for col in joined_df.columns
        if col not in ["filename", "doc_pk", "part_pk", "title", "ocr_lines_in_part"]
    ]
    joined_df = joined_df.select(columns_reordered)

    return joined_df


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
        .alias("best_GT_1_id"),  # Renommer la colonne GT_id en GT_id_Top1
        pl.col("total_aligned_lines").first().alias("best_GT_1_aligned_lines_count"),
    )

    # Add a column for each GT_id with the number of total_aligned_lines_count for each filename
    pivot_df = grouped_df.pivot(
        values="total_aligned_lines", index="filename", columns="GT_id"
    )

    # Join the two DataFrames
    joined_df = result_df.join(pivot_df, on="filename", how="left")

    # Insert the number of total ocr lines in the dataframe
    df_ocr_lines = prepare_ocr_lines_df(ocr_lines_dict_path)
    joined_df_with_ocr_lines = insert_ocr_lines(
        base_df=joined_df, df_ocr_lines=df_ocr_lines
    )

    if eSc_connexion:
        # Insert the information from eSc: doc_pk, part_pk, title
        joined_df_with_ocr_lines = insert_infos_from_eSc(
            joined_df_with_ocr_lines, eSc_connexion, doc_pk
        )

    # Add a row index column
    joined_df_with_ocr_lines = joined_df_with_ocr_lines.with_row_index("id", offset=1)

    save_df_as_tsv(joined_df_with_ocr_lines, "results_based_on_total_aligned_lines")


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
        .alias("best_GT_1_id"),  # Rename GT_id column to GT_id_Top1
        pl.col("max_aligned_clusters_size")
        .first()
        .alias("best_GT_1_biggest_cluster_length"),
    )

    # Add a column for each GT_id with the number of max_aligned_clusters_size for each filename
    pivot_df = grouped_df.pivot(
        values="max_aligned_clusters_size", index="filename", columns="GT_id"
    )

    # Join the two DataFrames
    joined_df = result_df.join(pivot_df, on="filename", how="left")

    # Insert the number of total ocr lines in the dataframe
    df_ocr_lines = prepare_ocr_lines_df(ocr_lines_dict_path)
    joined_df_with_ocr_lines = insert_ocr_lines(
        base_df=joined_df, df_ocr_lines=df_ocr_lines
    )

    if eSc_connexion:
        # Insert the information from eSc: doc_pk, part_pk, title
        joined_df_with_ocr_lines = insert_infos_from_eSc(
            joined_df_with_ocr_lines, eSc_connexion, doc_pk
        )

    # Add a row index column
    joined_df_with_ocr_lines = joined_df_with_ocr_lines.with_row_index("id", offset=1)

    save_df_as_tsv(joined_df_with_ocr_lines, "results_based_on_biggest_cluster_length")
