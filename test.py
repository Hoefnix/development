#!/usr/bin/python
import requests
from requests.auth import HTTPBasicAuth
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import time
import socket
import os
import ephem 

def httpGet( httpCall, wachten = 2):
	resultaat = requests.Response
	# bericht("url=%s, timeout=%s"%(httpCall[-40:],wachten))
	try:
		resultaat = requests.get(httpCall, timeout=wachten)
	except requests.Timeout as e:
		bericht("%s: url=%s, timeout=%s"%(e, httpCall, wachten))
		resultaat.status_code = 999
	except:
		bericht("Fout: url=%s, timeout=%s"%(httpCall,wachten))
		resultaat.status_code = 999
	return resultaat
	
class zonnetijden(object):
	def __init__(self):
		# where am i 
		self.o		= ephem.Observer()
		self.o.lat  = '51.916905'
		self.o.long =  '4.563472'
		self.sun	= ephem.Sun() # define sun as object of interest

	def onder(self):
		return time.mktime(time.strptime(format(self.o.next_setting(self.sun)), "%Y/%m/%d %H:%M:%S"))
			
	def nacht(self):
		sunrise = self.o.next_rising(self.sun)
		sunset  = self.o.next_setting(self.sun)

		sr_next = ephem.localtime(sunrise)
		ss_next = ephem.localtime(sunset)		
	
		return 1 if (sr_next < ss_next) else 0

class woonkamerinit(object):
	def __init__(self):
		self.temperatuur = 0
		self.staandelamp = 0
		self.ledstrip = 0
		self.aanuit = 0
		self.lichtaan = zon.onder()
		self.lichtuit = time.time()
			
	def schakel(self, aanofuit):
		if aanofuit == "flp":
			aanofuit = "uit" if self.aanuit == 1 else "aan" 
		httpGet("http://192.168.178.201?%s"%aanofuit, 1)
		httpGet("http://192.168.178.204/aanuit=%s"%aanofuit, 1)
		resultaat = httpGet("http://192.168.178.208?gpio2=%s"%aanofuit, 1)
		if (resultaat.status_code == requests.codes.ok):
			self.aanuit = int(resultaat.text)
		return self.aanuit
		
	def automatisch(self):
		bericht("licht gaat aan om: %s"%time.strftime("%H:%M:%S", time.localtime(self.lichtaan)))
		if time.time() > self.lichtaan:
			# alleen als we niet thuis zijn; als het alarmsysteem aan staat
			bericht("Licht wordt ingeschakeld")
			#	Licht gaat automatisch uit ergens tussen 00:00 en 01:00
			
			today = datetime.date.today() # wanneer is het 
			seconds_since_midnight = time.time() - time.mktime(today.timetuple()) # hoeveel seconden zijn er al verstreken vandaag
			seconden_tot_middernacht = 86400 - seconds_since_midnight # hoeveel zijn er nog over... 24x60x60 seconden in een dag minus 
			
			self.lichtuit = time.time() + seconden_tot_middernacht + randint(900,2700)

			bericht("licht gaat uit om: %s"%time.strftime("%H:%M:%S", time.localtime(self.lichtuit)))
		
		if time.time() > self.lichtuit:
			bericht("Licht wordt uitgeschakeld")

	def check(self):
		if self.lichtaan != zon.onder():
			self.lichtaan = zon.onder()
			bericht("licht gaat aan om: %s"%time.strftime("%H:%M:%S", time.localtime(self.lichtaan)))

		#	Temperatuur
		resultaat = httpGet("http://192.168.178.201/?temperatuur")
		if (resultaat.status_code == requests.codes.ok):
			self.temperatuur	= resultaat.text

		#	Staande lamp
	#	resultaat = requests.get("http://192.168.178.201/?status", timeout=2)
	#	if (resultaat.status_code == requests.codes.ok):
	#		self.staandelamp	= int(resultaat.text[-1])

		#	Led strip
	#	resultaat = requests.get("http://192.168.178.204", timeout=2)
	#	if (resultaat.status_code == requests.codes.ok):
	#		self.ledstrip	= int(json.loads( resultaat.text )["aanuit"])

		#	Schemerlamp
		resultaat = httpGet("http://192.168.178.208/gpio2")
		if (resultaat.status_code == requests.codes.ok):
			self.aanuit = int(resultaat.text)
		return self.aanuit
		
def bericht(message=None):
	if not message is None:
		print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),message))

try:
	while True:
		zon = zonnetijden()
		woonkamer = woonkamerinit()
		woonkamer.check()
		woonkamer.automatisch()
		time.sleep(120)
	
except KeyboardInterrupt:
	bericht("Tot ziens...\n")
