#coding = utf-8
import os
import sys
import time
import socket
import urllib2
import ConfigParser
from send import *
def main():
	config = ConfigParser.ConfigParser()
	config.read("config.ini")
	smtpserver = config.get("mail", "smtpserver")
	user = config.get("mail", "user")
	passwd = config.get("mail", "passwd")
	autostart = config.get("settings", "autostart")
	startsend = config.get("settings", "startsend")
	if autostart == "1" and startsend == "1":
		pc_name = socket.gethostname()
		current_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
		url = "http://1212.ip138.com/ic.asp"
		try:
			page = urllib2.urlopen(url)
		except:
			pass
		else:
			text = page.read()
			if "<center>" in text and "</center>" in text:
				text = text[text.index("<center>") + 8:text.index("</center>")]
				info_list = text.split(" ")
				ip = info_list[0]
				ip = ip[ip.index("[")+1:]
				ip = ip[:ip.index("]")]
				location = info_list[1]
				location = location[6:]
				title = "您的电脑当前有开机动作！"
				message = "电脑名称：%s\n开机时间：%s\nIP地址：%s\n地理位置：%s" % (pc_name, current_time, ip, location.decode("gb2312").encode("utf8"))
				send(smtpserver, user, passwd, title = title, msg = message)
	try:
		os.startfile("Email My PC.exe")
	except:
		pass
	finally:
		sys.exit()
if __name__ == '__main__':
	main()
