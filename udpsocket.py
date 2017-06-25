# sudo sendip -p ipv4 -is 192.168.178.11 -p udp -us 5005 -ud 5005 -d "Hello" -v 192.168.178.11

import socket 

UDP_IP = "192.168.178.11" 
UDP_PORT = 5005 

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP 

sock.bind(('0.0.0.0', 5005)) 

while True:
	data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
	print "received message:", data, addr

