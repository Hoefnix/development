import RPi.GPIO as GPIO
import StringIO
import subprocess
import glob, os
import time
from datetime import datetime
from PIL import Image, ImageStat, ImageDraw, ImageFont
import ephem
import json
import requests
import socket
import picamera
from fractions import Fraction

sensor	=  4	# (gpio 7)
extern	= 22	# (gpio 3)

led1	=  7	# (gpio 5)
led2	= 25	# (gpio 6)

# voor de telegram bot
tgAPIcode  = "112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU"
botAPIcode = "328955454:AAEmupBEwE0D7V1vsoB8Xo5YY1wGIFpu6AE"	#kattenluikbot

JSONresult= "/var/tmp/result.json"
Johannes_Smits = "12463680" 
jsm = "12463680" 
kattenluikID = "-12086796"
luikChat = "-12086796"

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
vorigefoto = time.time()

# File photo size settings
saveWidth	= 512
saveHeight	= 512

pauze = 30
UDP_PORT = 5005
gestart = time.time()

class lichtsterkte(object):
	def __init__(self, seconden=300):
		self.start = 0
		self.interval = seconden
		self.lichtsterkte = 0
		self.check()
		bericht ("Class lichtsterkte is gereed, waarde is %s"%(self.lichtsterkte))
			
	def check(self):
		if time.time()-self.start < self.interval:
			return self.lichtsterkte
		self.start = time.time()
		
		command = "raspistill -ISO 200 -w %s -h %s -roi 0.55,0.15,0.4,0.4 -t 50 -n -e bmp -o -" % (100, 100)
		imageData = StringIO.StringIO()
		imageData.write(subprocess.check_output(command, shell=True))
		imageData.seek(0)
	
		im = Image.open(imageData).convert('L')
		stat = ImageStat.Stat(im)
	
		with open('/var/www/html/lichtsterkte.json', 'w') as myfile:
			data = myfile.write('{"licht":%s}'%int(stat.mean[0]))
					
		self.lichtsterkte = int(stat.mean[0])
		return self.lichtsterkte
		
def indenacht():
	laatste_foto = time.time() - 10
	telegram(kattenluikID, message = unichr(10024))

	sock.settimeout(600)
	while night():
		#licht.check()
		
		if (time.time() - gestart) > 86400:
			os.system('kill %d' % os.getpid())

		try:
			data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			
			if "kattenluik" in data:
				bericht ( "%s %s"%(data, addr) )

			if data == '{"kattenluik":1}':
				maakfoto( iso = 800 )
				continue #sla de rest over
				
			elif data == '{"kattenluik":"foto"}':
				maakfoto( iso = 800 )

			elif data == '{"kattenluik":"test"}':
				testFoto()

		except socket.timeout:
			continue
			
	sock.settimeout(0.1)
	telegram(kattenluikID, message = unichr(9728))
	return

def maakfoto(wdth=512,hght=512,iso=200):
	global vorigefoto
	
	tijd = datetime.now()
	filename = filenamePrefix + "-%04d%02d%02d-%02d%02d%02d.jpg" % ( tijd.year, tijd.month, tijd.day, tijd.hour, tijd.minute, tijd.second)
	fullname = filepath + "/" + filename
	bericht("seconden tussen fotos %s"%(time.time() - vorigefoto) )			
	if (time.time() - vorigefoto) > 7: # zit er x seconden tussen ?
		vorigefoto = time.time()
		
		timeout = "-t 350" if iso <= 200 else "-t 1 -ss 30000"
		
		if licht.lichtsterkte < 75:
			bericht ("(%s) Flits..."%licht.lichtsterkte)
			GPIO.output(led1, 1)
			GPIO.output(led2, 1)
			
		subprocess.call("raspistill --nopreview -w %s -h %s -ISO  %s -e jpg -q 15 %s -o %s" % (wdth, hght, iso, timeout, fullname), shell=True)

		GPIO.output(led1, 0)
		GPIO.output(led2, 0)
		
		if not deurisopen():		
			telegram(luikChat, image = fullname)
		else:
			bericht ("%s niet verzonden, deur is open"%fullname)
	else:
		bericht ("%s niet verzonden, te snel na elkaar"%fullname)

	# daarna de oude fotos wegwerken
	filelist = glob.glob("%s/kl*.jpg" % filepath)
	for f in filelist:
		os.remove(f)

def deurisopen():
	opendeur = False
	try:
		resultaat = requests.get("http://192.168.178.203", timeout=2)
	except requests.Timeout as e:
		return opendeur
	except requests.exceptions.RequestException as e:
		return opendeur
                
	if (resultaat.status_code == requests.codes.ok):
		opendeur = int( resultaat.json()["keukendeur"] )
		
	return opendeur
	
# Capture a small test image (for motion detection)
def captureTestImage():
	command = "raspistill -ISO 200 -w %s -h %s -roi 0.55,0.15,0.4,0.4 -t 50 -n -e bmp -o -" % (100, 100)
	imageData = StringIO.StringIO()
	imageData.write(subprocess.check_output(command, shell=True))
	imageData.seek(0)
	im = Image.open(imageData)
	buffer = im.load()
	imageData.close()
	# return im, buffer
	return buffer

def testFoto():
	testfoto = "/var/tmp/testfoto.jpg"
	command = "raspistill -ISO 200 -w %s -h %s -roi 0.55,0.15,0.4,0.4 -t 50 -n -e bmp -o -" % (100, 100)
	imageData = StringIO.StringIO()
	imageData.write(subprocess.check_output(command, shell=True))
	imageData.seek(0)

	image = Image.open(imageData)
	draw  = ImageDraw.Draw(image)
	font = ImageFont.load_default()
	draw.text( (10,90), "test", fill='#a00000', font=font)
	image.save(testfoto, "JPEG")

	telegram(image = testfoto)
	os.remove(testfoto)

def telegram( chat_id="12463680", message = None, image = None ):
	if not message is None:
		url = "https://api.telegram.org/bot328955454:AAEmupBEwE0D7V1vsoB8Xo5YY1wGIFpu6AE/sendMessage"
		payload = {"chat_id":chat_id, "text":message, "parse_mode":"HTML"}
		r = requests.get(url, params=payload)	
		return (r.json()["ok"])
		
	elif not image is None:
		url	= "https://api.telegram.org/bot112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU/sendPhoto"
		data	= {'chat_id': chat_id}
		files	= {'photo': (image, open(image, "rb"))}
		r = requests.post(url , data=data, files=files)
		return (r.json()["ok"])

def night():
	# where am i 
	o = ephem.Observer()
	o.lat  = '51.916905'
	o.long =  '4.563472'
		
	# define sun as object of interest
	s = ephem.Sun()
	sunrise = o.next_rising(s)
	sunset  = o.next_setting(s)

	sr_next = ephem.localtime(sunrise)
	ss_next = ephem.localtime(sunset)		

	return 1 if (sr_next < ss_next) else 0
	
def strtonum(str):
	try: 
		return int(str) 
	except ValueError: 
		return 0
		
def bericht(message=None, viaTelegram=False, viaPushover=False):
	if not message is None:
		print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),message))
		if viaTelegram:
			telegram(message = message)
		if viaPushover:
			pushover(bericht = message)

def pushover( bericht = "" ):
	try:
		r = requests.post('https://api.pushover.net/1/messages.json', data = {'token':'aYs6YxK8qV1KnGV1LEHzQQtFTrCutk', 'user':'udEe5uL7YjuyYLyhQXBjvjnqiGGsf8', 'title':'Kattenluik', 'message':bericht})
	except requests.Timeout as e:
		bericht("Pushover - %s"%e)
	except:
		bericht("Pushover - Fout")
	return
	
# Get first image
buffer1 = captureTestImage()
buffer2 = buffer1

sock	= socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.settimeout(0.1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', UDP_PORT)) 

bericht ("%s is gestart"%__file__, viaPushover = True)
bericht ("ctrl-c voor een herstart\n")
vorige = ""

try:
	licht	= lichtsterkte(300) # iedere vijf minuten lichtsterkte checken
	
	while (True):
		if (time.time() - gestart) > 43200: # 86400:
			os.system('kill %d' % os.getpid())

		licht.check()
		
		if night():
			indenacht()
			continue
		
		try:
			data, addr = sock.recvfrom(65535)
			try:
				watte = json.loads(data.strip())["kattenluik"]
			except:
				 continue
			
			if watte in ["test", "foto", "1", "0"]:
				 bericht ("UDP: '%s', opdracht: '%s' (%s)"%(data, watte, addr))
				 
			if	 watte == "test":
				bericht("testfoto wordt nu gemaakt...")
				testFoto()
			elif watte == "foto":
				bericht("foto van kattenluik wordt nu gemaakt...")
				maakfoto()
			elif watte == 1:
				bericht("Kattenluik gaat open...")
			elif watte == 0:
				bericht("...kattenluik weer dicht")
			else:
				bericht("%s onbekende opdracht: '%s'..."%(time.strftime("%a om %H:%M:%S"), watte) )
			continue
				
		except socket.timeout:
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
				maakfoto()
				buffer1 = captureTestImage()
				buffer2 = buffer1

			# Swap comparison buffers
			buffer1 = buffer2
			time.sleep(0.1)	# geef CPU wat lucht 

except (KeyboardInterrupt):# , RuntimeError, TypeError, NameError, ValueError):
	print (time.strftime("%a om %H:%M:%S")+ "\nShutting down...")
	GPIO.output(led1, 0)
	GPIO.output(led2, 0)
	GPIO.cleanup()
	sock.close()	# close UDP socket
	
	subprocess.call("screen -dmS kattenluik python %s"%__file__, shell=True)
	print ("Done, bye bye\n")
