#!/usr/bin/python.

import time
import subprocess
import os
from random import randint
import datetime
import stat  
import socket
import json
import requests

tgAPIcode  = "112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU"
Johannes_Smits = "12463680"

def TelegramMsg( bericht="afentoe", chat_id="12463680" ):
	payload = {"chat_id":chat_id, "text":bericht, "parse_mode":"HTML"}
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage", params=payload)	
	return (r.json()["ok"])

TelegramMsg("<i>afentoe</i> op de <b>%s</b> is gestart "% (socket.gethostname()) + time.strftime("om %H:%M:%S") )
print ("\033[2JBureaulamp aan/uit op de %s is gestart"% (socket.gethostname()) + time.strftime("om %H:%M:%S") )
print("Druk op Ctrl-C om te stoppen")

try:
	while True:
		r = requests.get("http://192.168.178.202/gpio04=aan")
		slapen = randint(600,7200)
		print( "Bureaulamp is nu aan, gaat uit over %s minuten" % (slapen/60), Johannes_Smits )
		time.sleep( slapen )
		
		r = requests.get("http://192.168.178.202/gpio04=uit")
		slapen = randint(600,7200)
		print( "Bureaulamp is nu uit, gaat aan over %s minuten" % (slapen/60), Johannes_Smits )
	
except KeyboardInterrupt:
 	print ("Even opruimen...")
 	print ("Klaar")
