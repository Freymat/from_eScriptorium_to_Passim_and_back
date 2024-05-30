import os

from paths import *
from config import *

# You can configure the pipeline by changing the parameters in the config.py file.



# Complete Pipeline

# Step 1. Import a document from eScriptorium
# The archive file has to be unzipped in the data/raw/xmls_from_eSc' folder.
# from src.fetch_xmls_from_eSc import initiate_xml_export
# if __name__ == "__main__":
#     initiate_xml_export(doc_pk)

# # Step 2. Extract textblocks from the OCR results
from src.prepare_data_for_passim import build_passim_input
if __name__ == "__main__":
    build_passim_input(xmls_from_eSc_path, ocr_lines_dict_path, GT_texts_directory_path, input_passim_path)

# # Step 3. Run Passim
from src.compute_alignments_with_passim import *
if __name__ == "__main__":
    run_command_and_save_output(command_passim, output_passim_path)

# Step 4. Process the results
# Extract Passim results, select relevant alignments and update altos XML files for eScriptorium.
from src.process_alignment_results import *
if __name__ == "__main__":
    process_passim_results(passim_out_json_path, lines_dict_with_alg_GT_path, xmls_from_eSc_path, xmls_for_eSc_path, levenshtein_threshold)

# Step 5. Summarize the results in tsv files
from src.build_results_summary_tsv import *
if __name__ == "__main__":
    create_tsvs(alignment_register_path, doc_pk,   display_n_best_gt, n_best_gt)


   
# Step 6. Optional: export the results to eScriptorium
# from src.export_results_to_eSc import *
# if __name__ == "__main__":
#     import_zip_to_eSc(xmls_for_eSc_path)
#     print(f"{root_url}/api/documents/{doc_pk}/imports/")