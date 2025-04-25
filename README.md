## The Hidden Cost of Stolen Oil: Measuring the Scale of Illegal Oil-induced Land Contamination


Abstract: Oil theft and illegal artisanal refining pose significant threats to environmental health, energy security, and regional stability, hindering progress toward the United Nations Sustainable Development Goals in oil-rich regions. However, the clandestine nature of these activities and the difficulty in distinguishing their environmental impacts from those of legal oil operations have obscured their spatiotemporal patterns and ecological consequences. To address this gap, we proposed a novel detection framework for illegal oil-induced land contamination (IOLC), leveraging its persistent and cumulative characteristics as an objective indicator for large-scale, long-term analysis. By integrating high-resolution, time-series, and multi-spectral satellite imagery with our developed deep learning model, we systematically mapped IOLC areas across Nigeria from 2016 to 2023. Our results show that illegal oil operations directly degraded over 470 km² of mangrove ecosystems and 63 km² of forests, affecting ~1.63 million people. Correlational analysis further revealed that these activities are closely tied to fluctuations in global crude oil prices and domestic conflict events. This study provides the first high-resolution, quantitative assessment of illegal oil-induced environmental degradation, offering actionable insights for evidence-based policymaking and intervention in vulnerable regions and beyond.


## Setup

### Environment

* Python 3.10 and PyTorch 2.0.1 (or later).
* Download the repo and setup the environment with:


```bash
git clone https://github.com/dongrunmin/IOLC.git
cd IOLC
conda env create -f environment.yml
conda activate IOLC
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

We introduce an illegal oil-induced land contamination (IOLC) dataset for STMamba training and test. This dataset is available for download via [google drive](https://drive.google.com/file/d/1zkI9CUEV3QXiryNI3oZpND16SzKZlejC/view?usp=drive_link).

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



## IOLC maps

We provide generated mapping results in shapefile format for Nigeria (2016-2023):

```angular2html
mapping_results/shp_2016-2023/
│── 2016/
│── 2017/
│── ...
└── 2023/
```


## Acknowledgements

This implementation is based on [Vivim](https://github.com/scott-yjyang/Vivim.git). Thanks for their public codes.


