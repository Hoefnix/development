import RPi.GPIO as GPIO
import StringIO
import subprocess
import glob, os
import time
from datetime import datetime
from PIL import Image
import ephem
import json
import requests
import socket

sensor	=  4	# (gpio 7)
extern	= 22	# (gpio 3)

led1	=  7	# (gpio 5)
led2	= 25	# (gpio 6)

# voor de telegram bot
tgAPIcode = "112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU"
JSONresult= "/var/tmp/result.json"
Johannes_Smits = "12463680" 
kattenluikID = "-12086796"

fotosperminuut = 0
startvanminuut = time.time()
 
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(sensor, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(extern, GPIO.IN, GPIO.PUD_DOWN)

GPIO.setup(led1, GPIO.OUT) 
GPIO.setup(led2, GPIO.OUT) 

# Motion detection settings:
# need future changes to read values dynamically via command line parameter or xml file
# --------------------------
# Threshold      - (how much a pixel has to change by to be marked as "changed")
# Sensitivity    - (how many changed pixels before capturing an image) needs to be higher if noisy view
# filepath       - location of folder to save photos
# filenamePrefix - string that prefixes the file name for easier identification of files.

threshold = 50
sensitivity = 400 
forceCapture = True
filepath = "/var/tmp"
filenamePrefix = "kl"
previousfile = "previous"

#Latitude en Longitude van thuis
home_lat  = '51.916905'
home_long =  '4.563472'

# File photo size settings
saveWidth	= 512
saveHeight	= 512

pauze = 30
UDP_PORT = 5005

def nightmode():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
	sock.setblocking(0)
	sock.settimeout(5.0)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(('', UDP_PORT)) 

	tgSendMessage(Johannes_Smits, "Nachtmodus wordt gestart op %s luistert naar UDP poort %s" % (socket.gethostname(), UDP_PORT))
	while night():
		try:
			data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			if data == "kattenluik=1":
				saveImage(saveWidth, saveHeight, 800)
		except socket.timeout:
			continue
	tgSendMessage(Johannes_Smits, "Nachtmodus wordt gestopt")

	sock.close()
	return
			
def nachtmodus():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(('', UDP_PORT)) 
	
	tgSendMessage(Johannes_Smits, "Nachtmodus wordt gestart op %s luistert naar UDP poort %s" % (socket.gethostname(), UDP_PORT))
	while night():
		data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
		if data == "kattenluik=1":
			saveImage(saveWidth, saveHeight, 800)

	tgSendMessage(Johannes_Smits, "Nachtmodus wordt gestopt")	
	sock.close()
	return

def deurisopen():
	opendeur = False
	try:
		resultaat = requests.get("http://192.168.178.203")
	except requests.exceptions.RequestException as e:
		return opendeur
                
	if (resultaat.status_code == requests.codes.ok):
		opendeur = int( resultaat.json()["keukendeur"] )
		
	return opendeur
	
def beweging( channel ):
	# print ("(%s) beweging gezien" % channel)
	saveImage(saveWidth, saveHeight, 800)

# Capture a small test image (for motion detection)
def captureTestImage():
	command = "raspistill -ISO 200 -w %s -h %s -roi 0.25,0.25,0.5,0.5 -t 50 -n -e bmp -o -" % (100, 100)
	imageData = StringIO.StringIO()
	imageData.write(subprocess.check_output(command, shell=True))
	imageData.seek(0)
	im = Image.open(imageData)
	buffer = im.load()
	imageData.close()
	# return im, buffer
	return buffer

def testFoto():
	subprocess.call("raspistill --nopreview -ISO 200 -w %s -h %s -roi 0.25,0.25,0.5,0.5 -t 50 -n -e jpg -o %s" % (100, 100, "/var/tmp/testfoto.jpg"), shell=True)
	tgSendPhoto(Johannes_Smits, "/var/tmp/testfoto.jpg")
	os.remove("/var/tmp/testfoto.jpg")

# Save a full size image 
def saveImage(width, height, iso):
	global fotosperminuut
	global startvanminuut

	# eerst de oude fotos wegwerken
	filelist = glob.glob("%s/kl*.jpg" % filepath)
	for f in filelist:
		os.remove(f)

	if ((time.time() - startvanminuut) <= 60):
		fotosperminuut += 1
	else:
		fotosperminuut = 0
		startvanminuut = time.time()
		
	if (fotosperminuut > 4 ):
		time.sleep(30)
		startvanminuut = time.time()
		fotosperminuut = 0
	else:
		tijd = datetime.now()
		filename = filenamePrefix + "-%04d%02d%02d-%02d%02d%02d.jpg" % ( tijd.year, tijd.month, tijd.day, tijd.hour, tijd.minute, tijd.second)
		fullname = filepath + "/" + filename
	
		if not deurisopen():
			parameter = "-t 350"
			if (iso > 200 ):
				parameter = "-t 1 -ss 66000"
				GPIO.output(led1, 1)
				GPIO.output(led2, 1)
			
			subprocess.call("raspistill --nopreview -w %s -h %s -ISO %s -e jpg -q 15 %s -o %s" % (width, height, iso, parameter, fullname), shell=True)
		
			GPIO.output(led1, 0)
			GPIO.output(led2, 0)

			tgSendPhoto(kattenluikID, fullname)
	return
		
def tgSendMessage( chat_id="12463680", bericht="Kattenluik" ):
	payload = {"chat_id":chat_id, "text":bericht, "parse_mode":"HTML"}
	r = requests.get("https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendMessage", params=payload)	
	return (r.json()["ok"])

def tgSendPhoto( chat_id="12463680", imagePath="" ):
	url	= "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU"
	data = {'chat_id': chat_id}
	files = {'photo': (imagePath, open(imagePath, "rb"))}
	r = requests.post(url + '/sendPhoto', data=data, files=files)
	return (r.json()["ok"])

def night():
	# where am i 
	o = ephem.Observer()
	o.lat  = home_lat
	o.long = home_long
		
	# define sun as object of interest
	s = ephem.Sun()
	sunrise = o.next_rising(s)
	sunset  = o.next_setting(s)

	sr_next = ephem.localtime(sunrise)
	ss_next = ephem.localtime(sunset)		

	return 1 if (sr_next < ss_next) else 0

def secsuntilsunrise():
	# where am i 
	o = ephem.Observer()
	o.lat  = home_lat
	o.long = home_long
		
	# define sun as object of interest
	sunrise = o.next_rising(ephem.Sun())
	sr_next = ephem.localtime(sunrise)
	
	return (sr_next - datetime.now()).seconds

def strtonum(str):
	try: 
		return int(str) 
	except ValueError: 
		return 0

# Get first image
buffer1 = captureTestImage()
buffer2 = buffer1

print ("\033[0;0H\033[JKattenluikmonitor is gestart op %s\n" % time.strftime("%a om %H:%M:%S") )
print ("\033[Jctrl-c om te stoppen\n")

tgSendMessage(Johannes_Smits, "Kattenluikmonitor gestart" )

try:
	while (True):
		if night():
			nachtmodus()

			# let the interrupt take over and go to sleep
			# GPIO.add_event_detect(sensor, GPIO.RISING, callback=beweging)
			# time.sleep(secsuntilsunrise()+60)
			# GPIO.remove_event_detect(sensor)
			continue
				
		if os.path.isfile("/var/tmp/maakfoto"):
			saveImage(saveWidth, saveHeight, (800 if night() else 200))
			os.remove("/var/tmp/maakfoto")
			continue

		elif os.path.isfile("/var/tmp/testfoto"):
			testFoto()
			os.remove("/var/tmp/testfoto")
			continue
                        
		elif os.path.isfile("/var/tmp/pauze"):
			with open('/var/tmp/pauze', 'r') as f:
    				pauze  = strtonum(f.read())
			pauze = 30 if pauze <= 0 else pauze
			tgSendMessage( kattenluikID, "De komende %s minuten doe ik even niks..." % pauze)
			time.sleep(pauze*60) 
			os.remove("/var/tmp/pauze")
			tgSendMessage( kattenluikID, "... en daar gaan we weer")
			continue

		# Get comparison image
		buffer2 = captureTestImage()
		changedPixels = 0
		for x in xrange(1, 99):
			# Scan one line of image then check sensitivity for movement
			for y in xrange(1, 99):
				# Just check green channel as it's the highest quality channel
				pixdiff = abs(buffer1[x,y][1] - buffer2[x,y][1])
				if pixdiff > threshold:
					changedPixels += 1
					if changedPixels > sensitivity:
						break
			if changedPixels > sensitivity:
				break

		if changedPixels > sensitivity:
			saveImage(saveWidth, saveHeight, 200)
			buffer1 = captureTestImage()
			buffer2 = buffer1
		
		# Swap comparison buffers
		buffer1 = buffer2
		time.sleep(0.1)	# geef CPU wat lucht 

except (KeyboardInterrupt):# , RuntimeError, TypeError, NameError, ValueError):
	GPIO.output(led1, 0)
	GPIO.output(led2, 0)
	print (time.strftime("%a om %H:%M:%S")+ " Shutting down...")
	GPIO.cleanup()
	print ("Done")
