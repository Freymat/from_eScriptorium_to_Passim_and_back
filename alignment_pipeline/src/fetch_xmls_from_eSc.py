import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.functions import export_xml
from modules.packages import *


def get_all_parts_infos(doc_pk):
    """
    Get all parts information from the eScriptorium API, handling pagination to retrieve all pages.
    """
    url = f"https://msia.escriptorium.fr/api/documents/{doc_pk}/parts/"
    all_parts_infos = []

    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        all_parts_infos.extend(data['results'])
        
        # Update the URL to the next page, or set it to None if there are no more pages
        url = data.get('next')
    
    # save the parts information in a json file
    # if the directory does not exist, create it
    all_parts_infos_path = f'eSc_parts_infos'
    if not os.path.exists(all_parts_infos_path):
        os.makedirs(all_parts_infos_path)
    with open(f'{all_parts_infos_path}/all_parts_infos.json', 'w') as f:
        json.dump(all_parts_infos, f)

    
    return all_parts_infos

# get all the parts from the document
all_parts = get_all_parts_infos(doc_pk)

# get the part pk list
part_pk_list = [ part['pk'] for part in all_parts ]

print(f"{len(part_pk_list)} parts found")

# get the xmls of the parts from eScriptorium
export_xml(doc_pk,part_pk_list,tr_level_pk,region_type_pk_list,include_undefined = False, include_orphan = False, file_format = 'alto',include_images = False, print_status = True)