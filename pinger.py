import os
import requests
import time

while True:
        time.sleep(30)
	print "next try.." 
	rawPingFile = os.popen('ping -c 1 %s' % "192.168.178.16")
	rawPingData = rawPingFile.readlines()
	rawPingFile.close()
	
	# Extract the ping time     
	if len(rawPingData) < 2:
		print "192.168.178.16 not found" 
	else:
		index = rawPingData[1].find('time=')
		if index == -1:
			print "Ping failed or timed out" 
		else:
			print "Is pingbaar" 

