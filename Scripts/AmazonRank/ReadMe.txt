I - Preparing The Environment
    1 - Install Multilogin
    2 - Go to %username%\.multiloginapp.com
    3 - Open app.properties And Add The Following Line As A New Line Without The Leading Spaces
        multiloginapp.port = 35000
    4 - Run Multilogin And Login To The Account
    5 - Install Latest Python 3 And Select "Add Python 3.x to PATH" When Asked
    6 - Open Command Line And Run The Following Commands
        py -3 -m pip install pyclick
        py -3 -m pip install requests
        py -3 -m pip install selenium
    7 - Fill Configuration File As In The Sample.csv File (You Can Change The Name Of The File As You Wish)
    8 - Run The Program Using The Following Command In The Command Line Window Without The Leading Spaces (You Can Use Any Name For The Configuration File)
        AmazonRank.py Sample.csv

II - Notes
    1 - Try To Adjust The Resolution Of Each Profile To Let It Open In A Full Screen Or At Least Making It Large Enough To Display The Full Width Of The Pages
    2 - Don't Delete The Header Row In The Configuration File As The Script Will Always Escape That First Row
    3 - The Numbers Of Rows Start From 2 As The First Row Is Always The Headers
    4 - Only Use One Row After The Header While Testing, After You Finish Testing You Can Use As Many Rows As You Wish
    5 - "Min Delay" And "Max Delay" Are Two Numbers That The Script Will Use To Wait For Random Time In Minutes Before Executing The Row
        For Example If "Min Delay" Is 60 And "Max Delay" Is 180 The Script Will Wait For A Number Of Minutes Between 60 And 180 Minutes Before Executing The Row
        "Min Delay" And "Max Delay" Can Be 0 If You Don't Want The Script To Wait Before The Specified Row
    6 - "Profile Id" Is Shown When You Click The Profile In The Multilogin Application
    7 - You Need To Put The Password In The Configuration File As The Script Will Try To Login To The Account If It Is Not Already Logged In
    8 - "Address Number" Is A Number Starting From 1, But Note That If Amazon Didn't Ask For Selecting Address During Purchasing The Script Will Not Choose Any Address
    9 - You Can Add As Many Products As You Wish In One Row By Repeating The Last 5 Columns
   10 - "Product FBA" Can Either Be 0 For FBM Or 1 For FBA
   11 - The Script Saves Four Log Files SampleData.csv, SampleSucceeded.csv, SampleFailed.csv, And SampleFailed.tar
   12 - SampleData.csv Contains ["Row Number","Email","Order Fee","Order Price","Order Number","Customer Name"] Of Each Succeeded Row
   13 - SampleSucceeded.csv Contains ["Row Number","Stage"] Of Each Succeeded Row And The Script Will Escape Those Rows For Those Stages If You Rerun It
   14 - SampleFailed.csv Contains ["Row Number","Stage","Row Cells","Traceback"] Of Each Failed Row
   15 - SampleFailed.tar Contains A Screenshot For Each Failed Row Showing The Last Page Opened In The Browser Before Failure When Possible
        Screenshots Are Saved With File Names In This Format [Row Number]_[Stage]_[Email]_[Timestamp].png
