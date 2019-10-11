I - Preparing The Environment
    1 - Install Latest Python 3 And Select "Add Python 3.x to PATH" When Asked
    2 - Download chromedriver from here https://chromedriver.storage.googleapis.com/74.0.3729.6/chromedriver_win32.zip
    3 - Unzip chromedriver_win32.zip and move chromedriver.exe to %userprofile%\AppData\Local\Programs\Python\Python3x-32
    4 - Open Command Line And Run The Following Command
        py -3 -m pip install pypiwin32
        py -3 -m pip install selenium
    5 - Run The Program Using The Following Command In The Command Line Window Without The Leading Spaces (You Can Use Any Name For The Configuration File)
        AmazonAds.py Sample.csv

II - Notes
    1 - You Can Add As Many Products ASINs As You Wish In One Row By Repeating The Last Column
    2 - The Script Saves One Log File SampleSucceeded.csv
    3 - SampleSucceeded.csv Contains ["Search Url","Repeats","Product ASIN"] For Succeeded Trials
