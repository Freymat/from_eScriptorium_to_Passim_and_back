import os
import sys
import requests
import json

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config import root_url, headers, all_parts_infos_path

def get_all_parts_infos(doc_pk):
    """
    Retrieve all part information from the eScriptorium API, managing pagination to retrieve all pages.
    """
    url = f"{root_url}/api/documents/{doc_pk}/parts/"
    all_parts_infos = []

    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        all_parts_infos.extend(data['results'])

        # Update the URL to the next page, or set it to None if there are no more pages
        url = data.get('next')

    # Sauvegarder les informations des parties dans un fichier json
    os.makedirs(all_parts_infos_path, exist_ok=True)
    with open(os.path.join(all_parts_infos_path, 'all_parts_infos.json'), 'w') as f:
        json.dump(all_parts_infos, f)

    return all_parts_infos
