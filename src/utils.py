import os
import sys
import requests
import json

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from credentials import root_url, headers
from config import doc_pk
from paths import all_parts_infos_path


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
        all_parts_infos.extend(data["results"])

        # Update the URL to the next page, or set it to None if there are no more pages
        url = data.get("next")

    # Sauvegarder les informations des parties dans un fichier json
    os.makedirs(all_parts_infos_path, exist_ok=True)
    with open(os.path.join(all_parts_infos_path, "all_parts_infos.json"), "w") as f:
        json.dump(all_parts_infos, f)

    return all_parts_infos


def load_all_parts_infos():
    """
    Get all parts informations from the folder 'eSc_parts_infos'.
    """
    # check if the file exists
    if not os.path.exists(f"{all_parts_infos_path}/all_parts_infos.json"):
        print("The file 'all_parts_infos.json' does not exist.")
        print("Loading the parts informations from the eScriptorium API.")
        get_all_parts_infos(doc_pk)
        return None
    with open(
        f"{all_parts_infos_path}/all_parts_infos.json", "r", encoding="utf-8"
    ) as json_file:
        all_parts_infos = json.load(json_file)

    return all_parts_infos


def test_connection():
    '''
    Test the connection to the server
    '''

    url = root_url

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("Connection to the server was successful")
    except requests.exceptions.RequestException as e:
        print(f"Server connection failure : {e}")


def count_xml_files(directory):
    """
    Count the number of XML files in the specified directory.

    Args:
    directory (str): The path to the directory.

    Returns:
    int: The number of XML files in the directory.
    """
    # Initialize a counter
    count = 0
    
    # Iterate over all files in the directory
    for file in os.listdir(directory):
        # Check if the file ends with .xml
        if file.endswith(".xml"):
            count += 1
    
    return count

def count_txt_files(directory):
    """
    Count the number of .txt files in the specified directory and its subdirectories.

    Args:
    directory (str): The path to the directory.

    Returns:
    int: The number of .txt files in the directory and its subdirectories.
    """
    txt_count = 0
    
    # Walk through all subdirectories and files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".txt"):
                txt_count += 1
    
    return txt_count