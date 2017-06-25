# monitor op UDP poort 5005 op JSON met duplicator er in.
#
# mogelijkheden:
#	{"duplicator":"licht"}
#	{"duplicator":"scherm"}
#	{"duplicator":"status"}
#
# de rest wordt genegeerd.
#
import subprocess 
import time 
import socket 
import json

UDP_IP = "192.168.178.11" 
UDP_PORT = 5005 

lichtpin = 4 # gpio4
schrmpin = 5 # gpio5
printpin = 5 # gpio5

class gpioinit( object ):
	def write(self, pin, waarde):
		return 1 - subprocess.call("/usr/local/bin/gpio write %s %s"%(pin,waarde), shell=True )

	def read(self, pin):
		out = int(subprocess.check_output("/usr/local/bin/gpio read %s"%pin, shell=True )[0])
		return out

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.setblocking(0) 
sock.settimeout(5.0) 
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
sock.bind(('', UDP_PORT)) # udp port 5005

gpio = gpioinit()

#initieel alles uit
gpio.write(lichtpin, 0)
gpio.write(printpin, 0)

print ("\033[2JDuplicator commando monitor") 
print ("\033[3mControl-C om te stoppen\033[0m")

try:
	while True:
		try:
			jsonstr, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			if "duplicator" in jsonstr:
				print(time.strftime("%a om %H:%M:%S")+" - "+jsonstr)
				try:
					ontvangen = json.loads(jsonstr.strip())["duplicator"]
				except:
					print("...fout in JSON")
					continue
					
				if "status" in ontvangen:
					terug = '{"licht":%s'%gpio.read(lichtpin)+', "scherm":%s'%gpio.read(schrmpin)+'}'
					print ("sending: %s"%terug)
					sock.sendto(terug, addr)
					continue
					
				elif "licht" in ontvangen:
					pin = lichtpin
					waarde = 1 if gpio.read(pin) == 0 else 0
					print("Licht wordt geschakeld. Waarde is nu %s wordt %s "%(gpio.read(pin), waarde))
					
				elif "scherm" in ontvangen:
					pin = schrmpin
					waarde = 1 if gpio.read(pin) == 0 else 0
					print("Scherm wordt geschakeld. Waarde is nu %s wordt %s "%(gpio.read(pin), waarde))
					
				elif "printr" in ontvangen:
					pin = printpin
					waarde = 1 if gpio.read(pin) == 0 else 0
					print("Printer wordt geschakeld. Waarde is nu %s wordt %s "%(gpio.read(pin), waarde))

				else:
					print("...ongeldig commando (licht/printr/scherm/status)")
					continue
							
				gpio.write(pin, waarde)
				print("waarde is nu %s "%gpio.read(pin))
		
		except socket.timeout:
			continue

except (KeyboardInterrupt):#, RuntimeError, TypeError, NameError, ValueError):
	print time.strftime("%a om %H:%M:%S")+ " Shutting down..."
	sock.close()
	print "Done"
