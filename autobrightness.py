#!/usr/bin/python

# fotos maken als hij te donker is dan een opnieuw met een hogere brightness
# wanneer foto beschouwd wordt als te-donker wordt bepaald door de waarde van tedonker... 
# als brightness 100% en nog steeds te donker, dan toch maar versturen 

import datetime
import ephem 
import os
import subprocess
import time
from PIL import Image, ImageStat

filename = '/var/tmp/bureau.jpg'

def brabbel(bericht):
	print bericht
	subprocess.call("echo 'msg Johannes_Smits %s' | nc 127.0.0.1 1208" % bericht, shell=True)
	
def night():
        #where am i 
        o = ephem.Observer()
        o.lat  = '51.916905'
        o.long =  '4.563472'

        #define sun as object of interest
        s = ephem.Sun()
        sunrise = o.next_rising(s)
        sunset  = o.next_setting(s)

        sr_next = ephem.localtime(sunrise)
        ss_next = ephem.localtime(sunset)

        if sr_next < ss_next:
                return 1
        return 0

def helderheid( im_file ):
	im = Image.open(im_file).convert('L')
	stat = ImageStat.Stat(im)
	return int(stat.mean[0])

brightness = 50 if night() else 0
contrast = 50	
opnieuw = True
tedonker = 60

while opnieuw:
	opnieuw = False
	
	f = open('/var/tmp/foto.cfg', 'w')
	if (f.mode == "w"):
		f.write("device v4l2:/dev/v4l/by-id/usb-Vimicro_Vimicro_USB_Camera__Altair_-video-index0\n")
		# f.write("device v4l2:/dev/v4l/by-id/usb-Image_Processor_USB_2.0_PC_Cam-video-index0\n")
		f.write("input 0\nresolution 160x120\nno-banner\njpeg 80\n")
		f.write("set brightness=%s%%\nsave %s\n" % (brightness, filename))
		f.close()

	subprocess.call("/usr/bin/fswebcam -q -c /var/tmp/foto.cfg", shell=True)
	waarde = helderheid( filename )
	if (waarde < tedonker):
		print("Te donker (%s) met brightness (%s%%), opnieuw..." % (waarde, brightness))
		opnieuw = True
		brightness += 10
		if (brightness >= 100): # meer dan 100% heeft geen zin. het is blijkbaar pikkedonker
			opnieuw = False

print "Config wordt geschreven...\n"
contrast = 50+(brightness/5) # fotos met hoge brightness zien er beter uit met hogere contrast
f = open('/var/tmp/foto.cfg', 'w')	
if (f.mode == "w"):
	f.write("device v4l2:/dev/v4l/by-id/usb-Vimicro_Vimicro_USB_Camera__Altair_-video-index0\n")
	# f.write("device v4l2:/dev/v4l/by-id/usb-Image_Processor_USB_2.0_PC_Cam-video-index0\n")
	f.write("input 0\nresolution 640x480\njpeg 80\n")
	f.write('title "smits.smit"\nsubtitle "werk in de straat"\ntimestamp "%d-%m-%Y %H:%M:%S (%Z)"\n')
	f.write('info "brightness=%s%% contrast=%s%%"\n' % (brightness, (40+(brightness/5))))
	f.write("set brightness=%s%%\nsave %s\n" % (brightness, filename))
	f.write("set contrast=%s%%\n" % (50+(brightness/10)) )
	f.close()
		
subprocess.call("/usr/bin/fswebcam -q -c /var/tmp/foto.cfg ", shell=True)
print("Foto genomen met een brightness van %s%%" % brightness)
newname = "/var/tmp/"+time.strftime("%Y%m%d%H%M%S")+".jpg"
subprocess.call("/opt/develop/tocopycom.sh %s %s" % (filename, newname), shell=True)
