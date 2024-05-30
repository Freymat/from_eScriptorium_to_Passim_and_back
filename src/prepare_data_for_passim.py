import os
import sys
import glob
import json
import jsonlines
from xml.etree import ElementTree

# Add 'src' parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from config import *
from paths import *

# Initialize the list where output datas for Passim will be stored
def initialize_passim_input():
    global passim_input
    passim_input = []
    return passim_input

def extract_ocr_textblocks(xmls_from_eSc_path, ocr_lines_dict_path):
    """ This script reads the XML alto files produced by eScriptorium,
    extracts and concatenate the text of the ocr lines from each TextBlock elements.

    The result is a list of dictionaries, one per alto file.
    Each dictionnary contains the list of the text blocks in the file. Each element of this list is a dictionary containing:
    - the concatenated text of the lines in the TextBlock element,
    - the ID of the TextBlock element,
    - the IDs of the TextLine elements in the text block, and the starting position of each line in the concatenated text.
    """

    # Initialize list to store parts
    parts = []

    # Loop through all XML files in the directory
    for filename in glob.glob(os.path.join(xmls_from_eSc_path, "*.xml")):
        # Obtenir le nom de chaque fichier
        basename = os.path.splitext(os.path.basename(filename))[0]

        # Initialize list to store text blocks
        blocks = []

        # Parse the XML file
        tree = ElementTree.parse(filename)
        root = tree.getroot()

        # Loop through all TextBlock elements in the XML file
        for text_block in root.iter("{http://www.loc.gov/standards/alto/ns-v4#}TextBlock"):
            # Obtenir l'ID de l'attribut ID de l'élément TextBlock
            text_block_id = text_block.get("ID")

            lines = []
            continuous_text = ""
            char_count = 0  # Initial position for continuous text

            # Loop through all TextLine elements in the TextBlock element
            for text_line in text_block.iter("{http://www.loc.gov/standards/alto/ns-v4#}TextLine"):
                text = text_line.find("{http://www.loc.gov/standards/alto/ns-v4#}String").get("CONTENT").strip()

                line_dict = {
                    "line_id": text_line.get("ID"),
                    "start": char_count,  # Start position of line in continuous text
                    "end" : char_count + len(text) - 1,
                    "length": len(text),
                    "text": text
                }
                separator = "\n"
                continuous_text += (text + separator)
                char_count += len(text + separator)  # Updates the starting position for the next line.

                lines.append(line_dict)

            # Add text block to block list
            blocks.append({
                "ocr_block_text": continuous_text.strip(),  # Removes superfluous spaces at the beginning and end
                "text_block_id": text_block_id,
                "ocr_lines_in_block": len(lines),  # Number of lines in the block
                "ocr_lines": lines,
                "series": 'OCR'  # Distinguishes OCR from control
            })

        # Ajouter un document avec ses blocs correspondants à la liste des parties
        parts.append({
            "filename": basename,
            "ocr_lines_in_part": sum([block["ocr_lines_in_block"] for block in blocks]),
            "ocr_blocks": blocks,
            # total number of ocr lines in the xml part, for the selected text regions
            "ocr_lines_in_part": sum([block["ocr_lines_in_block"] for block in blocks])
        })

    # Check that the directory exists before saving the file
    ocr_lines_dict_dir = os.path.dirname(ocr_lines_dict_path)
    if not os.path.exists(ocr_lines_dict_dir):
        os.makedirs(ocr_lines_dict_dir)

    # Save the 'parts' dictionnary to a JSON file
    with open(ocr_lines_dict_path, "w", encoding="utf-8") as file_handler:
        json.dump(parts, file_handler, ensure_ascii=False, indent=4)

def add_OCR_textblocks_to_passim_input(ocr_lines_dict_path):
    '''
    Read the JSON file containing the OCR textblocks and build the input for Passim.
    GT texts still need to be added to the input. 
    '''
    # open the dictionnary
    with open(ocr_lines_dict_path, "r", encoding="utf-8") as f:
        parts = json.load(f)        
    
    for part in parts:
        for block in part["ocr_blocks"]:
            text_block_id = block["text_block_id"]
            text_block_text = block["ocr_block_text"]
            filename = part["filename"]
            passim_input.append({"id": text_block_id +'_' + filename, "series": 'OCR',"ref": '0', "text": text_block_text})
            # print(text_block_id, filename)
    # print(passim_input)
    return passim_input

def add_GT_texts_to_passim_input(GT_texts_directory_path):
    '''
    Add every digital witness text to the passim_input list 
    '''
    for root, dirs, files in os.walk(GT_texts_directory_path):
        for file in files:
            if file.endswith(".txt"):
                text_file = os.path.join(root, file)
                with open(text_file, "r", encoding="utf-8") as file_handler:
                    text = file_handler.read()
                    filename = os.path.basename(text_file)
                    passim_input.append({"id": filename, "series": 'GT', "ref": '1', "text": text})
                    # print(f"Added to output: {filename}")
       # print(passim_input)
    return passim_input

def write_passim_input_to_json(input_passim_path, passim_input):
    ''' 
    Write Data to JSONLines File in compact format without ASCII Encoding, for Passim
    '''
    # Check that the directory exists before saving the file
    input_passim_dir = os.path.dirname(input_passim_path)
    if not os.path.exists(input_passim_dir):
        os.makedirs(input_passim_dir)

    # Open the output file in write mode
    with open(input_passim_path, "w", encoding="utf-8") as file_handler:
        # Create a jsonlines writer object that writes to the output file
        writer = jsonlines.Writer(file_handler)
        # Loop through each item in the output_data list
        for item in passim_input:
            # Write the current item to the output file using the jsonlines writer
            writer.write(item)
    print(f"input file for passim created: {input_passim_path}")

def build_passim_input(xmls_from_eSc_path, ocr_lines_dict_path, GT_texts_directory_path, input_passim_path):
    '''
    Build the input for Passim from the OCR textblocks and the GT texts.
    Parameters:
    - xmls_from_eSc_path: path to the directory containing the XML alto files imported from eScriptorium, containing the OCR results.
    - ocr_lines_dict_path: path to the JSON file that will contain the extracted textblocks from OCR.
    - GT_texts_directory_path: path to the directory containing the ground truth texts.
    - input_passim_path: path for the output JSON file. This file will be used as input for Passim.
    '''
    # Initialize the list where output datas for Passim will be stored
    initialize_passim_input()
    # Extract OCR textblocks from XML alto files imported from eScriptorium
    extract_ocr_textblocks(xmls_from_eSc_path, ocr_lines_dict_path)
    # Add OCR textblocks to the passim_input list
    add_OCR_textblocks_to_passim_input(ocr_lines_dict_path)
    # Add GT texts to the passim_input list
    add_GT_texts_to_passim_input(GT_texts_directory_path)
    # Write the passim_input list to a JSON file
    write_passim_input_to_json(input_passim_path, passim_input)

if __name__ == "__main__":
    build_passim_input(xmls_from_eSc_path, ocr_lines_dict_path, GT_texts_directory_path, input_passim_path)
