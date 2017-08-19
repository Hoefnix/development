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

def telegram( chat_id="-12086796", message = None, image = None ):
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
			telegram(message = message)
			
sock	= socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.settimeout(600)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', UDP_PORT)) 

bericht ("%s is gestart"%__file__, viaTelegram = False)
bericht ("ctrl-c voor een herstart\n")
vorige = ""

try:
	while True:
		try:
			data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
			
			if "kattenluik" in data:
				bericht ( "%s %s"%(data, addr) )
					
			if data == '{"kattenluik":1}':
				if (time.time() - vorigefoto) > 7: # zit er x seconden tussen ?
					subprocess.call("/usr/bin/fswebcam -c /home/osmc/catcam.cfg", shell=True)
					bericht("foto verzonden")
					vorigefoto = time.time()
				else:
					bericht ("foto niet verzonden, te snel na elkaar (v:%s, n:%s)"%(vorigefoto,time.time()))
				continue

			elif data == '{"kattenluik":"foto"}':	
				if (time.time() - vorigefoto) > 7: # zit er x seconden tussen ?
					subprocess.call("/usr/bin/fswebcam -c /home/osmc/catcam.cfg", shell=True)
					bericht("foto verzonden" )
					vorigefoto = time.time()
				else:
					bericht ("foto niet verzonden, te snel na elkaar (v:%s, n:%s)"%(vorigefoto,time.time()))
				continue

		except socket.timeout:
			continue

except (KeyboardInterrupt):# , RuntimeError, TypeError, NameError, ValueError):
	bericht("Herstart...")
	sock.close()	# close UDP socket	
	subprocess.call("screen -dmS catcam python %s"%__file__, shell=True)