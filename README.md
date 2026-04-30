# tess-flare-detection
Using traditional threshold method and machine learning method Stella to detect flares in TESS 2-min light curves

## Data preperation
Before using both models to detect flares, there are several steps needed to prepare the data.
First, to download the light curves from MAST, downloading_lightcurves.py in src is needed. You can input a .csv file that records the target stars' TIC id and sector. Then, the algorithms will download the light curves from MAST automatically.
Second, to use the traditional threshold method, the data need to be normalized. To achieve this, normalize_flux.py in src can be helpful.

## Flare detection
To use the traditional threshold method to deteect flares, you need to open the serch.set and then set everything by following instructions in the file.
After that, run the traditional_threshold_method.py in src to detect flares.

To use the CNN model Stella to detect flares, you only need to input the light curves before normalized into cnn_model_stella.py in src.

## Event matching
To match the results detected by models with the benchmark, event_matching_and_recall.py in the src will be helpful. 
You can input your benchmark and the model's results. 
Then, the output will be a .csv file that records all flares correctly detected by the model. Moreover, the recall rate will be calculated in the terminal.