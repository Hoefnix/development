#!/usr/bin/env python3

import subprocess
import signal
import requests
import os
import time

watchedpids = {"httplistner":0,"otherprocess":0}

def bericht(message=None, Telegram=False, viaPushover=False):
	if not message is None:
		print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),message))
		if Telegram:
			telegram(message=message)
		if viaPushover:
			pushover( bericht = message )
	
def pushover(titel = "WatchDog", bericht = "" ):
	try:
		r = requests.post('https://api.pushover.net/1/messages.json', 
			data = {	'token'	:'aYs6YxK8qV1KnGV1LEHzQQtFTrCutk', 
						'user'	:'udEe5uL7YjuyYLyhQXBjvjnqiGGsf8', 
						'title'	:titel,
						'message':bericht})
	except requests.Timeout as e:
		bericht("Pushover - %s"%e)
	except:
		bericht("Pushover - Fout")
	return

def telegram( chat_id="12463680", message = None, image = None ):
	#	johannes_smits	=  "12463680"
	#	alarmsysteem	= "-24143102"
	if not message is None:
		url = "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage"
		payload = {"chat_id":chat_id, "text":message, "parse_mode":"HTML"}
		r = requests.get(url, params=payload)	
		return (r.json()["ok"])
		
	elif not image is None:
		url	= "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendPhoto"
		data	= {'chat_id': chat_id}
		files	= {'photo': (image, open(image, "rb"))}
		r = requests.post(url, data=data, files=files)
		return (r.json()["ok"])
		
def file_get_contents(filename):
	try:
		with open(filename) as f:
			return f.read()
	except:
		return None		
	
bericht("Gestart op de %s"%os.uname()[1],viaPushover=True)
try:
	while True:
		# httplistner (homebridge)
		try:
			resultaat = requests.get("http://localhost:1208?getpid", timeout=4)
			if (resultaat.status_code == requests.codes.ok):
				if int(resultaat.text) != watchedpids["httplistner"]:
					bericht("PID van HTTPListner is %s"%int(resultaat.text))	
					watchedpids["httplistner"] = int(resultaat.text)

		except requests.Timeout as e:
			bericht("Timeout: %s"%e)

			if not watchedpids["httplistner"]:
				jsonpid = file_get_contents("/var/tmp/httplistner.pid")
				watchedpids["httplistner"] = int(jsonpid["pid"]) if jsonpid else 0
				
			if watchedpids["httplistner"]:	#	indien 0 (zichzelf) dan niks doen
				bericht("Geen reactie, stuur nu SIGINT naar PID %s"%watchedpids["httplistner"],False)	
				os.kill(watchedpids["httplistner"], signal.SIGINT)
				#time.sleep(0.1)	#	na kleine pauze gelijk weer testen
				continue
			else:
				bericht("Geen reactie van httplistner, geen PID bekend")

		time.sleep(120)	# twee minuutjes rust

except KeyboardInterrupt:
	bericht ('ctrl-C ontvangen, watchdog wordt gestopt')
	subprocess.call("/usr/bin/screen -dmLS watchdog python3 %s"%__file__, shell=True)
