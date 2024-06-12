This repository is a work in progress.
Scheduled delivery date: 06/25/2024
# Aligning large quantities of digital text on large numbers of ocerized manuscripts/prints.

![alt text](images/alignment-example_1.png)

## Pipeline purpose
The function of the scripts in this repository is to enable the alignment on known digital texts with large numbers of digitized manuscripts or prints.

To improve a character recognition model, it is necessary to train it by providing it with transcribed lines of textual content.
This method is expansive in terms of time and human resources.

By aligning digital texts with manuscript images, it is possible to reduce the cost of training a character recognition model.

The principle of this pipeline is as follows:
- textual content is extracted from manuscript images using Kraken OCR software (integrated into eScriptorium).
- Using algorithmic tools like Passim, the extracted text is compared with multiple known digital texts that constitute the ground truth (GT).
- When matches are found between OCR and GT, the two texts are aligned.
- A character recognition model can then be trained on these alignments, avoiding the need to manually transcribe text from manuscript images.

The aim of this pipeline is therefore to align large numbers of known numerical texts with large numbers of documents (manuscripts or prints).

**The pipeline has been tested on batches of more than 7000 manuscript images and 150 known digital texts and corpus like the Hebrew Bible, Talmuds, Mishnah, Midrashim, etc.**

## Installation
1. Create a dedicated environment with conda:
```bash
conda create -n alignment_pipeline python=3.11
```
2. Activate the environment:
```bash
conda activate alignment_pipeline
```
3. Install [passim](https://github.com/dasmiq/passim) in the environment:
```bash
pip install git+https://github.com/dasmiq/passim.git
```
4. Clone the repository:
```bash
git clone https://github.com/Freymat/from_eScriptorium_to_Passim_and_back.git
```
5. Install the required packages:
```bash
pip install -r requirements.txt
```
6. Insert your eScriptorium token in the `credentials.py` file.

7. Configure the pipeline by modifying the `config.py` file.
More information on the configuration of the pipeline is available in the [How to use the pipeline](#how-to-use-the-pipeline) section.

## Pipeline steps

1. **Text retrieval from eScriptorium**. Altos XML files containing OCR lines from document images are retrieved from eScriptorium. The user selects the document to be processed and the regions of the page to be aligned (e.g. 'Main Central', 'Main Left').
2. **Prepare XML files for alignment**. XML files are prepared for alignment. OCR lines are extracted from the altos XML files and concatenated into blocks of text (corresponding to page regions, e.g. 'Main Central', 'Main Left'). These strings are integrated into a dictionary, which also contains a unique identifier for each block of text. Known digital texts (GT) to be aligned are added to these dictionaries. These texts come from the [Sefaria](https://www.sefaria.org/texts) API. They have been retrieved, cleaned and prepared by the script available at [this address](https://github.com/Freymat/from_Sefaria_to_Passim).
3. **Search for alignments with Passim**. Alignments are searched with [Passim](https://github.com/dasmiq/passim) via a sub-process.
4. **Alignment recovery and integration into XML files**. Valid alignments (above a certain Levenshtein distance threshold) are reintegrated into the altos XML files. The content of each OCR line is replaced by the aligned text, if valid. OCR lines without valid alignment are replaced by empty text.
5. **Summary of results**. Several summary files are generated to evaluate alignment quality. An alignment register contains alignment information for each page. Two tsv files are created, giving for each page and each GT the number of aligned lines, and the length of successive line clusters. These files are useful for quickly identifying alignments in XML/manuscript files.
6. **Re-import XML files into eScriptorium**. The modified altos files can then be reimported into eScriptorium via its API. A transcription layer is created for each GT aligned in eScriptorium. The user can then view the alignment result in eScriptorium.

Example of alignment in eScriptorium (left: picture of text page, right: alignment found with a levensthein ratio greater than 0.8) :

![alt text](images/alignment-example_2.png)

## Results
The pipeline provides the following results:
- `data/output/xmls_for_eSc/` : XML files ready to be re-imported into eScriptorium. The files are organized by ground truth (GT) detected as aligned. Once imported into eScriptorium, a transcription layer is created for each GT. The layer contains the lines selected for alignment. The other lines are empty.

- `data/output/alignment_register/` : a dictionary listing the alignments found on each page.

```json
{
        "filename": "IE87234800_00004.xml",
        "part_pk": 734751,
        "part_title": "Element 17",
        "levenshtein_threshold": 0.8,
        "total_aligned_lines_count": 17,
        "aligned_clusters_size": [
            8,
            5,
            1,
            3
        ],
        "GT_id": "Machzor_Rosh_Hashanah_Ashkenaz_clean_concatenated.txt"
    }
```
with:
    `filename`: alto file name, `part_pk` and `part_title`: page identifiers in eScriptorium, `levenshtein_treshold`: the levenshtein ratio threshold set by the user, above which the alignment is considered valid, `total_aligned_lines_count`: the number of lines aligned on the page, `aligned_clusters_size`: the number of successive lines aligned in each group of lines in the page.

- For more details on the alignment content, see the `data/processed/lines_dict_with_alg_GT` folder:

```json
{
    "text_block_id": "eSc_textblock_ab76e7e2",
    "ocr_lines_in_block": 19,
    "ocr_lines": [
        {
            "line_id": "eSc_line_4e3880cd",
            "start": 0,
            "end": 38,
            "length": 39,
            "text": "הגדול הגבור ודנורא אל עליון קונה ברחמיו",
            "alg_GT": "הגדול הגבור והנורא. אל עליון קונה",
            "GT_id": "Machzor_Rosh_Hashanah_Ashkenaz_clean_concatenated.txt",
            "GT_start": 19915,
            "GT_len": 34,
            "levenshtein_ratio": 0.861
        }
    ]
}
```
with:
    `text_block_id`: unique identifier of the text block in the xml alto file, `ocr_lines_in_block`: number of OCR lines in the block, `ocr_lines`: list of OCR lines with their alignment content, `line_id`: unique identifier of the line in the xml alto, `start`: start position of the line in the block, `end`: end position of the line in the block, `length`: length of the line, `text`: OCR line content, `alg_GT`: aligned ground truth content, `GT_id`: GT identifier, `GT_start`: start position of the GT in the GT file, `GT_len`: length of the GT line, `levenshtein_ratio`: levenshtein ratio between the OCR line and the detected GT text.

- `data/output/pipeline_timings/` : a file containing the time taken for each step of the pipeline.
```txt
Current date: 2024-05-31 15:13:35
doc_pk: 4381
Passim n-grams: 15
Spark parameters: n_cores=38, mem=90 GB, driver_mem=40 GB
Levenshtein ratio threshold: 0.7

Number of xml files processed (OCR): 962
Number of txt files processed (Ground truth texts): 151
 
Step 2 (prepare OCR lines for Passim): 0:00:05.891599
Step 3 (Passim computation): 0:09:26.488877
Step 4 (xmls update with alignments from Passim): 0:01:00.126999
Step 5 (Tsv with results creation): 0:00:23.462202
```

- ```data/output/results_summary_tsv/``` : contains tsv files with the number of total aligned lines (tsv 1) and the length of the biggest line cluster (tsv 2) for each page and each GT.

![alt text](images/tsv_pandas_biggest_cluster.png)
Parameters `display_n_best_gt = true` and `n_best_gt` can be set in the `config.py` file to insert in the dataframe the n best GT for each part.

![alt text](images/tsv_pandas_nbest.png)

## How to use the pipeline

### 1. Set the credentials:
Insert your eScriptorium API access token in the `credentials.py` file. This token is required to import and export XML files from eScriptorium.

### 2. Configure the pipeline:
The configuration file `config.py` contains the parameters required for pipeline execution:

#### Document informations in eScriptorium
- `doc_pk` (int): the id of the document containing manuscript/prints in eScriptorium.(e.g. doc_pk = 4381)
- `region_type_pk_list` (list) : the list of region types in the page, where to look for alignments. The regions are defined in eScriptorium, and are called 'MainCentral', 'MainLeft', 'MainRight', etc. Give the region type pk for each region to be processed as a list. (e.g. region_type_pk_list = [6909, 6910])
- `transcription_level_pk` (int): the transcription level in eScriptorium where the OCR lines are stored. (e.g. transcription_level_pk = 10754). This involves that a transcription layer has been created in eScriptorium before running the pipeline.

#### Passim parameters:
- `n` (int): character n-gram order for alignment detection with Passim. Other [passim parameters](https://github.com/dasmiq/passim?tab=readme-ov-file#controlling-passims-n-gram-filtering) can be set. To do this, modify the `command_passim` parameter in the`src/compute_alignments_with_passim.py` file.
- `n_cores` (int): number of threads (Spark argument)
- `mem` (int): memory per node, in GB (Spark argument)
- `driver_mem` (int): memory for the driver, in GB (Spark argument)

#### Results filtering parameter:
`levenshtein_threshold` (int): for every OCR line with an alignment found by Passim, the Levenshtein ratio beetween OCR and GT is calculated. If this ratio is above the threshold, the alignment is considered valid.

#### Results summary (tsv) parameters
Two tsv files are created in the `data/output/results_summary_tsv/` folder. They contain the number of aligned lines and the length of the biggest line cluster for each page and each GT. The following parameters can be set:

`display_n_best_gt` (bool): if True, the best GT for each part will be displayed at the beginning of the tsv file.

`n_best_gt` (int): the number of best GT to display in the tsv file.

### 3. Get your xml alto files (OCR) from eScriptorium
After having set the doc_pk you want to retrieve from eScriptorium in the `config.py`, you can import the xml files with the following command:

```bash
python main.py --import_document_from_eSc
```
**Important**: It's not possible to download and save the xml files from eScriptorium automatically in the folder `data/raw/xmls_from_eSc/`. The import is initiated by the `--import_document_from_eS` command, and the user has to download the files manually from eScriptorium and place them in the folder `data/raw/xmls_from_eSc/`, before running the pipeline.

##### Running the pipeline without connection to eScriptorium:
It is possible to run the pipeline without connection to eScriptorium, using local XML files. The advantage is that you can use the pipeline on very large quantities of pages (xmls) without having to import them into eScriptorium.
To do this, set the variables in the `config.py` file as follows:
```python
eSc_connexion = False
doc_pk = None 
region_type_pk_list = [ None ]
transcription_level_pk = None
```
The xmls files must be placed in the `data/raw/xmls_from_eSc/` folder.


### 4. Run the pipeline:
After having put the xml files in the `data/raw/xmls_from_eSc/` folder, you can run the pipeline.

The available commands are displayed with:
```bash
python main.py --help
```

To run the pipeline, use the following command:
```bash
python main.py --run_all --no_import
```
This will compute the alignments, create the results summary tsv files, and export the XML files to eScriptorium.

If you want to skip the export to eScriptorium:
```bash
python main.py --run_all --no_import --no_export
```

You can run each step of the pipeline separately with the following commands:
``` bash
--import_document_from_eSc  # Import document from eScriptorium
--prepare_data_for_passim   # Prepare data for Passim
--compute_alignments_with_passim    # Compute alignments with Passim
--create_xmls_from_passim_results   # Process Passim's alignment results
--compiling_results_summary     # Summarize results in tsv files
--export_xmls_to_eSc    # Export results to eScriptorium
```

### 5. Check the results:
The results are available in the `data/output/` folder. The `xmls_for_eSc` folder contains the XML files ready to be re-imported into eScriptorium. The `alignment_register` folder contains a dictionary listing the alignments found on each page. The `pipeline_timings` folder contains a file with the time taken for each step of the pipeline. The `results_summary_tsv` folder contains tsv files with the number of total aligned lines and the length of the biggest line cluster for each page and each GT.

### 6. Backup the results:
You can backup the results with the command:
```bash
python main.py --backup_results
```
A .zip file with a timestamp is created in the `data/results_backups` folder.
### 7. Clean the pipeline:
The pipeline generates a large number of files. To clean the output folders, use the following command:
(Beware: this command will delete all files in the output folders, make sure to backup the results before running it)
```bash
python main.py --clean_all
```
You can choose the data you want to delete with the following commands:


```bash
  --clean_except_xmls
```
Clean the pipeline, but keep the XML files. Useful if you want to re-run the pipeline without having to re-import the XML files from eScriptorium.
```bash
  --clean_except_passim
```
Clean the pipeline, but keep the Passim results and the xmls from eScriptorium. Useful if you want to tweak the levensthein treshold.



