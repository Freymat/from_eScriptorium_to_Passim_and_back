import os
from credentials import get_serverinfo, serverconnections

# Server parameters
servername = "msIA"

# Fetch server connection details
root_url, headers, headersbrief = get_serverinfo(servername, serverconnections)
print(f"Server URL: {root_url}")

# Document informations in eScriptorium
doc_pk = 4381
region_type_pk_list = [
    6909
]  # Region type pk list, e.g., [6909] for {'pk': 6909, 'name': 'MainCentral'}
transcription_level_pk = 10754  # Transcription level pk

# Passim parameters
n = 7
n_cores = 6  # Number of threads (Spark argument)
mem = 8  # Memory per node, in GB (Spark argument)
driver_mem = 4  # Memory for the driver, in GB (Spark argument)

# Filering parameters
# aligned lines with a levenshtein ratio > threshold will be kept.
levenshtein_threshold = 0.8

# Results summary (tsv) parameters
# Choose to display the n best GT for part
display_n_best_gt = True
# Number of best GT to display
n_best_gt = 5
