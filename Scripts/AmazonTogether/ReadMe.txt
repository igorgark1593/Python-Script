I - Describing Files
    1 - AmazonCommon.py Is A Common Script Between Most Amazon Scripts
    2 - AmazonTogether.py Is The Script To Perform Adding To Cart
    3 - BrowserCommon.py Is A Common Script Between Most Scripts
    4 - ReadMe.txt Is This Help File
    5 - Sample.csv Is A Sample Configuration File That Demonestrates The Format Used To Configure Together Script

II - Preparing The Environment
    1 - Install Multilogin
    2 - Go to %username%\.multiloginapp.com
    3 - Open app.properties And Add The Following Line As A New Line Without The Leading Spaces
        multiloginapp.port = 35000
    4 - Run Multilogin And Login To The Account
    5 - Install Latest Python 3 And Select "Add Python 3.x to PATH" When Asked
    6 - Open Command Line And Run The Following Commands
        A - py -3 -m pip install pyclick
        B - py -3 -m pip install requests
        C - py -3 -m pip install selenium
    7 - Fill Configuration File As In The Sample.csv File (You Can Change The Name Of The File As You Wish)
    8 - Run The Program Using The Following Command In The Command Line Window Without The Leading Spaces (You Can Use Any Name For The Configuration File)
        AmazonTogether.py Sample.csv

III - Notes
    1 - Try To Adjust The Resolution Of Each Profile To Let It Open In A Full Screen Or At Least Making It Large Enough To Display The Full Width Of The Pages
    2 - Don't Delete The Header Row In The Configuration File As The Script Will Always Escape That First Row
    3 - The Indexes Of Rows Start From 2 As The First Row Is Always The Headers
    4 - Only Use One Row After The Header While Testing, After You Finish Testing You Can Use As Many Rows As You Wish
    5 - ProfileId Is Shown When You Click The Profile In The Multilogin Application
    6 - You Need To Put The Password In The Configuration File As The Script Will Try To Login To The Account If It Is Not Already Logged In
    7 - FromDelay And ToDelay Are Two Numbers That The Script Will Use To Wait For Random Time In Minutes Before Executing The Row
        For Example If FromDelay Is 60 And ToDelay Is 180 The Script Will Wait For A Number Of Minutes Between 1 And 2 Hours Before Executing The Row
        FromDelay And ToDelay Can Be 0 If You Don't Want This Feature
    8 - The Script Saves Three Log Files SampleSucceededData.csv, SampleSucceeded.csv, and SampleFailed.csv
    9 - SampleSucceededData.csv Contains Data Of Rows That Have Been Completed Successfully
   10 - SampleSucceeded.csv Contains The Indexes Of Rows That Have Been Completed Successfully And The Script Will Escape Those Rows If You Rerun It
   11 - SampleFailed.csv Contains The Indexes Of Rows That Have Been Failed Along With The Reason Of Failure Which I Can Use To Debug The Failure
