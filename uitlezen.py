import sys
import serial
import requests
import datetime
import time
import json

##############################################################################
#Main program
##############################################################################

#Set COM port config
ser = serial.Serial()
ser.baudrate = 115200
ser.bytesize=serial.EIGHTBITS
ser.parity=serial.PARITY_NONE
ser.stopbits=serial.STOPBITS_ONE
ser.xonxoff=0
ser.rtscts=0
ser.timeout=20
ser.port="/dev/ttyUSB0"

thingspeakapi = '0SSAA5SGLQ0IZQRQ'

#Open COM port
try:
    ser.open()
except:
    sys.exit ("Fout bij het openen van %s."  % ser.name)

lasttime = time.time()
gasm3uur = 0
teller	= 0
waarden	= {"laag":0,"hoog":0,"tarief":0,"vermogen":0,"stroom":0,"meterstnd":0, "tydmeting":0}
vorige	= {"meterstnd":0, "tydmeting":0}

print("\033[2J\033[1;1HUitlezen energiemeter\n\033[3mControl-C om te stoppen\033[0m")
try:
	while True:
		p1_line=' '
		while (p1_line[0] != "!"):
			try:
				p1_raw = ser.readline().decode("utf-8") 
			except KeyboardInterrupt:
				ser.close()
				sys.exit('\nAfsluiten...\n')
			except:
				print("Fout bij het lezen van seriele poort\n")
				continue
			
			p1_str=str(p1_raw)
			p1_line=p1_str.strip()
		
			if not p1_line:
				p1_line= " "

			if   (p1_line.find("1-0:1.8.1") != -1):
				waarden["laag"] = float(p1_line.split("(")[1].split("*")[0])
			elif (p1_line.find("1-0:1.8.2") != -1):
				waarden["hoog"] = float(p1_line.split("(")[1].split("*")[0])
			elif (p1_line.find("0-0:96.14.0") != -1):
				waarden["tarief"] = int(p1_line.split("(")[1].split(")")[0])
			elif (p1_line.find("1-0:1.7.0") != -1):
				waarden["vermogen"] = int(p1_line.split("(")[1].split("*")[0].replace(".",""))
			elif (p1_line.find("1-0:31.7.0") != -1):
				waarden["stroom"] = int(p1_line.split("(")[1].split("*")[0].replace(".",""))
			elif (p1_line.find("0-1:24.2.1") != -1):
				waarden["tydmeting"] = int(p1_line.replace("0-1:24.2.1", "").split(")")[0][1:12])
				waarden["meterstnd"] = float(p1_line.split("(")[2].split("*")[0])
				
			print("\033[8;1H\033[2KMeter: %s"%p1_line)
			
		print( json.dumps(waarden) )
		
		teller += 1
		if teller > 10: # eens in de 10 lezingen de html schrijven
			teller = 0

			html = '<html><head><META HTTP-EQUIV="refresh" CONTENT="15"><style>body{color:white;font-family: sans-serif;font-size:12px;text-shadow:rgba(200,200,200,0.5) 1px 2px 2px;}</style></head><body>'
			html =  html + "<table border=0 style='background-color:rgba(40,40,40,0.1);font-size:12px;width:97vw;'>"
			html =  html + "<tr><td>Verbruik <small>%s <i>(%starief)</i></small></td><td align='right'><b>%d Wh</b></td></tr>"%(time.strftime("%H:%M"),('hoog' if waarden["tarief"]==2 else 'laag'),waarden["vermogen"])
			html =  html + "<tr><td>Gasverbruik afgelopen uur</td><td align='right'>%0.2f &#13221;</td></tr>"%gasm3uur
			html =  html + "<tr><td>Stroom nu</td><td align='right'>%d A</td></tr>"%waarden["stroom"]
			html =  html + "<tr><td>Meterstand</td><td align='right'></td></tr>"
			html =  html + "<tr><td>&emsp;- elektriciteit laag </td><td align='right'>%0.3f kWh</td></tr>"%waarden["laag"]
			html =  html + "<tr><td>&emsp;- elektriciteit hoog </td><td align='right'>%0.3f kWh</td></tr>"%waarden["hoog"]
			html =  html + "<tr><td>&emsp;- gas  <small>%s</small></td><td align='right'>%0.3f &#13221;</td></tr>"%(waarden["tydmeting"],waarden["meterstnd"])
			html =  html + "</table></body></html>";
				
			with open("/var/www/html/energie.html","w") as bestand:
				bestand.write(html)
			print("\033[4;1H\033[2K[%s] Energie.html geschreven\n"%time.strftime("%H:%M:%S"))
			
		#iedere vijf minuten upload naar thingspeak
		if (time.time()-lasttime) > 300:
			lasttime = time.time()
			gasm3uur = (waarden["meterstnd"]-vorige["meterstnd"]) if vorige["tydmeting"] != 0 else 0
			print("\033[4;1H\033[2K[%s] Gas gebruik %s"%(time.strftime("%H:%M:%S"),gasm3uur))

			vorige["meterstnd"] = waarden["meterstnd"]
			vorige["tydmeting"] = waarden["tydmeting"]
			
			print("\033[3;1H\033[2K[%s] Gegevens worden nu naar ThingSpeak geschreven"%time.strftime("%H:%M:%S"))
			try:
				r = requests.get("https://api.thingspeak.com/update?api_key=%s&field1=%0.3f&field2=%0.3f&field3=%0.2f&field4=%0.3f&field5=%d&field6=%0.3f" % (thingspeakapi, waarden["laag"], waarden["hoog"], waarden["vermogen"], waarden["meterstnd"], waarden["stroom"], gasm3uur), timeout=1)
				print("\033[3;1H\033[2K[%s] Update ThingSpeak is gelukt"%time.strftime("%H:%M:%S"))
			except requests.exceptions.Timeout:
				print("\033[3;1H\033[2K[%s] Update ThingSpeak mislukt"%time.strftime("%H:%M:%S"))
				continue
			except:
				print("\033[3;1H\033[2K[%s] Update ThingSpeak mislukt, vage shit"%time.strftime("%H:%M:%S"))
				continue
				
			time.sleep(61-int(time.strftime("%S"))) #slaap de rest van de minuut

except KeyboardInterrupt:
	print ('\nAfsluiten...\n')
	ser.close()
