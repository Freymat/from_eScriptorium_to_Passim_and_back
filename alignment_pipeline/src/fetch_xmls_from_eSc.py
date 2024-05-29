import os
import sys
import json
import requests

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config import root_url, headers, headersbrief, doc_pk, region_type_pk_list, transcription_level_pk, all_parts_infos_path

from utils import get_all_parts_infos


def export_xml(doc_pk, part_pk_list, tr_level_pk, region_type_pk_list, include_undefined=True, include_orphan=True, file_format='alto', include_images=False, print_status=True):
    # e.g. https://escriptorium.openiti.org/api/documents/3221/export/
    export_url = f"{root_url}/api/documents/{doc_pk}/export/"
    
    # Create a copy of region_type_pk_list to avoid modifying the original list
    region_types = region_type_pk_list.copy()

    # Add 'Undefined' to region_types if include_undefined is True
    if include_undefined:
        region_types.append('Undefined')

    # Add 'Orphan' to region_types if include_orphan is True
    if include_orphan:
        region_types.append('Orphan')

    data = {'parts': part_pk_list, 'transcription': tr_level_pk, 'task': 'export',
            'region_types': region_types, 'include_images': include_images, 'file_format': file_format}
    
    # e.g. {"parts": [755434], "transcription": 5631, "task": "export", "region_types": [2,'Undefined','Orphan'], "include_images" : False, "file_format": "alto"}
    res = requests.post(export_url, data=data, headers=headersbrief)
    if print_status:
        print(res.status_code)
        print(res.content)
    return res


if __name__ == "__main__":
    print(f"doc_pk: {doc_pk}")

    # get all the parts from the document
    all_parts = get_all_parts_infos(doc_pk)
    part_pk_list = [part['pk'] for part in all_parts]
    print(f"{len(part_pk_list)} parts found")
    print(f"region_type_pk_list: {region_type_pk_list}")

    # Initiate the export of the XMLs altos on eScriptorium instance
    # The XMLs will have to be downloaded manually from the eScriptorium interface
    # And saved in the 'data/raw/xmls_from_eSc' folder
    export_xml(doc_pk, part_pk_list, transcription_level_pk, region_type_pk_list, include_undefined=True,
               include_orphan=True, file_format='alto', include_images=False, print_status=True)
    
    print(f"XMLs export initiated. Please download the XMLs from your eScriptorium instance ({root_url}) and unzip them in the 'data/raw/xmls_from_eSc' folder.")
