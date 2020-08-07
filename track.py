import itertools
import time
import numpy as np
import datetime
import urllib.request as urllib2
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import json


def generate_timestamps(start,end,minutes=10):
	start_epoch=int(start.timestamp())
	end_epoch=int(end.timestamp())
	time_span_in_seconds=end_epoch-start_epoch
	
	A=np.arange(start_epoch,end_epoch,minutes*60)
	return A

def split_timestamps(array):
	id=np.arange(1,len(array),10)
	id=np.append(id,len(array))-1
	split_time=[array[id[i]:id[i+1]] for i in range(len(id)-1)]
	return split_time
	
def generate_urls(split_time):
	out1=[str(split_time[i].tolist())[1:-1].replace(' ','') for  i in range(len(split_time))]
	out2=['https://api.wheretheiss.at/v1/satellites/25544/positions?timestamps=%s&units=miles'%i for i in out1]
	return out1,out2

def get_iss_location(url):
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

def plot_iss_track(lon,lat):
	fig = plt.figure(figsize=(12,6))
	ax = plt.axes(projection=ccrs.PlateCarree())
	ax.stock_img()
	req = urllib2.Request("http://api.open-notify.org/iss-now.json")
	response = urllib2.urlopen(req)
	obj = json.loads(response.read())
	currect_location_lon, currect_location_lat = float(obj['iss_position']['longitude']),float(obj['iss_position']['latitude'])
	plt.plot(currect_location_lon,currect_location_lat, color='red', linewidth=2,marker='o', transform=ccrs.PlateCarree())
	plt.plot(lon,lat, color='blue', linewidth=2 ,transform=ccrs.Geodetic())
	plt.text(currect_location_lon + 3, currect_location_lat - 12, 'ISS current location', horizontalalignment='left', transform=ccrs.PlateCarree())
	plt.show()


if __name__ == "__main__":
	start = datetime.datetime.strptime("21-07-2020", "%d-%m-%Y")
	end = datetime.datetime.strptime("22-07-2020", "%d-%m-%Y")
	a=generate_timestamps(start,end)
	out=split_timestamps(a)
	urls1,track_urls=generate_urls(out)
	loc2=[]
	for i in range(len(track_urls)-1):
		time.sleep(1.1)
		loc1=get_iss_location(track_urls[i])
		loc2.append(loc1)
		printProgressBar(i + 1, len(track_urls)-1, prefix = 'Retrieving location:', suffix = 'Complete', length = 70)
	loc=list(itertools.chain(*loc2))
	[datetime.datetime.utcfromtimestamp(i) for i in [i['timestamp'] for i in loc]]
	lon=[i['longitude'] for i in loc]
	lat=[i['latitude'] for i in loc]
	plot_iss_track(lon,lat)
