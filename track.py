import sys
import math
import itertools
import time
import datetime
import json
import argparse
import numpy as np
from sympy import symbols, Eq, solve
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import urllib.request as urllib2
import cartopy.crs as ccrs

def generate_timestamps(start,end,minutes=10):
	start_epoch=int(start.timestamp())
	end_epoch=int(end.timestamp())
	time_span_in_seconds=end_epoch-start_epoch
	timestamps=np.arange(start_epoch,end_epoch,minutes*60)
	return timestamps

def split_timestamps(array):
	split_time_id=np.arange(1,len(array),10)
	split_time_id=np.append(split_time_id,len(array))-1
	split_time=[array[split_time_id[i]:split_time_id[i+1]] for i in range(len(split_time_id)-1)]
	return split_time
	
def generate_urls(split_time):
	out1=[str(split_time[i].tolist())[1:-1].replace(' ','') for  i in range(len(split_time))]
	out2=['https://api.wheretheiss.at/v1/satellites/25544/positions?timestamps=%s&units=miles'%i for i in out1]
	return out1,out2

def read_url_json(url):
	req1 = urllib2.Request(url)
	response1 = urllib2.urlopen(req1)
	obj1 = json.loads(response1.read())
	return obj1

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
	percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
	filledLength = int(length * iteration // total)
	bar = fill * filledLength + '-' * (length - filledLength)
	print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
	if iteration == total: 
		print()


def get_iss_location_details(url_json):
	loc2=[]
	for i in range(len(track_urls)):
		time.sleep(1.1)
		loc1=read_url_json(track_urls[i])
		loc2.append(loc1)
		printProgressBar(i + 1, len(track_urls), prefix = 'Retrieving location:', suffix = 'Complete ', length = 70)
	loc=list(itertools.chain(*loc2))
	return loc

def calc(fp,sp,theta,iss_altitude):
	altitude=iss_altitude*1.60934/111.11 # km
	swath_distance=(theta/360)*2*np.pi*altitude
	distance=math.sqrt((fp[0]-sp[0])**2 + (fp[1]-sp[1])**2)
	angular_distance=math.sqrt(distance**2 + swath_distance**2)
	x,y = symbols ('x y')
	eq1 = Eq((x-fp[0])**2 + (y-fp[1])**2 - swath_distance**2)
	eq2 = Eq((x-sp[0])**2 + (y-sp[1])**2 - angular_distance**2)
	sol = solve((eq1, eq2),(x, y))
	return(sol)

def plot_iss_current_location(lon,lat,plt):
	req = urllib2.Request("http://api.open-notify.org/iss-now.json")
	response = urllib2.urlopen(req)
	obj = json.loads(response.read())
	currect_location_lon, currect_location_lat = float(obj['iss_position']['longitude']),float(obj['iss_position']['latitude'])
	plt.plot(currect_location_lon,currect_location_lat, color='red', linewidth=2,marker='o', transform=ccrs.PlateCarree())
	plt.text(currect_location_lon + 3, currect_location_lat - 12, 'ISS current location', horizontalalignment='left', transform=ccrs.PlateCarree())
	return plt

def validate(date,format):
	try:
		datetime.datetime.strptime(date,format)
	except ValueError:
		raise ValueError("Incorrect data format")

def parse_arguments():
	format="%d-%m-%Y-%H:%M:%S"
	start = datetime.datetime.strptime("18-09-2019-07:00:00", format)
	end = datetime.datetime.strptime("18-09-2019-09:00:00", format)
	minutes=5

	parser = argparse.ArgumentParser(description="Need to pass arguments as start and end date, fate format, and the interval in minutes.")
	parser.add_argument("--startdate", type=str, default=start, help="Need to pass start date")
	parser.add_argument("--enddate", type=str, default=end, help="Need to pass end date")
	parser.add_argument("--dateformat", type=str, default=format, help="Need to pass date format")
	parser.add_argument("--minutes", type=int, default=minutes, help="Need to pass interval minutes")
	args = parser.parse_args()
	validate(args.startdate,args.dateformat)
	args.startdate=datetime.datetime.strptime(args.startdate,args.dateformat)
	args.enddate=datetime.datetime.strptime(args.enddate,args.dateformat)
	return args.startdate, args.enddate, args.dateformat, args.minutes

def calculate_desis_swath(lon,lat,altitude):
	right=[]
	left=[]
	right_swath_angle=5
	left_swath_angle=45
	for i in range(lon.shape[0]-1):
		fp=np.array([lon[i],lat[i]])
		sp=np.array([lon[i+1],lat[i+1]])
		right_latlon=calc(fp,sp,right_swath_angle,altitude[i])
		left_latlon=calc(fp,sp,left_swath_angle,altitude[i])
		if fp[1]>=sp[1]:
			right.append(right_latlon[0])
			left.append(left_latlon[1])
		else:
			right.append(right_latlon[1])
			left.append(left_latlon[0])
		printProgressBar(i + 1, lon.shape[0]-1, prefix = 'Calculating DESIS swath coordinates:', suffix = 'Complete ', length = 70)

	right_swath=np.concatenate([np.flip(np.vstack(left)[:,0]),np.vstack(right)[:,0]])
	left_swath=np.concatenate([np.flip(np.vstack(left)[:,1]),np.vstack(right)[:,1]])
	return right_swath, left_swath

def iss_track_plot(lon,lat,a,b):
	fig = plt.figure(figsize=(12,6))
	ax = plt.axes(projection=ccrs.PlateCarree())
	ax.stock_img()
	plt.plot(lon,lat,'k',transform=ccrs.Geodetic())
	qw=plt.fill(a,b,facecolor='b',alpha=0.45,transform=ccrs.Geodetic())
	plt.grid(True)
	gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,linewidth=2, color='gray', alpha=0.5, linestyle='--')
	gl.xlabels_top = True
	gl.ylabels_left = True
	gl.xlines = True
	gl.xformatter = LONGITUDE_FORMATTER
	gl.yformatter = LATITUDE_FORMATTER
	plot_iss_current_location(lon,lat,plt)
	return plt


if __name__ == "__main__":
	start, end, format, minutes = parse_arguments()
	
	gen_times=generate_timestamps(start,end,minutes=minutes)
	out=split_timestamps(gen_times)
	urls1,track_urls=generate_urls(out)
	loc=get_iss_location_details(track_urls)

	lon=np.array([i['longitude'] for i in loc])
	lat=np.array([i['latitude'] for i in loc])
	altitude=np.array([i['altitude'] for i in loc])

	right_swath,left_swath=calculate_desis_swath(lon,lat,altitude)	
	plt=iss_track_plot(lon,lat,right_swath,left_swath)
	plt.show()

