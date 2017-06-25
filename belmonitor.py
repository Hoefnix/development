#!/usr/bin/python.

import RPi.GPIO as GPIO 
import time
import subprocess
import os
import datetime
import stat  
import socket
import json
import requests

namehost = socket.gethostname()

GPIO.setmode(GPIO.BCM)  
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

tgAPIcode  = "112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU"
Johannes_Smits = "12463680"

def erWordtGebeld(channel):
	print('Deurbel werd ingedrukt op ' + time.strftime("%a om %H:%M:%S")+"\n")
	returncode = subprocess.Popen("/usr/bin/fswebcam -c /opt/develop/deurcam.cfg", shell=True)
	time.sleep(1)

def TelegramMsg( chat_id="12463680", bericht="BelenLicht" ):
	payload = {"chat_id":chat_id, "text":bericht, "parse_mode":"HTML"}
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage", params=payload)	
	return (r.json()["ok"])
	
GPIO.add_event_detect(24, GPIO.FALLING, callback=erWordtGebeld, bouncetime=500)
TelegramMsg(Johannes_Smits, "Belmonitor op de <b>%s</b> is gestart "% (socket.gethostname()) + time.strftime("om %H:%M:%S") )

print("Druk op Ctrl-C om te stoppen")

try:
	while True:
		time.sleep(3600)

except KeyboardInterrupt:
 	print ("Even opruimen...")
 	GPIO.remove_event_detect(24)
 	GPIO.cleanup()
 	print ("Klaar")
