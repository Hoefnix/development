#!/usr/bin/python
import requests
from requests.auth import HTTPBasicAuth
from http.server import BaseHTTPRequestHandler,HTTPServer
import json
import time
import socket
import os
import ephem
import datetime
import subprocess


def empty(myString):
	if myString == "nil":
		return True
	elif myString and myString.strip():	#	myString is not None AND myString is not empty or blank
		return False
	return True


def verwachting():
	teller = 0
	verwachting = ""
	
	resultaat = httpGet("http://api.openweathermap.org/data/2.5/forecast?q=capelle%20aan%20den%20ijssel,nl&units=metric&lang=nl&APPID=2799a7fec820a086d91e60e3b48fac5a")
	if (resultaat.status_code == requests.codes.ok):
		# bericht(resultaat.text)
		if not empty(resultaat.text):
			verwachting = json.loads( resultaat.text )

			regel = verwachting["list"][0]
			lokaletijd = time.localtime(regel["dt"])
			windomsc = wind(regel["wind"]["speed"])["klasse"].lower()
			windkrch = wind(regel["wind"]["speed"])["kracht"]
			verwachting = "%s - %s\xb0C met %s%s"%(time.strftime("%H:%M", lokaletijd), int(round(regel["main"]["temp"],0)), windomsc, windkrch)
	return verwachting
					
def weerbericht( vorigebericht ):
	
	resultaat = httpGet("http://api.openweathermap.org/data/2.5/weather?q=capelle%20aan%20den%20ijssel,nl&units=metric&lang=nl&APPID=2799a7fec820a086d91e60e3b48fac5a")
	if (resultaat.status_code == requests.codes.ok):
		# bericht(resultaat.text)
		if not empty(resultaat.text):
			weerbericht = json.loads( resultaat.text )
			bericht( showtime(weerbericht["dt"]) )
			if weerbericht["dt"] != vorigebericht:
				omschr = ""
				weernu = json.loads( resultaat.text )["weather"]
				for regel in weernu:
					omschr = omschr + "" if empty(omschr) else ", "
					omschr = omschr + regel["description"]
				
				weernu = json.loads( resultaat.text )["weather"][0]
				omschr = weernu["description"]
				tempnu = json.loads( resultaat.text )["main"]["temp"]
				tempmn = json.loads( resultaat.text )["main"]["temp_min"]
				tempmx = json.loads( resultaat.text )["main"]["temp_max"]
				luvoch = json.loads( resultaat.text )["main"]["humidity"]
				ludruk = json.loads( resultaat.text )["main"]["pressure"]
				wdsnlh = json.loads( resultaat.text )["wind"]["speed"]
				windri = windrichting(float(json.loads( resultaat.text )["wind"]["deg"]))
				datetm = showtime(json.loads( resultaat.text )["dt"])
			
				wdomsc = wind(wdsnlh)["klasse"].lower()
				wdkrch = wind(wdsnlh)["kracht"]

				bericht( "Het weer op %s \u000A %s, %s\xb0C met %s%s uit het %s\u000A %s"%(datetm, omschr,int(round(tempnu,0)),wdomsc,wdkrch,windri,verwachting()), True)

				return weerbericht["dt"]
	return vorigebericht
	
#	{"coord":{"lon":139,"lat":35},
#	 "sys":{"country":"JP","sunrise":1369769524,"sunset":1369821049},
#	 "weather":[{"id":804,"main":"clouds","description":"overcast clouds","icon":"04n"}],
#	 "main":{"temp":289.5,"humidity":89,"pressure":1013,"temp_min":287.04,"temp_max":292.04},
#	 "wind":{"speed":7.31,"deg":187.002},
#	 "rain":{"3h":0},
#	 "clouds":{"all":92},
#	 "dt":1369824698,
#	 "id":1851632,
#	 "name":"Shuzenji",
#	 "cod":200}

def wind( snelheid ):
	if		0	< snelheid	<	0.2:
		return {"kracht": "\u2070","klasse":"Windstil","omschrijving":"Rook stijgt recht omhoog"}
	elif 0.3 < snelheid	<	1.5:
		return {"kracht": "\u2071","klasse":"Zwakke wind","omschrijving":"Rookpluimen geven richting aan"}
	elif 1.6 < snelheid	<	3.3:
		return {"kracht": "\xb3","klasse":"Zwakke wind","omschrijving":"Bladeren ritselen, wind voelbaar in het gezicht"}
	elif 3.4 < snelheid	<	5.4:
		return {"kracht": "\xb3","klasse":"Matige wind","omschrijving":"Bladeren en twijgen voortdurend in beweging"}
	elif 5.5 < snelheid	<	7.9:
		return {"kracht": "\u2074","klasse":"Matige wind","omschrijving":"Stof en papier dwarrelen op"}
	elif 8.0 < snelheid	<	10.7:
		return {"kracht": "\u2075","klasse":"Vrij krachtige wind","omschrijving":"Takken maken zwaaiende bewegingen"}
	elif 10.8 < snelheid	<	13.8:
		return {"kracht": "\u2076","klasse":"Krachtige wind","omschrijving":"Grote takken bewegen en hoed wordt afgeblazen"}
	elif 13.9 < snelheid <	17.1:
		return {"kracht": "\u2077","klasse":"Harde wind","omschrijving":"Bomen bewegen"}
	elif 17.2 < snelheid <	20.7:
		return {"kracht": "\u2078","klasse":"Stormachtige wind","omschrijving":"Twijgen breken af"}
	elif 20.8 < snelheid <	24.4:
		return {"kracht": "\u2079","klasse":"Storm","omschrijving":"Takken breken af, Dakpannen waaien weg"}
	elif 24.5 < snelheid <	28.4:
		return {"kracht": "\u2071\u2070","klasse":"Zware storm","omschrijving":"Bomen worden ontworteld"}
	elif 28.5 < snelheid <	32.6:
		return {"kracht": "\u2071\u2071","klasse":"Zeer zware storm","omschrijving":"Uitgebreide schade aan bossen en gebouwen"}
	elif 32.6 < snelheid <	99.9:
		return {"kracht": 12,"klasse":"Orkaan","omschrijving":"Niets blijft meer overeind"}

def windrichting(hoek, afkorten=False ):
	if		337.5	< hoek < 360 :
		return "n" if afkorten else "noorden"
	elif		0	< hoek < 22.5:
		return "n" if afkorten else "noorden"
	elif	22.5	< hoek < 67.5:
		return "no" if afkorten else "noordoosten"
	elif	67.5	< hoek < 112.5:
		return "o" if afkorten else "oosten"
	elif	112.5	< hoek < 157.5:
		return "zo" if afkorten else "zuidoosten"
	elif	157.5	< hoek < 202.5:
		return "z" if afkorten else "zuiden"
	elif	202.5	< hoek < 247.5:
		return "zw" if afkorten else "zuidwesten"
	elif	247.5	< hoek < 292.5:
		return "w" if afkorten else "westen"
	elif	292.5	< hoek < 337.5:
		return "nw" if afkorten else "noordwesten"

def bericht(message=None, ookTelegram=False):
	if not message is None:
		print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),message))
		if ookTelegram:
			telegram(message)

def telegram(message="...", chat_id="12463680"):
	#	johannes_smits	=  "12463680"
	#	alarmsysteem	= "-24143102"
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage?chat_id=%s&text=%s" % (chat_id, message), timeout=5)
	return r.status_code
		
def showtime(tijd):
	lokaletijd = time.localtime(tijd)
	weekdagen = {0:"zondag",1:"maandag",2:"dinsdag",3:"woensdag",4:"donderdag",5:"vrijdag",6:"zaterdag"}
	dag = weekdagen[int(time.strftime("%w", lokaletijd))]
#	return time.strftime("%H:%M:%S", time.localtime(tijd))
	return "%s %s"%(dag, time.strftime("%H:%M", lokaletijd))
		
def httpGet( httpCall, wachten = 2):
	resultaat = requests.Response
	try:
		resultaat = requests.get(httpCall, timeout=wachten)
	except requests.Timeout as e:
		bericht("%s: url=%s, timeout=%s"%(e, httpCall, wachten))
		resultaat.status_code = 999
	except:
		bericht("Fout: url=%s, timeout=%s"%(httpCall,wachten))
		resultaat.status_code = 999
	return resultaat
			
try:
	vorigbericht = 0
	while True:
		vorigbericht = weerbericht( vorigbericht )
		time.sleep(3600)	# even rust
	
except KeyboardInterrupt:
	bericht("(httplistner) ctrl-c ontvangen, weerbericht wordt opnieuw gestart", True)