# ANNOTE

## Annotation of Time-series Events
![alt text](annote.png)
Annotation of Time-series Events (ANNOTE) is a new annotation software. 
It enables the loading of 
longitudinal, time-series data from audio files or CSV 
files. It provides visualization of up to three 
one-dimensional data signals, such as audio or sensor data, 
allowing users to select regions to indicate event start 
and end points. Dynamic label adjustments adapt to user 
requirements, while the user-friendly nature of the 
software ensures accessibility for professionals and 
non-professionals alike. ANNOTE's streamlined annotation 
process accelerates the development of models and 
applications that rely on annotated time-series data.

# Highlights
- Load audio files or CSV files
- Visualize up to three one-dimensional data signals
- Annotate start and end points of events
- Dynamic label adjustments


# Contents
- [Getting started](#getting-started)
- [Authors](#authors)
- [License](#license)
- [Citation](#citation)


## Getting started
We provide:
- an example for a [labels file](src/annote/labels_file_example.json)

## Requirements
To use ANNOTE, you need to have Python 3.8.10  on your system. It was only tested on this Python version.


### Install with pip

````
pip install git+https://github.com/ankilab/ANNOTE.git
````

or

````    
git clone https://github.com/ankilab/ANNOTE.git
cd ANNOTE
pip install .
annote
````

## Loading annotations from .annote
To save annotations we use the [flammkuchen package](https://github.com/portugueslab/flammkuchen). 
The saved files can be accessed in the following way:
    
````   
import flammkuchen as fl
annotations = fl.load('path/to/file.annote')
print(annotations)
````

## Troubleshooting common issues
- Using Ubuntu: If you get an error message like `qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.` 
  you can try to install the following `sudo apt install libxcb-cursor0`.


## Authors
- René Groh ([rene.groh@fau.de](mailto:rene.groh@fau.de]))
- Jie Yu Li
- Nicole Y. K. Li-Jessen
- Andreas M. Kist 

## License
The project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Citation
If you use ANNOTE in your research, please cite our paper:

```
@article{groh2024annote,
  title={ANNOTE: Annotation of time-series events},
  author={Groh, Ren{\'e} and Li, Jie Yu and Li-Jessen, Nicole YK and Kist, Andreas M},
  journal={Software Impacts},
  volume={21},
  pages={100679},
  year={2024},
  publisher={Elsevier}
}
```

