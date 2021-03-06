#!/usr/bin/python.

import RPi.GPIO as GPIO 
import time
import subprocess
import os

GPIO.setmode(GPIO.BCM)  
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def erWordtGebeld(channel):
	returncode = subprocess.Popen("/usr/bin/fswebcam -c /opt/develop/deurmonitor.cfg", shell=True)
	print('Deurbel werd ingedrukt op ' + time.strftime("%a om %H:%M:%S"))

GPIO.add_event_detect(24, GPIO.FALLING, callback=erWordtGebeld, bouncetime=500)
print( "Deurbelmonitor is gestart op " + time.strftime("%A om %H:%M:%S") )
print( "Druk op Ctrl-C om te stoppen")

try:
	while True:
		time.sleep(3600)

except KeyboardInterrupt:
 	print "Even opruimen..."
 	GPIO.remove_event_detect(24)
 	GPIO.cleanup()
 	print "Klaar"



