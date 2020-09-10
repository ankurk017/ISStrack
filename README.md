# ISStrack

## Description
User can plot the current, past, or future tracks of the International Space Station, overlapped with the swath of DLR Earth Sensing Imaging Spectrometer (DESIS).

## Required Libraries
sys, math, itertools, time, datetime, json, argparse, numpy, sympy, matplotlib, urllib, cartopy

## Arguments
This tool needs 4 optional arguments as follows,

1. startdate: Start date of ISS track which user wishes to plot.

2. enddate: End date of ISS track which user wishes to plot.

3. dateformat: Date format of the entered startdate and enddate. Both startdate and enddate should be in the same format.

4. temp_res: Temporal resolution (in minutes) in which user needs to retrieve the ISS location. Smaller values of temp_res leads to finer ISS track and swath (takes time to calculate swath locations), whereas larger temp_res values leads to coarser ISS track and swath (takes comparatively less time to calculate swath location).

If the user does not provide any of the optional arguments, then this tool will plot the ISS track of 1 hour prior to the current UTC time to the 1 hour later of the current UTC time with the time interval of 5 minutes.

## Examples

1. User needs to specify start_date, end_date, dateformat and interval temp_res as arguments

`$python  iss_tracker.py --startdate='18-09-2019-07:00:00' --enddate='18-09-2019-08:30:00' --dateformat='%d-%m-%Y-%H:%M:%S' --temp_res=5`

`$python  iss_tracker.py --startdate='18/09/2019-07' --enddate='18/09/2019-08' --dateformat='%d/%m/%Y-%H' --temp_res=5`

2. If a user is proving start_date and end_date is the default format (), then there is no need to specify the dateformat argument while running the script

`$python  iss_tracker.py --startdate='18-09-2019-07:00:00' --enddate='18-09-2019-08:30:00' --temp_res=1`

![Sample ISS track overlapped with DESIS swath for one day](https://github.com/ankurk017/ISStrack/blob/master/Sample_track/Figure1_git.png)

3. User can chose not to provide any arguments

`$python  iss_tracker.py`

![Sample ISS track overlapped with DESIS swath for one day](https://github.com/ankurk017/ISStrack/blob/master/Sample_track/Figure2_git.png)

## Methodology for the calculation of DESIS swath 

Steps to calculate the DESIS swath latitude-longitude

1. **Calculating swath distance**: It is the product of DESIS altitude (one of the paramters obtained from URL) and the _tan_ of DESIS swath angle. 

![Figure is on the 3-D (X-Y-Z) plane](https://github.com/ankurk017/ISStrack/blob/master/Sample_track/calculation_figure1.jpg)

2. **Calculating the distance between the current and the next neighboring ISS location**: In order to calculate the right and left side of ISS, one needs to have the location of ISS at time _t+1_ (Nadir<sub>t+1</sub>). Then one can easily calculate the distance between the current (Nadir<sub>t</sub>)  and the next neighbouring ISS location (Nadir<sub>t+1</sub>) using _distance formula_.


3. **Solving quadratic equation**: Based on (Nadir<sub>t</sub>), (Nadir<sub>t+1</sub>), _Swath Distance_ and _Neighboring Distance_, one can easily solve the two equations having two unknowns (X<sub>s</sub> and Y<sub>s</sub>). 

![Figure is on the horizontal plane](https://github.com/ankurk017/ISStrack/blob/master/Sample_track/calculation_figure2.jpg)
 
