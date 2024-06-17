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
from config import eSc_connexion, levenshtein_threshold, n, doc_pk, n_best_gt


def load_alignment_register(alignment_register_path):
    """
    Load the alignment register from the JSON file.
    This file contains all the results of the alignment process.
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

    # Drop the 'ocr_blocks' column, as we only need the number of OCR lines
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

    # if eSc_connexion:
    #     # Insert the information from eSc: doc_pk, part_pk, title
    #     joined_df_with_ocr_lines = insert_infos_from_eSc(
    #         joined_df_with_ocr_lines, eSc_connexion, doc_pk
    #     )

    # # Add a row index column
    # joined_df_with_ocr_lines = joined_df_with_ocr_lines.with_row_index("id", offset=1)

    save_df_as_tsv(joined_df_with_ocr_lines, "results_based_on_total_aligned_lines")

    return sorted_df


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

    # save_df_as_tsv(sorted_df, 'sorted_df_max_aligned_clusters_size')

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

    # if eSc_connexion:
    #     # Insert the information from eSc: doc_pk, part_pk, title
    #     joined_df_with_ocr_lines = insert_infos_from_eSc(
    #         joined_df_with_ocr_lines, eSc_connexion, doc_pk
    #     )

    # # Add a row index column
    # joined_df_with_ocr_lines = joined_df_with_ocr_lines.with_row_index("id", offset=1)

    save_df_as_tsv(joined_df_with_ocr_lines, "results_based_on_biggest_cluster_length")

    return sorted_df

def create_overall_results_tsv(alignment_register):
    """
    Create a tsv files summarizing the results based on the total aligned lines and the biggest cluster length.
    This file will be used to create tops (best GTs ranking) for each part.   
    """

    sorted_df_total_aligned_lines = create_tsv_total_aligned_lines(alignment_register)
    sorted_df_max_cluster_length = create_tsv_max_cluster_length(alignment_register)

    # join the two DataFrames
    joined_df = sorted_df_total_aligned_lines.join(
        sorted_df_max_cluster_length,  on=["filename", "GT_id"], how="outer")


    # Select only the relevant columns for the final output
    joined_df = joined_df.select([
        "filename",
        "GT_id",
        "total_aligned_lines",
        "max_aligned_clusters_size"
    ])
    # Insert the number of total ocr lines in the dataframe
    df_ocr_lines = prepare_ocr_lines_df(ocr_lines_dict_path)
    joined_df_with_ocr_lines = insert_ocr_lines(
        base_df=joined_df, df_ocr_lines=df_ocr_lines
    )

    # Insert the aligned line ratio
    # in % rounded to 1 decimal places
    joined_df_with_ocr_lines = joined_df_with_ocr_lines.with_columns(
        (pl.col("total_aligned_lines") / pl.col("ocr_lines_in_part") * 100).round(1).alias("aligned_lines_ratio")
        .alias("aligned_lines_ratio"))
    

    # reorder columns
    columns_reordered = [
        "filename",        
        "GT_id",
        "ocr_lines_in_part",
        "total_aligned_lines",
        "aligned_lines_ratio",
        "max_aligned_clusters_size",
    ]
    joined_df_with_ocr_lines = joined_df_with_ocr_lines.select(columns_reordered)
    print(joined_df_with_ocr_lines.head())
    return joined_df_with_ocr_lines


def get_top_gt_ids(df, n_best_gt, sort_column):
    """
    Get the top n_best_gt GT_ids for each filename, based on the sort_column.
    returns a list of lists with the filename, GT_id, and the value of the sort_column.
    """
    top_gt_ids_list = []
    grouped = df.group_by('filename').agg([
        pl.col('GT_id').sort(descending=True).head(n_best_gt).alias('Top_GT_ids'),
        pl.col(sort_column).sort(descending=True).head(n_best_gt).alias('Top_total_aligned_lines')
    ])
    for row in grouped.iter_rows(named=True):
        filename = row['filename']
        top_gt_ids = row['Top_GT_ids']
        top_aligned_lines = row['Top_total_aligned_lines']
        entry = [filename]
        for gt_id, aligned_lines in zip(top_gt_ids, top_aligned_lines):
            entry.append(gt_id)
            entry.append(aligned_lines)
        # Compléter avec "None" si moins de top_n GT_id trouvés
        while len(entry) < 2 * n_best_gt + 1:
            entry.append(None)
        top_gt_ids_list.append(entry)
    return top_gt_ids_list

def build_top_gt_tsv(top_gt_ids_list, n_best_gt):
    """
    Build the results summary TSV file, with the top GT_ids for each filename.
    Takes the list of top GT_ids for each filename as input (get_top_gt_ids).
    Returns a DataFrame.        
    """

    columns = ['filename']
    for i in range(1, n_best_gt + 1):
        columns.append(f'Top{i}_GT_id')
        columns.append(f'total_aligned_lines_{i}')

    # Convertir en DataFrame
    top_gt_df = pl.DataFrame(top_gt_ids_list, schema=columns)

    return top_gt_df

df = create_overall_results_tsv(alignment_register_path)
top_gt_ids_list = get_top_gt_ids(df, n_best_gt, sort_column='total_aligned_lines')
top_gt_df = build_top_gt_tsv(top_gt_ids_list, n_best_gt)
print(top_gt_df.head())























# def create_tsvs(alignment_register):
#     """
#     Create TSV files with the results of the alignment process.
#     """
#     sorted_df_total_aligned_lines = create_tsv_total_aligned_lines(alignment_register)
#     sorted_df_max_cluster_length = create_tsv_max_cluster_length(alignment_register)

#     # join the two DataFrames
#     joined_df = sorted_df_total_aligned_lines.join(
#         sorted_df_max_cluster_length,  on=["filename", "GT_id"], how="outer")


#     # Select only the relevant columns for the final output
#     joined_df = joined_df.select([
#         "filename",
#         "GT_id",
#         "total_aligned_lines",
#         "max_aligned_clusters_size"
#     ])
#     # Insert the number of total ocr lines in the dataframe
#     df_ocr_lines = prepare_ocr_lines_df(ocr_lines_dict_path)
#     joined_df_with_ocr_lines = insert_ocr_lines(
#         base_df=joined_df, df_ocr_lines=df_ocr_lines
#     )

#     # reorder columns
#     columns_reordered = [
#         "filename",        
#         "GT_id",
#         "ocr_lines_in_part",
#         "total_aligned_lines",
#         "max_aligned_clusters_size",
#     ]
#     joined_df_with_ocr_lines = joined_df_with_ocr_lines.select(columns_reordered)


#     if eSc_connexion:
#         # Insert the information from eSc: doc_pk, part_pk, title
#         joined_df_with_ocr_lines = insert_infos_from_eSc(
#             joined_df_with_ocr_lines, eSc_connexion, doc_pk
#         )

  

#     # Add a row index column
#     joined_df_with_ocr_lines = joined_df_with_ocr_lines.with_row_index("id", offset=1)


#     save_df_as_tsv(joined_df_with_ocr_lines, "Overall_results")

