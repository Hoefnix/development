import requests
import time
import socket

pauze = 30
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.setblocking(0)
sock.settimeout(5.0)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', UDP_PORT)) # udp port 5005

print ("\033[2JMonitor UDP/5005")
print ("\033[3mControl-C om te stoppen\033[0m")

try:
	while (True):
		try :
        		data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			print ("[%s]" % data)
			r = requests.get("http://192.168.178.100/esp8266/telegram.php?%s" % data)	
		except socket.timeout:
#			print("\033[5;1H\033[K"+time.strftime("%a om %H:%M:%S")+" nothing...")
			continue

except (KeyboardInterrupt):# , RuntimeError, TypeError, NameError, ValueError):
        sock.close()
        print ("Done")
