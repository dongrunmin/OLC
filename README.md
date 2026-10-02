## Substantial health toll of oil-induced land contamination: Evidence from satellite observations and causal inference

Abstract: Oil-induced land contamination (OLC) causes severe environmental degradation and poses substantial hazards to child health. We study how OLC affects pediatric health by combining a novel, satellite-derived deep-learning inventory of OLC in Nigeria (2016–2023) with geocoded Demographic and Health Surveys. This study first uncovers the spatiotemporal patterns of this widespread pollution, demonstrating that official oil spill records capture only a marginal fraction of the true contamination extent, leaving approximately 96% to 99% of the annual satellite-derived OLC areas entirely unrecorded. Environmentally, OLC degraded over 476.79 km² of mangroves, exposing ~1.63 million people. To assess the health burden associated with waterborne pollution, we introduce a river network model comparing downstream communities with upstream communities. We find that OLC significantly increases the risk of acute diarrhea and infant mortality downstream. Crucially, our results show that these impacts are driven by waterborne transmission and exacerbated by lacking clean water infrastructure, rather than a simple proximity effect. Furthermore, OLC-driven premature mortality introduces a survivor bias that can obscure hematological damage in surviving children. These findings suggest that risk assessments relying solely on spatial distance may underestimate actual environmental health threats if baseline infrastructure and mortality selection are not adequately considered. Interventions should prioritize targeted clean water provisions alongside dynamic hydrology-based public health measures. Our framework offers an objective, satellite-based tool for policymakers to monitor environmental injustice and evaluate the efficacy of regulatory interventions.


## Setup

### Environment

* Python 3.10 and PyTorch 2.0.1 (or later).
* Download the repo and setup the environment with:


```bash
git clone https://github.com/dongrunmin/OLC.git
cd OLC
conda env create -f environment.yml
conda activate OLC
```

### Install casual-conv1d

```bash
cd causal-conv1d

python setup.py install
```

### Install mamba

```bash
cd mamba

python setup.py install
```

### Dataset

We introduce an oil-induced land contamination (OLC) dataset for STMamba training and test. This dataset is available for download via [google drive](https://drive.google.com/file/d/1zkI9CUEV3QXiryNI3oZpND16SzKZlejC/view?usp=drive_link).

The satellite imagery is sourced from the NICFI Satellite Data Program, which provides free high-resolution satellite data for tropical regions to facilitate the sustainable development of developing countries. According to the availability and quality of the images, we used Planet Surface Reflectance data from the dry season of each year, primarily focusing on December. Each image has four spectral bands (i.e., red, green, blue, and near-infrared) with a resolution of 4.77 meters. 

For the original dataset, each sample consists of 8 images and their corresponding segmentation masks, with each image sized 512 × 512 pixels. Note that during training, images are randomly cropped to 256 × 256 pixels for augmentation. A pre-cropped evaluation dataset (256 × 256 pixels) is provided to streamline metric computation. 

The dataset is organized in the following structure:


```angular2html
├── dataset_tif/
│   ├── image/ # Training and evaluation images (512 × 512)
│   │   ├── 2016/ # Planet images from 2016
│   │   ├── 2017/ # Planet images from 2017
│   │   ├── 2018/ # Planet images from 2018
│   │   ├── 2019/ # Planet images from 2019
│   │   ├── 2020/ # Planet images from 2020
│   │   ├── 2021/ # Planet images from 2021
│   │   ├── 2022/ # Planet images from 2022
│   │   ├── 2023/ # Planet images from 2023
│   ├── label/ # Segmentation masks corresponding to images  
│   │   ├── 2016/ 
│   │   ├── 2017/  
│   │   ├── 2018/ 
│   │   ├── 2019/ 
│   │   ├── 2020/ 
│   │   ├── 2021/ 
│   │   ├── 2022/ 
│   │   ├── 2023/
├── dataset_pkl/ # Training and evaluation samples stored in pkl format (8 images and the corresponding segmentation labels)
├── test_tif/ # Pre-cropped evaluation dataset (256 × 256 pixels) 
├── csv/
│   ├── seg_train.csv/ # Training data split  
│   ├── seg_val.csv/ # Evaluation data split  
```


## Training

Please modify the data paths in `data/datasets.yaml` and `train.sh` and run command:

  ```bash
  sh train.sh
  ```


## Inference

After training the model, please modify the data paths in the following files to match your local setup:

   - `configs/Nigeria` (modify dataset and model paths)
   - `test.sh` 


Then, run command:

  ```bash
  sh test.sh
  ```



## OLC maps

We provide generated mapping results in shapefile format for Nigeria (2016-2023): https://doi.org/10.5281/zenodo.21718340.

## Health-model reproduction

The scripts in `Health_script/` perform regression analysis **after DHS records have been processed and linked to OLC, river-network, and household features**. They use one combined model-ready CSV. DHS extraction, satellite segmentation, and spatial feature generation are upstream steps and are not performed by these scripts.

### Input and environment

Place `all_living_and_deceased_model_ready.csv` in `data/health/`. The updated file has 7,162 records and 82 columns. Its variable definitions and sample rules are documented in `data/health/HEALTH_DATA_DICTIONARY.md`.

The health models require Python 3.11 or later and NumPy, pandas, SciPy, statsmodels, and scikit-learn. PyTorch, Mamba, CUDA, and satellite images are not required to run this stage. Tested dependency versions are pinned in `Health_script/requirements.txt`.

From the repository root:

```bash
python -m pip install -r Health_script/requirements.txt
python Health_script/run_health_models.py
```

To use another location for the complete CSV or results:

```bash
python Health_script/run_health_models.py --data /path/to/all_living_and_deceased_model_ready.csv --output-dir /path/to/results
```

The default paths are resolved from the scripts, so execution does not depend on the working directory. Each analysis can also be run separately with the same `--data` and `--output-dir` options:

```bash
python Health_script/01_strict_diarrhea.py
python Health_script/02_expanded_diarrhea.py
python Health_script/03_infant_mortality.py
python Health_script/04_hemoglobin_survivors.py
python Health_script/05_hemoglobin_with_deceased.py
```


## Acknowledgements

This implementation is based on [Vivim](https://github.com/scott-yjyang/Vivim.git). Thanks for their public codes.
