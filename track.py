import argparse
import cartopy.crs as ccrs
import datetime
import itertools
import json
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import sys
import time
import urllib.request as urllib2

from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from sympy import symbols, Eq, solve


def generate_timestamps(start, end, temp_res=10):
    """
    Function to generate epoch timestamps in the specific interval based on input start date, end date and interval temp_res
        Parameters:
            start (str): Start date of the ISS track
            end (str): End date of the ISS track
            temp_res (int): This is an optional argument. If not provided, default value will be considered. Temporal resolution (in minutes) in which user needs to retrieve the ISS location. Smaller values of temp_res leads to finer ISS
            track and swath (takes time to calculate swath locations), whereas larger temp_res values leads to coarser ISS track and swath (takes comparatively less time to calculate swath location).

        Returns:
            timestamps: Timestamps in epoch
    """

    start_epoch = int(start.timestamp())
    end_epoch = int(end.timestamp())

    time_span_in_seconds = end_epoch - start_epoch
    timestamps = np.arange(start_epoch, end_epoch, temp_res*60)

    return timestamps


def split_timestamps(array):
    """
    Function to split epoch timestamps (generated from generate_timestamps function) in the sets of 10. This is because API takes maximum 10 timestamps to retrieve location at one go.
        Parameters:
            array: Array contains the list of timestamps
        Returns:
            split_time: Array contains the timestamps in the sets of 10
    """

    split_time_id = np.arange(1, len(array), 10)
    split_time_id = np.append(split_time_id, len(array))-1

    split_time = [array[split_time_id[time_sequence]:split_time_id[time_sequence+1]]
                  for time_sequence in range(len(split_time_id)-1)]

    return split_time


def generate_urls(split_time):
    """
    Function to generate URLs based on array which is in the sets of 10
        Parameters:
            split_time: Array contains the timestamps in the sets of 10
        Returns:
            track_url: List of all URLs which is going to be used to retrieve locations
    """

    timestamps = [str(split_time[split_time_index].tolist())[1:-1].replace(' ', '')
                  for split_time_index in range(len(split_time))]

    track_url = [
        f'https://api.wheretheiss.at/v1/satellites/25544/positions?timestamps={timestamp}&units=miles' for timestamp in timestamps
    ]

    return track_url


def read_url_json(url):
    """
    Function to retrieve location details from given URL
        Parameters:
            url: URL having the details of ISS
        Returns:
            details: Details of ISS at all timestamps in dictonary form
    """

    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    json_response = json.loads(response.read())

    return json_response


def printProgressBar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Function to display a progress bar
            printProgressBar(
                i + 1, lon.shape[0]-1, prefix = 'Calculating DESIS swath coordinates:', suffix = 'Complete ', length = 70)
        Parameters:
            iteration: Current iteration value
            total: Total iteration value
            prefix: Prefix text
            suffix: Suffix Text
            decimals: Number of decimals to be printed while displaying the progress percentage
            length: Percentage of screen covering the progress bar
            fill: Fill character value in the progress bar
            printEnd: Ending character. Eg. "\r"
        Returns:
            None
    """

    # calculate percentage in 2 decimal places
    percent = 100 * (iteration / float(total))
    percent = f'{percent:.{2}f}'

    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)

    if iteration == total:
        print()


def get_iss_location_details(url_json):
    """
    Function to retrieve location details from list of URLs
        Parameters:
            url: List of URLs having the details of ISS
        Returns:
            details: Details of ISS at all timestamps from all URLS in dictonary form and showing progress bar
    """

    locations = []
    for url_sequence in range(len(track_urls)):
        #Currently requests are limited to roughly 1 per second	
        time.sleep(1.1)
        loc1 = read_url_json(track_urls[url_sequence])
        locations.append(loc1)
        printProgressBar(
            url_sequence + 1,
            len(track_urls),
            prefix='Retrieving location:',
            suffix='Complete ',
            length=70
        )

    output = list(itertools.chain(*locations))

    return output


def calculate_desis_lonlat(nadir_at_time_t, nadir_at_time_t_plus_1, theta, iss_altitude):
    """
    Calculation of DESIS swath latitude longitude
        Parameters:
            nadir_at_time_t: Latitude-Longitude of the first location
            nadir_at_time_t_plus_1: Latitude-Longitude of the second location
            theta: Angle (in degree) of the scanning instrument
            iss_altitude: ISS altitude (in miles) over the first location
        Returns:
            sol: Latitude-Longitude of right and left side of the instrument
    """

    altitude = iss_altitude*1.60934/111.11  # km
    swath_distance = altitude*np.tan(theta*np.pi/180)
    distance = math.sqrt((nadir_at_time_t[0]-nadir_at_time_t_plus_1[0])**2 + (nadir_at_time_t[1]-nadir_at_time_t_plus_1[1])**2)
    angular_distance = math.sqrt(distance**2 + swath_distance**2)

    x, y = symbols('x y')
    equation1 = Eq((x-nadir_at_time_t[0])**2 + (y-nadir_at_time_t[1])**2 - swath_distance**2)
    equation2 = Eq((x-nadir_at_time_t_plus_1[0])**2 + (y-nadir_at_time_t_plus_1[1])**2 - angular_distance**2)
    solution = solve((equation1, equation2), (x, y))

    return solution


def plot_iss_current_location(plt):
    """
    Plotting of the current location of ISS
        Parameters:
            plt: Matplotlib figure handle
        Returns:
            None
    """

    request = urllib2.Request("http://api.open-notify.org/iss-now.json")

    response = urllib2.urlopen(request)
    json_response = json.loads(response.read())

    currect_location_lon = float(json_response['iss_position']['longitude'])
    currect_location_lat = float(json_response['iss_position']['latitude'])

    plt.plot(
        currect_location_lon,
        currect_location_lat,
        color='red',
        linewidth=2,
        marker='o',
        transform=ccrs.PlateCarree()
    )
    plt.text(
        currect_location_lon + 3,
        currect_location_lat - 12,
        'ISS current location',
        horizontalalignment='left',
        transform=ccrs.PlateCarree()
    )

    return plt


def validate(date, format):
    """
    Validation of given date and date format
        Parameters:
            date: Date stampt
            format: Date format
        Returns:
            None
    """

    try:
        datetime.datetime.strptime(date, format)
    except ValueError:
        raise ValueError("Incorrect data format")


def parse_arguments():
    """
    python iss_tracker.py --startdate='18-09-2019-07:00:00' --enddate='18-09-2019-08:30:00' --dateformat='%d-%m-%Y-%H:%M:%S' --temp_res=1
    python iss_tracker.py --startdate='18-09-2019-07' --enddate='18-09-2019-08' --dateformat='%d-%m-%Y-%H' --temp_res=1
    python iss_tracker.py --startdate='18-09-2019-07:00:00' --enddate='18-09-2019-08:30:00' --temp_res=1
        Parameters:
             None
        Returns:
             tuple of arguments: args.startdate, args.enddate, args.dateformat, args.temp_res
    """

    date_format = "%d-%m-%Y-%H:%M:%S"

    current_time = datetime.datetime.utcnow()
    timedelta = datetime.timedelta(hours=1)
    start = (current_time-timedelta).strftime(date_format)
    end = (current_time+timedelta).strftime(date_format)
    temp_res = 5

    parser = argparse.ArgumentParser(
        description="Need to pass arguments as start and end date, fate format, and the interval in temp_res."
    )
    parser.add_argument("--startdate", type=str,
                        default=start, help="Need to pass start date")
    parser.add_argument("--enddate", type=str, default=end,
                        help="Need to pass end date")
    parser.add_argument("--dateformat", type=str,
                        default=date_format, help="Need to pass date format")
    parser.add_argument("--temp_res", type=int, default=temp_res,
                        help="Need to pass interval temp_res")
    args = parser.parse_args()

    validate(args.startdate, args.dateformat)
    args.startdate = datetime.datetime.strptime(
        args.startdate,
        args.dateformat
    )
    args.enddate = datetime.datetime.strptime(args.enddate, args.dateformat)

    return args.startdate, args.enddate, args.dateformat, args.temp_res


def calculate_desis_swath(lon, lat, altitude):
    """
    Function to retrieve location details from list of URLs
        Parameters:
           lon: Longitude of the first and second ISS location
           lat: Latitude of the first and second ISS location
           altitude: Altitude of the first ISS location
        Returns:
           right_swath: Latitude-Longitude of the DESIS right swath
           left_swath: Latitude-Longitude of the DESIS left swath
    """

    right = []
    left = []
    right_swath_angle = 5
    left_swath_angle = 45

    for location_index in range(lon.shape[0]-1):
        nadir_at_time_t = np.array([lon[location_index], lat[location_index]])
        nadir_at_time_t_plus_1 = np.array([lon[location_index+1], lat[location_index+1]])
        right_latlon = calculate_desis_lonlat(nadir_at_time_t, nadir_at_time_t_plus_1, right_swath_angle, altitude[location_index])
        left_latlon = calculate_desis_lonlat(nadir_at_time_t, nadir_at_time_t_plus_1, left_swath_angle, altitude[location_index])
        if nadir_at_time_t[1] >= nadir_at_time_t_plus_1[1]:
        # Ascending ISS pass: Latitude at time_t is less than latitude at time_t_plus_1
            if nadir_at_time_t_plus_1[0]-nadir_at_time_t[0] <= 0:
                right.append(right_latlon[1])
                left.append(left_latlon[0])
            else:
                right.append(right_latlon[0])
                left.append(left_latlon[1])
        else:
        # Descending ISS pass: Latitude at time_t is greater than latitude at time_t_plus_1
            if nadir_at_time_t_plus_1[0]-nadir_at_time_t[0] <= 0:
                right.append(right_latlon[0])
                left.append(left_latlon[1])
            else:
                right.append(right_latlon[1])
                left.append(left_latlon[0])
        printProgressBar(
            location_index + 1,
            lon.shape[0]-1,
            prefix='Calculating DESIS swath coordinates:',
            suffix='Complete ',
            length=70
        )

    right_swath = np.concatenate(
        [np.flip(np.vstack(left)[:, 0]),
         np.vstack(right)[:, 0]]
    )
    left_swath = np.concatenate(
        [np.flip(np.vstack(left)[:, 1]),
         np.vstack(right)[:, 1]]
    )

    return right_swath, left_swath


def iss_track_plot(lon, lat, right, left):
    """
    Plotting the ISS track and DESIS swath
        Parameters:
            lon: ISS longitude
            lat: ISS latitude
            right: Latitude-Longitude of the DESIS right swath
            left: Latitude-Longitude of the DESIS left swath
        Returns:
            plt: Matplotlib figure handle
    """
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.stock_img()
    plt.plot(lon, lat, 'k', transform=ccrs.Geodetic())
    qw = plt.fill(right, left, facecolor='b',
                  alpha=0.45, transform=ccrs.Geodetic())
    plt.grid(True)

    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=2, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = True
    gl.ylabels_left = True
    gl.xlines = True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    plot_iss_current_location(plt)

    return plt


if __name__ == "__main__":
    start, end, date_format, temp_res = parse_arguments()

    gen_times = generate_timestamps(start, end, temp_res=temp_res)
    out = split_timestamps(gen_times)
    track_urls = generate_urls(out)
    loc = get_iss_location_details(track_urls)

    lon = np.array([location_details['longitude'] for location_details in loc])
    lat = np.array([location_details['latitude'] for location_details in loc])
    altitude = np.array([location_details['altitude'] for location_details in loc])

    right_swath, left_swath = calculate_desis_swath(lon, lat, altitude)
    plt = iss_track_plot(lon,lat,right_swath,left_swath)
    plt.show()
