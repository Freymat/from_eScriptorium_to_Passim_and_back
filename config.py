import os

# eSc connexion
# Set to False if you want to run the pipeline locally (no imports or exports to eScriptorium).
# this allows to run the pipeline on numerous xmls altos directly saved in the 'data/raw/xmls_from_eSc' folder.
# Set to True if you want to import a document from eScriptorium, and then export the results back to eScriptorium.
eSc_connexion = True

# Document informations in eScriptorium
doc_pk = 4381 # set to None if eSc_connexion is False
region_type_pk_list = [
    6909, 8356, 8355
]  # Region type pk list, e.g., [6909] or [6909, 6910, 6911], or [None] if eSc_connexion is False
transcription_level_pk = 11691
  # Transcription level pk, set to None if eSc_connexion is False

# Passim parameters
n = 7
n_cores = 6  # Number of threads (Spark argument)
mem = 8  # Memory per node, in GB (Spark argument)
driver_mem = 4  # Memory for the driver, in GB (Spark argument)

# Filtering parameters
# aligned lines with a levenshtein ratio > threshold will be kept.
levenshtein_threshold = 0.8

# Results summary (tsv) parameters
# Choose to display the n best GT for part
display_n_best_gt = True
# Number of best GT to display
n_best_gt = 5
