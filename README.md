# ISStrack

## Description
User can plot the current, past, or future tracks of the International Space Station, overlapped with the swath of DLR Earth Sensing Imaging Spectrometer (DESIS).

## Required Libraries
sys, math, itertools, time, datetime, json, argparse, numpy, sympy, matplotlib, urllib, cartopy

## Arguments
This tool needs 4 optional arguments as follows,

1. startdate: Start date of ISS track which user wishes to plot

2. enddate: End date of ISS track which user wishes to plot

3. dateformat: Date format of the entered startdate and enddate. Both startdate and enddate should be in the same format.

4. minutes: Minutes in which user needs to retrieve the ISS location.

If the user does not provide any of the optional arguments, then this tool will plot the ISS track of 1 hour prior to the current UTC time to the 1 hour later of the current UTC time with the time interval of 5 minutes.

## Example

1. User needs to specify start_date, end_date, dateformat and interval minutes as arguments

`$python  iss_tracker.py --startdate='18-09-2019-07:00:00' --enddate='18-09-2019-08:30:00' --dateformat='%d-%m-%Y-%H:%M:%S' --minutes=1`




![Sample ISS track for one day](https://github.com/ankurk017/ISStrack/blob/master/Sample_track/ISS_track.png)


![Sample ISS track overlapped with DESIS swath for one day](https://github.com/ankurk017/ISStrack/blob/master/Sample_track/Sample_plot2.jpeg)

