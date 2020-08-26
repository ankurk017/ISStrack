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


def generate_timestamps(start, end, minutes=10):
    """
    Function to generate epoch timestamps in the specific interval based on input start date, end date and interval minutes
        Parameters:
            start (str): Start date of the ISS track
            end (str): End date of the ISS track
            minutes (int): This is an optional argument. If not provided, default value will be considered. This is the interval time (in minutes) which user needs to retrieve location.
        Returns:
            timestamps: Timestamps in epoch  
    """

    start_epoch = int(start.timestamp())
    end_epoch = int(end.timestamp())

    time_span_in_seconds = end_epoch-start_epoch
    timestamps = np.arange(start_epoch, end_epoch, minutes*60)

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

    split_time = [array[split_time_id[i]:split_time_id[i+1]]
                  for i in range(len(split_time_id)-1)]

    return split_time


def generate_urls(split_time):
    """
    Function to generate URLs based on array which is in the sets of 10
        Parameters:
            split_time: Array contains the timestamps in the sets of 10
        Returns:
            track_url: List of all URLs which is going to be used to retrieve locations
    """

    timestamps = [str(split_time[i].tolist())[1:-1].replace(' ', '')
                  for i in range(len(split_time))]

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
            printProgressBar(i + 1, lon.shape[0]-1, prefix = 'Calculating DESIS swath coordinates:', suffix = 'Complete ', length = 70)
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

    percent = ("{0:." + str(decimals) + "f}").format(
        100 * (iteration / float(total))
    )

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
    for i in range(len(track_urls)):
        time.sleep(1.1)
        loc1 = read_url_json(track_urls[i])
        locations.append(loc1)
        printProgressBar(
            i + 1,
            len(track_urls),
            prefix='Retrieving location:',
            suffix='Complete ',
            length=70
        )

    output = list(itertools.chain(*locations))

    return output


def calc(fp, sp, theta, iss_altitude):
    """
    Calculation of DESIS swath latitude longitude
        Parameters:
            fp: Latitude-Longitude of the first location
            sp: Latitude-Longitude of the second location
            theta: Angle (in degree) of the scanning instrument
            iss_altitude: ISS altitude (in miles) over the first location
        Returns:
            sol: Latitude-Longitude of right and left side of the instrument
    """

    altitude = iss_altitude*1.60934/111.11  # km
    swath_distance = altitude*np.tan(theta*np.pi/180)
    distance = math.sqrt((fp[0]-sp[0])**2 + (fp[1]-sp[1])**2)
    angular_distance = math.sqrt(distance**2 + swath_distance**2)

    x, y = symbols('x y')
    equation1 = Eq((x-fp[0])**2 + (y-fp[1])**2 - swath_distance**2)
    equation2 = Eq((x-sp[0])**2 + (y-sp[1])**2 - angular_distance**2)
    solution = solve((eq1, eq2), (x, y))

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
    date_format = "%d-%m-%Y-%H:%M:%S"

    # start = datetime.datetime.strptime("18-09-2019-07:00:00", format)
    # end = datetime.datetime.strptime("18-09-2019-09:00:00", format)

    current_time = datetime.datetime.utcnow()
    timedelta = datetime.timedelta(hours=6)
    start = (current_time-timedelta).strftime(date_format)
    end = (current_time+timedelta).strftime(date_format)
    minutes = 5

    parser = argparse.ArgumentParser(
        description="Need to pass arguments as start and end date, fate format, and the interval in minutes."
    )
    parser.add_argument("--startdate", type=str,
                        default=start, help="Need to pass start date")
    parser.add_argument("--enddate", type=str, default=end,
                        help="Need to pass end date")
    parser.add_argument("--dateformat", type=str,
                        default=date_format, help="Need to pass date format")
    parser.add_argument("--minutes", type=int, default=minutes,
                        help="Need to pass interval minutes")
    args = parser.parse_args()

    validate(args.startdate, args.dateformat)
    args.startdate = datetime.datetime.strptime(
        args.startdate,
        args.dateformat
    )
    args.enddate = datetime.datetime.strptime(args.enddate, args.dateformat)

    return args.startdate, args.enddate, args.dateformat, args.minutes


def calculate_desis_swath(lon, lat, altitude):
    right = []
    left = []
    right_swath_angle = 5
    left_swath_angle = 45

    for i in range(lon.shape[0]-1):
        fp = np.array([lon[i], lat[i]])
        sp = np.array([lon[i+1], lat[i+1]])
        right_latlon = calc(fp, sp, right_swath_angle, altitude[i])
        left_latlon = calc(fp, sp, left_swath_angle, altitude[i])
        if fp[1] >= sp[1]:
            if sp[0]-fp[0] <= 0:
                right.append(right_latlon[1])
                left.append(left_latlon[0])
            else:
                right.append(right_latlon[0])
                left.append(left_latlon[1])
        else:
            if sp[0]-fp[0] <= 0:
                right.append(right_latlon[0])
                left.append(left_latlon[1])
            else:
                right.append(right_latlon[1])
                left.append(left_latlon[0])
        printProgressBar(
            i + 1,
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
    start, end, date_format, minutes = parse_arguments()

    gen_times = generate_timestamps(start, end, minutes=minutes)
    out = split_timestamps(gen_times)
    track_urls = generate_urls(out)
    loc = get_iss_location_details(track_urls)

    lon = np.array([i['longitude'] for i in loc])
    lat = np.array([i['latitude'] for i in loc])
    altitude = np.array([i['altitude'] for i in loc])

    right_swath, left_swath = calculate_desis_swath(lon, lat, altitude)
    plt = iss_track_
