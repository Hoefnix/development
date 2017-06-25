# monitor voor aantal zaken
# - deurbel (nog niet aangesloten)
# - geluidssensor (voor het alarm)
# - UDP poort 5005 
# - waarschuwen als niemand thuis is 

import datetime
import os
import socket
import time

# Instellen UDP listener
UDP_PORT = 1208
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.setblocking(0)
sock.settimeout(0.1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', UDP_PORT)) # udp port 5005


try:
	while True:
		try :
			jsonstr, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			print ("[%s] UDP: %s (%s)" % (time.strftime("%a om %H:%M:%S"), jsonstr.strip(), addr) )
				
		except socket.timeout:
			continue

except (KeyboardInterrupt):#, RuntimeError, TypeError, NameError, ValueError):
	print time.strftime("%a om %H:%M:%S")+ " Shutting down..."
	sock.close()
	print "Done"
