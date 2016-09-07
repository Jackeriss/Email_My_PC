#coding = utf-8
import os
import sys
import time
import socket
import urllib2
import ConfigParser
from send import *

#开机启动本程序，发送开机启动邮件后将启动Email My PC本体，并关闭本程序
def main():
	config = ConfigParser.ConfigParser()
	config.read("config.ini")
	smtpserver = config.get("mail", "smtpserver")
	smtpport = config.get("mail", "smtpport")
	secret_user = config.get("mail", "user")
	user = ""
	for i in range(0,len(secret_user)):
		user += chr(ord(secret_user[i]) ^ 7)
	secret_passwd = config.get("mail", "passwd")
	passwd = ""
	for i in range(0,len(secret_passwd)):
		passwd += chr(ord(secret_passwd[i]) ^ 5)
	autostart = config.get("settings", "autostart")
	startsend = config.get("settings", "startsend")
	delay = float(config.get("settings", "delay"))
	if startsend == "1":
		time.sleep(60 * delay)
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
				message = "<p>电脑名称：%s</p><p>开机时间：%s</p><p>IP地址：%s</p><p>地理位置：%s</p>" % (pc_name, current_time, ip, location.decode("gb2312").encode("utf8"))
				send(smtpserver, smtpport, user, user, passwd, title=title, msg=message)
	try:
		os.startfile("Email My PC.exe")
	except:
		pass
	finally:
		sys.exit()

if __name__ == '__main__':
	main()
