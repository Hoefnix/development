#!/usr/bin/python
import requests
import time
import socket

PORT_NUMBER = 85

def bericht(message=None, viaTelegram=False, viaPushover=False):
	if not message is None:
		print("\033[3m%s\033[0m - %s\033[0m"%(time.strftime("%H:%M:%S"),message))
			
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(('localhost', PORT_NUMBER))
serversocket.listen(5) # become a server socket, maximum 5 connections
try:
	bericht("listening on %s to %s"%('localhost', PORT_NUMBER))
	while True:
		connection, address = serversocket.accept()
		buf = connection.recv(64)
		if len(buf) > 0:
			print ( buf)
			break
    
except KeyboardInterrupt:
	bericht("ctrl-c ontvangen, webserver wordt opnieuw gestart", viaPushover = True)
	# subprocess.call("/usr/bin/screen -dmS woonveilig python3 /opt/development/woonveilig.py", shell=True)