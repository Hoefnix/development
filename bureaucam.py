import subprocess
import time
from datetime import datetime
import requests
import socket
import ephem 

# voor de telegram bot
tgAPIcode  = "112338525:AAGyQLESoyVnCAdBJZTdaRcgV5KwN3uGipU"
botAPIcode = "328955454:AAEmupBEwE0D7V1vsoB8Xo5YY1wGIFpu6AE"	#kattenluikbot

jhsmChat =  "12463680" 
luikChat = "-12086796"

vorigefoto = time.time()
UDP_PORT = 5005

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

def httpGet( httpCall, wachten = 5):
	#bericht( "\033[33mhttpGet: %s"%httpCall )
	resultaat = requests.Response
	try:
		resultaat = requests.get(httpCall, timeout=wachten)
	except requests.Timeout as e:
		bericht("\033[31m%s: url=%s, timeout=%s"%(e, httpCall, wachten))
		resultaat.status_code = 999
	except:
		bericht("\033[31mFout: url=%s, timeout=%s"%(httpCall,wachten))
		resultaat.status_code = 999
	return resultaat
	
def bericht(message=None, viaTelegram=False):
	if not message is None:
		print("\033[3m%s\033[0m - %s"%(time.strftime("%H:%M:%S"),message))
		if viaTelegram:
			telegram(jhsmChat, message = message)

sock	= socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.settimeout(600)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', UDP_PORT)) 

bericht ("%s is gestart"%__file__, viaTelegram = True)
bericht ("ctrl-c voor een herstart\n")
vorige = ""

try:
	while True:
		try:
			data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			
			if "kattenluik" in data:
				bericht ( "%s %s"%(data, addr) )
				if night():	# 's-nachts overslaan, in het donker toch geen zin
					continue
					
			if data == '{"kattenluik":1}':	
				if (time.time() - vorigefoto) > 7: # zit er x seconden tussen ?
					time.sleep(0.5) # kleine vertraging om iets recentere foto af te wachten
					vorigefoto = time.time()
					telegram(luikChat, image = "/var/tmp/catcam.jpg")
				else:
					bericht ("foto niet verzonden, te snel na elkaar")
				continue

			elif data == '{"kattenluik":"foto"}':	
				if (time.time() - vorigefoto) > 7: # zit er x seconden tussen ?
					vorigefoto = time.time()
					telegram(luikChat, image = "/var/tmp/catcam.jpg")
				else:
					bericht ("foto niet verzonden, te snel na elkaar")
				continue

		except socket.timeout:
			continue

except (KeyboardInterrupt):# , RuntimeError, TypeError, NameError, ValueError):
	bericht("Herstart...")
	sock.close()	# close UDP socket	
	subprocess.call("screen -dmS catcam python %s"%__file__, shell=True)