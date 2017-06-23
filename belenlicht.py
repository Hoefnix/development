#!/usr/bin/python.

import RPi.GPIO as GPIO 
import time
import subprocess
import os
import ephem 
from random import randint
import datetime
import stat  
from PIL import Image, ImageStat
import socket
import json
import requests

namehost = socket.gethostname()

def wachten(sleep, aanofuit):
	weekdagen = ["zondag","maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag"]

	nieuwetijd = time.time()+sleep
	dag = weekdagen[int(time.strftime("%w", time.localtime(nieuwetijd)))]
	
	bericht = "\U0001F4A1 licht %s op %s om %s"%(aanofuit, dag, time.strftime("%H:%M:%S", time.localtime(nieuwetijd)))
	TelegramMsg( Johannes_Smits, bericht)
	time.sleep(sleep)
	return 
	
GPIO.setmode(GPIO.BCM)  
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

tgAPIcode  = "112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU"
Johannes_Smits = "12463680"

def erWordtGebeld(channel):
	print('Deurbel werd ingedrukt op ' + time.strftime("%a om %H:%M:%S")+"\n")
	returncode = subprocess.Popen("/usr/bin/fswebcam -c /opt/develop/deurcam.cfg", shell=True)
#	TelegramMsg(-150338, "Er staat iemand voor de deur")
	time.sleep(5)

def how_many_seconds_until_midnight():
	today = datetime.date.today()
	seconds_since_midnight = time.time() - time.mktime(today.timetuple())
	return 86400 - seconds_since_midnight 

def TelegramMsg( chat_id="12463680", bericht="BelenLicht" ):
	payload = {"chat_id":chat_id, "text":bericht, "parse_mode":"HTML"}
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage", params=payload)	
	return (r.json()["ok"])
	
def brightness( im_file ):
     im = Image.open(im_file).convert('L')
     stat = ImageStat.Stat(im)
     return int(stat.mean[0])
	
def file_age_in_seconds(pathname):
	return time.time() - os.stat(pathname)[stat.ST_MTIME]

def lichtsterkte():
	lichtsterkte = 999
	try:
		resultaat = requests.get("http://192.168.178.202/?metingen")
	except requests.exceptions.RequestException as e:
		return lichtsterkte
                
	if (resultaat.status_code == requests.codes.ok):
		lichtsterkte = int( resultaat.json()["lichtsterkte"] )
	return lichtsterkte

GPIO.add_event_detect(24, GPIO.FALLING, callback=erWordtGebeld, bouncetime=500)

bericht = "\U0001F4A1 - gestart op de <b>%s</b> "%socket.gethostname() + time.strftime("om %H:%M:%S") 
TelegramMsg(Johannes_Smits, bericht )

print("Druk op Ctrl-C om te stoppen")

try:
	while True:
		o = ephem.Observer()

		# Thuis coordinaten
		o.lat  = '51.916905'
		o.long =  '4.563472'

		#define sun as object of interest
		s = ephem.Sun()

		sunset = o.next_setting(s)

		dtnow = time.mktime(time.strptime(format(ephem.now()), "%Y/%m/%d %H:%M:%S"))
		dtset = time.mktime(time.strptime(format(sunset)     , "%Y/%m/%d %H:%M:%S"))

		# wachten tot zonsondergang minus een uur 
		sleep = (dtset-dtnow)-3600
		if sleep < 0: 
			sleep = 0
		
		wachten(sleep, aanofuit = "aan")
		# en dan kijken tot het donker genoeg is of het uur voorbij	
		uurtje = 3600
		while ((lichtsterkte() > 100) & (uurtje >= 0)):
			time.sleep(30)
			uurtje -= 30
		requests.get("http://192.168.178.100:1208?woonkamer:aan")
		
		# wachten met uitzetten tot 00:00 plus tussen de 15 en 45 minuten 
		sleep = randint(900,2700) + how_many_seconds_until_midnight()
		wachten(sleep, aanofuit = "uit")
		requests.get("http://192.168.178.100:1208?woonkamer:uit")

except KeyboardInterrupt:
 	print ("Even opruimen...")
 	GPIO.remove_event_detect(24)
 	GPIO.cleanup()
 	print ("Klaar")
