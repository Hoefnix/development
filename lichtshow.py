import random
import socket
import time

def toHex(dec):
    x = (dec % 16)
    digits = "0123456789ABCDEF"
    rest = dec / 16
    if (rest == 0):
        return digits[x]
    return toHex(rest) + digits[x]

UDP_PORT = 1208

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # internet, UDP 
sock.bind(('', 0))
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
  
print ("\033[0;0H\033[JLichtshowis gestart op %s\n" % time.strftime("%a om %H:%M:%S") )
print ("\033[Jctrl-c om te stoppen\n")

try:
	while True:
		rood  =	("00"+toHex(random.randint(0,255)))[-2:]
		groen =	("00"+toHex(random.randint(0,255)))[-2:]
		blauw =	("00"+toHex(random.randint(0,255)))[-2:]
		pauze = random.random()/random.randint(1,100)
		
		kleur = "#%s%s%s"%(rood,groen,blauw)
		print("\033[3;0H\033[J%s, %s"%(kleur, pauze))

		sock.sendto(kleur,('<broadcast>', UDP_PORT))
		time.sleep(pauze)	# geef CPU wat lucht 

except (KeyboardInterrupt):# , RuntimeError, TypeError, NameError, ValueError):
	print (time.strftime("%a om %H:%M:%S")+ " aan het afsluiten...")
	sock.close()
	print ("Done")
