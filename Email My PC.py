#coding = utf-8
import sys
import time
import os
import thread
import ConfigParser
import poplib
import subprocess
import pythoncom
import win32con
import win32api
from singleinstance import singleinstance
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
from shell import shell
from shell import shellcon
from PyQt4.QtGui import * 
from PyQt4.QtCore import *
from capture import Device
from PIL.ImageQt import ImageQt
from PIL import ImageGrab
from send import *

#摄像头画面预览
class Cam(QThread):
	trigger = pyqtSignal()

	def __init__(self, parent=None):
		super(Cam, self).__init__(parent)

	def run(self):
		global img
		while cam_open == True:
			try:
				img = ImageQt(cam[cam_no].getImage().resize((240, 180)))
				time.sleep(0.01)
				self.trigger.emit()
			except:
				pass

#重新连接
class Reconnect(QThread):
	trigger = pyqtSignal()

	def __init__(self, parent=None):
		super(Reconnect, self).__init__(parent)

	def run(self):
		time.sleep(5)
		self.trigger.emit()

#淡入提示文字
class In(QThread):
	trigger = pyqtSignal()

	def __init__(self, parent=None):
		super(In, self).__init__(parent)

	def run(self):
		global opacity
		for i in range(opacity, -1, -1):
			opacity = i
			time.sleep(0.01)
			self.trigger.emit()

#淡入淡出提示文字
class Trans(QThread):
	trigger = pyqtSignal()

	def __init__(self, parent=None):
		super(Trans, self).__init__(parent)

	def run(self):
		global opacity, new_trans
		for i in range(opacity, -1, -1):
			opacity = i
			time.sleep(0.01)
			self.trigger.emit()
		time.sleep(2)
		new_trans = False
		for i in range(opacity, 101):
			if new_trans == True:
				break
			opacity = i
			time.sleep(0.01)
			self.trigger.emit()
		new_trans = False

#新邮件检测与命令执行
class Server(QThread):
	trigger1 = pyqtSignal()
	trigger2 = pyqtSignal()
	trigger3 = pyqtSignal()
	trigger4 = pyqtSignal()
	trigger5 = pyqtSignal()
	trigger6 = pyqtSignal()
	trigger7 = pyqtSignal()

	def __init__(self, parent=None):
		super(Server, self).__init__(parent)

	def run(self):
		p = None
		count = 0
		pre_number = -1
		while 1:
			if service == True:
				try:
					if count == 0:
						self.trigger1.emit()
					#绝大多数邮箱不开启加密时的POP端口为110
					if popport == '110':
						p = poplib.POP3(popserver, popport)
					else:
						p = poplib.POP3_SSL(popserver, popport)
				except:
					self.trigger2.emit()
				else:
					try:
						p.user(user)
						p.pass_(passwd)
					except:
						self.trigger3.emit()
					else:
						try:
							resp, mails, octets = p.list()
							number = len(mails)
							if number != pre_number:
								if pre_number != -1:
									resp, lines, octets = p.retr(number)
									msg_content = b'\r\n'.join(lines)
									msg = Parser().parsestr(msg_content)
									info = get_info(msg)
									subject = info[0].strip()
									addr = info[1].strip()
									content = info[2].strip().strip('~!@#$%^&*()_+{}[]\'":?><\\/.,|-=')
									if addr in whitelist:
										thread.start_new_thread(self.processing, (p, subject, content, addr))
						except:
							self.trigger4.emit()
						else:
							if pre_number == -1:
								self.trigger5.emit()
							pre_number = number
						finally:
							try:
								p.quit()
							except:
								self.trigger4.emit()
				count += 1
			else:
				count = 0
				exception_id = -1
				pre_number = -1
				time.sleep(2)
			time.sleep(float(sleep))

	def processing(self, p, subject, content, addr):
		if tag_shutdown in subject:
			command = 'shutdown -s'
			subprocess.Popen('shutdown -s', shell=True)
			title = '成功执行关机命令！'
			send(smtpserver, smtpport, user, addr, passwd, title=title)
		if tag_screen in subject:
			pic_name = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
			pic_name = pic_name + '.jpg'
			pic = ImageGrab.grab()
			pic.save('%s' % pic_name)
			title = '截屏成功！'
			send(smtpserver, smtpport, user, addr, passwd, title=title, file_name=pic_name)
		if tag_cam in subject:
			pic_name = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
			pic_name = pic_name + '.jpg'
			cam[cam_no].getImage().save(pic_name)
			title = '拍照成功！'
			send(smtpserver, smtpport, user, addr, passwd, title=title, file_name=pic_name)
			self.trigger6.emit()
		if tag_button in subject:
			unrecognized = button_event(content)
			if unrecognized == '':
				title = '成功执行快捷键！'
				msg = '<p>已成功执行以下快捷键：</p><p>%s</p>' % content.encode("utf8")
			else:
				title = '存在无法识别的快捷键！'
				msg = '<p>您发送的快捷键为“%s”</p><p>其中快捷键“%s”无法识别</p>' \
				% (content.encode('utf8'), unrecognized.encode('utf8'))
			send(smtpserver, smtpport, user, addr, passwd, title=title, msg=msg)
		if tag_cmd in subject:
			subprocess.Popen(content, shell=True)
			title = '成功执行CMD命令！'
			msg = '<p>已成功执行以下命令：</p><p>%s</p>' % content.encode('utf8')
			send(smtpserver, smtpport, user, addr, passwd, title=title, msg=msg)

#主界面
class Setting_UI(QWidget):
	def __init__(self, parent=None):
		global cam, cam_no, cam_open, opacity, current_page, new_trans
		cam_open = False
		self.dragPosition = None
		current_page = 1
		new_trans = False
		super(Setting_UI, self).__init__(parent)
		#载入样式文件
		close_qss_file = open(unicode('ui/styles/btn_close', 'utf8'), 'r')
		close_qss = close_qss_file.read()
		close_qss_file.close()
		btn1_qss_file = open(unicode('ui/styles/btn1', 'utf8'), 'r')
		btn1_qss = btn1_qss_file.read()
		btn1_qss_file.close()
		btn2_qss_file = open(unicode('ui/styles/btn2', 'utf8'), 'r')
		btn2_qss = btn2_qss_file.read()
		btn2_qss_file.close()
		btn_menu1_qss_file = open(unicode('ui/styles/btn_menu1', 'utf8'), 'r')
		btn_menu1_qss = btn_menu1_qss_file.read()
		btn_menu1_qss_file.close()
		btn_menu2_qss_file = open(unicode('ui/styles/btn_menu2', 'utf8'), 'r')
		btn_menu2_qss = btn_menu2_qss_file.read()
		btn_menu2_qss_file.close()
		btn_menu3_qss_file = open(unicode('ui/styles/btn_menu3', 'utf8'), 'r')
		btn_menu3_qss = btn_menu3_qss_file.read()
		btn_menu3_qss_file.close()
		btn_menu4_qss_file = open(unicode('ui/styles/btn_menu4', 'utf8'), 'r')
		btn_menu4_qss = btn_menu4_qss_file.read()
		btn_menu4_qss_file.close()
		btn_menu5_qss_file = open(unicode('ui/styles/btn_menu5', 'utf8'), 'r')
		btn_menu5_qss = btn_menu5_qss_file.read()
		btn_menu5_qss_file.close()
		btn_menu6_qss_file = open(unicode('ui/styles/btn_menu6', 'utf8'), 'r')
		btn_menu6_qss = btn_menu6_qss_file.read()
		btn_menu6_qss_file.close()
		label_qss_file = open(unicode('ui/styles/label', 'utf8'), 'r')
		label_qss = label_qss_file.read()
		label_qss_file.close()
		label_bg1_qss_file = open(unicode('ui/styles/label_bg1', 'utf8'), 'r')
		label_bg1_qss = label_bg1_qss_file.read()
		label_bg1_qss_file.close()
		label_bg2_qss_file = open(unicode('ui/styles/label_bg2', 'utf8'), 'r')
		label_bg2_qss = label_bg2_qss_file.read()
		label_bg2_qss_file.close()
		lineedit_qss_file = open(unicode('ui/styles/lineedit', 'utf8'), 'r')
		lineedit_qss = lineedit_qss_file.read()
		lineedit_qss_file.close()
		tip_qss_file = open(unicode('ui/styles/tip', 'utf8'), 'r')
		tip_qss = tip_qss_file.read()
		tip_qss_file.close()
		combobox_qss_file = open(unicode('ui/styles/combobox', 'utf8'), 'r')
		combobox_qss = combobox_qss_file.read()
		combobox_qss_file.close()
		check_qss_file = open(unicode('ui/styles/check', 'utf8'), 'r')
		check_qss = check_qss_file.read()
		check_qss_file.close()
		textedit_qss_file = open(unicode('ui/styles/textedit', 'utf8'), 'r')
		textedit_qss = textedit_qss_file.read()
		textedit_qss_file.close()
		vscrollbar_qss_file = open(unicode('ui/styles/vscrollbar', 'utf8'), 'r')
		vscrollbar_qss = vscrollbar_qss_file.read()
		vscrollbar_qss_file.close()
		menu_qss_file = open(unicode('ui/styles/menu', 'utf8'), 'r')
		menu_qss = menu_qss_file.read()
		menu_qss_file.close()
		on_off_qss_file = open(unicode('ui/styles/on_off', 'utf8'), 'r')
		on_off_qss = on_off_qss_file.read()
		on_off_qss_file.close()
		#初始化组件
		self.btn_close = QPushButton()
		self.btn_menu1 = QPushButton()
		self.btn_menu2 = QPushButton()
		self.btn_menu3 = QPushButton()
		self.btn_menu4 = QPushButton()
		self.btn_menu5 = QPushButton()
		self.btn_menu6 = QPushButton()
		self.btn4_1 = QPushButton()
		self.btn_default = QPushButton()
		self.lineedit1_1 = QLineEdit(popserver)
		self.lineedit1_1.setTextMargins(6, 0, 6, 0)
		self.lineedit1_1_a = QLineEdit(popport)
		self.lineedit1_1_a.setTextMargins(6, 0, 6, 0)
		self.lineedit1_2 = QLineEdit(smtpserver)
		self.lineedit1_2.setTextMargins(6, 0, 6, 0)
		self.lineedit1_2_a = QLineEdit(smtpport)
		self.lineedit1_2_a.setTextMargins(6, 0, 6, 0)
		self.lineedit1_3 = QLineEdit(user)
		self.lineedit1_3.setTextMargins(6, 0, 6, 0)
		self.lineedit1_4 = QLineEdit(passwd)
		self.lineedit1_4.setTextMargins(6, 0, 6, 0)
		self.lineedit1_4.setEchoMode(QLineEdit.Password)
		self.lineedit1_5 = QLineEdit(sleep)
		self.lineedit1_5.setTextMargins(6, 0, 6, 0)
		self.lineedit1_5.setValidator(QIntValidator(0, 99999, self))
		self.lineedit1_5.setAlignment(Qt.AlignRight)
		self.lineedit2_1 = QLineEdit(tag_shutdown)
		self.lineedit2_1.setTextMargins(6, 0, 6, 0)
		self.lineedit2_2 = QLineEdit(tag_screen)
		self.lineedit2_2.setTextMargins(6, 0, 6, 0)
		self.lineedit2_3 = QLineEdit(tag_cam)
		self.lineedit2_3.setTextMargins(6, 0, 6, 0)
		self.lineedit2_4 = QLineEdit(tag_button)
		self.lineedit2_4.setTextMargins(6, 0, 6, 0)
		self.lineedit2_5 = QLineEdit(tag_cmd)
		self.lineedit2_5.setTextMargins(6, 0, 6, 0)
		#用setToolTip设置提示
		self.tip1_1 = QLabel()
		self.tip1_1.setToolTip(u'<p>此处内容请参考说明书。</p>')
		self.tip1_1.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip1_1.setStyleSheet(tip_qss)
		self.tip1_1.setParent(self)
		self.tip1_1.setGeometry(530, 118, 14, 14)
		self.tip1_2 = QLabel()
		self.tip1_2.setToolTip(u'<p>此处内容请参考说明书。</p>')
		self.tip1_2.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip1_2.setStyleSheet(tip_qss)
		self.tip1_2.setParent(self)
		self.tip1_2.setGeometry(530, 167, 14, 14)
		self.tip1_3 = QLabel()
		self.tip1_3.setToolTip(u'<p>支持域名邮箱。</p>')
		self.tip1_3.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip1_3.setStyleSheet(tip_qss)
		self.tip1_3.setParent(self)
		self.tip1_3.setGeometry(530, 216, 14, 14)
		self.tip1_4 = QLabel()
		self.tip1_4.setToolTip(u'<p>如开启POP3/SMTP服务的过程中让你启用授权密码，则此处填授权密码，否'
			u'则这里就填邮箱密码</p>')
		self.tip1_4.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip1_4.setStyleSheet(tip_qss)
		self.tip1_4.setParent(self)
		self.tip1_4.setGeometry(530, 265, 14, 14)
		self.tip1_5 = QLabel()
		self.tip1_5.setToolTip(u'<p>可用于远程监视电脑的开机情况，包括开机时间、计算机名、IP以及地理位'
			u'置等信息。</p>')
		self.tip1_5.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip1_5.setStyleSheet(tip_qss)
		self.tip1_5.setParent(self)
		self.tip1_5.setGeometry(385, 335, 14, 14)
		self.tip2_1 = QLabel()
		self.tip2_1.setToolTip(u'<p>将标签作为邮件的标题，将想要执行的快捷键作为邮件的正文。按键间使用“+”'
			u'连接，不区分大小写。</p>')
		self.tip2_1.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip2_1.setStyleSheet(tip_qss)
		self.tip2_1.setParent(self)
		self.tip2_1.setGeometry(582, 318, 14, 14)
		self.tip2_2 = QLabel()
		self.tip2_2.setToolTip(u'<p>将标签作为邮件的标题，将想执行的CMD命令作为邮件的正文。</p>')
		self.tip2_2.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip2_2.setStyleSheet(tip_qss)
		self.tip2_2.setParent(self)
		self.tip2_2.setGeometry(582, 368, 14, 14)
		self.tip3_1 = QLabel()
		self.tip3_1.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip3_1.setStyleSheet(tip_qss)
		self.tip3_1.setParent(self)
		self.tip3_1.setGeometry(312, 115, 14, 14)
		self.tip4_1 = QLabel()
		self.tip4_1.setToolTip(u'<p>用于远程查看摄像头画面的命令。</p>')
		self.tip4_1.setCursor(QCursor(Qt.PointingHandCursor))
		self.tip4_1.setStyleSheet(tip_qss)
		self.tip4_1.setParent(self)
		self.tip4_1.setGeometry(337, 113, 14, 14)
		#设置按钮与链接的鼠标指针为手型
		self.btn_close.setCursor(QCursor(Qt.PointingHandCursor))
		self.btn_menu1.setCursor(QCursor(Qt.PointingHandCursor))
		self.btn_menu2.setCursor(QCursor(Qt.PointingHandCursor))
		self.btn_menu3.setCursor(QCursor(Qt.PointingHandCursor))
		self.btn_menu4.setCursor(QCursor(Qt.PointingHandCursor))
		self.btn_menu5.setCursor(QCursor(Qt.PointingHandCursor))
		self.btn_menu6.setCursor(QCursor(Qt.PointingHandCursor))
		self.btn4_1.setCursor(QCursor(Qt.PointingHandCursor))
		self.btn_default.setCursor(QCursor(Qt.PointingHandCursor))
		#初始化组件
		self.label_title = QLabel()
		self.label_prompt = QLabel()
		self.label_opacity = QLabel()
		self.label1_a = QLabel()	
		self.label1_1 = QLabel()
		self.label1_1_a = QLabel()
		self.label1_2 = QLabel()
		self.label1_2_a = QLabel()
		self.label1_3 = QLabel()
		self.label1_4 = QLabel()
		self.label1_5 = QLabel()
		self.label1_6 = QLabel()
		self.label2_a = QLabel()
		self.label_bg_2_a = QLabel()
		self.label_bg_2_1 = QLabel()
		self.label_bg_2_2 = QLabel()
		self.label_bg_2_3 = QLabel()
		self.label_bg_2_4 = QLabel()
		self.label_bg_2_5 = QLabel()
		self.label2_1 = QLabel()
		self.label2_2 = QLabel()
		self.label2_3 = QLabel()
		self.label2_4 = QLabel()
		self.label2_5 = QLabel()
		self.label2_6 = QLabel()
		self.label2_7 = QLabel()
		self.label3_a = QLabel()
		self.label3_1 = QLabel()
		self.label4_a = QLabel()
		self.label4_1 = QLabel()
		self.label4_2 = QLabel()
		self.label5_a = QLabel()
		self.label5_1 = QLabel()
		self.label5_b = QLabel()
		self.label5_2 = QLabel()
		self.label5_2.setOpenExternalLinks(True)
		self.label6_a = QLabel()
		self.label6_1 = QLabel()
		self.label6_1.setOpenExternalLinks(True)
		self.label6_b = QLabel()
		self.label6_2 = QLabel()
		self.label_menu1 = QLabel()
		self.label_menu2 = QLabel()
		self.label_menu3 = QLabel()
		self.label_menu4 = QLabel()
		self.label_menu5 = QLabel()
		self.label_menu6 = QLabel()
		self.combobox4_1 = QComboBox()
		#检测摄像头
		cam = []
		i = 0
		while 1:
			try:
				cam.append(Device(devnum=i))
				self.combobox4_1.insertItem(i, u'%s'%cam[i].getDisplayName())
			except:
				break
			i += 1
		if i == 0:
			self.combobox4_1.insertItem(0, u'没有检测到摄像头')
			self.btn4_1.setEnabled(False)
		self.combobox4_1.setView(QListView())
		self.on_off = QCheckBox(u'', self)
		self.on_off.setCursor(QCursor(Qt.PointingHandCursor))
		self.on_off.move(580, 431)
		self.check1_1 = QCheckBox(u'开机启动', self)
		self.check1_1.setCursor(QCursor(Qt.PointingHandCursor))
		self.check1_1.move(210, 302)
		self.check1_2 = QCheckBox(u'开机发送邮件通知', self)
		self.check1_2.setCursor(QCursor(Qt.PointingHandCursor))
		self.check1_2.move(240, 332)
		self.textedit = QTextEdit()
		self.textedit.setAcceptRichText(False)
		#设置组件样式
		self.btn_close.setStyleSheet(close_qss)
		self.btn_menu1.setStyleSheet(btn_menu1_qss)
		self.btn_menu2.setStyleSheet(btn_menu2_qss)
		self.btn_menu3.setStyleSheet(btn_menu3_qss)
		self.btn_menu4.setStyleSheet(btn_menu4_qss)
		self.btn_menu5.setStyleSheet(btn_menu5_qss)
		self.btn_menu6.setStyleSheet(btn_menu6_qss)
		self.btn4_1.setStyleSheet(btn2_qss)
		self.btn_default.setStyleSheet(btn1_qss)
		self.label_title.setStyleSheet(label_qss)
		self.label_prompt.setStyleSheet(label_qss)
		opacity = 100
		self.label_opacity.setStyleSheet(u'QLabel{background:rgba(36, 48, 64, ' + str(opacity) + ')}')
		self.label1_a.setStyleSheet(label_qss)
		self.label1_1.setStyleSheet(label_qss)
		self.label1_1_a.setStyleSheet(label_qss)
		self.label1_2.setStyleSheet(label_qss)
		self.label1_2_a.setStyleSheet(label_qss)
		self.label1_3.setStyleSheet(label_qss)
		self.label1_4.setStyleSheet(label_qss)
		self.label1_5.setStyleSheet(label_qss)
		self.label1_6.setStyleSheet(label_qss)
		self.label2_a.setStyleSheet(label_qss)
		self.label_bg_2_a.setStyleSheet(label_bg1_qss)
		self.label_bg_2_1.setStyleSheet(label_bg2_qss)
		self.label_bg_2_2.setStyleSheet(label_bg2_qss)
		self.label_bg_2_3.setStyleSheet(label_bg2_qss)
		self.label_bg_2_4.setStyleSheet(label_bg2_qss)
		self.label_bg_2_5.setStyleSheet(label_bg2_qss)
		self.label2_1.setStyleSheet(label_qss)
		self.label2_2.setStyleSheet(label_qss)
		self.label2_3.setStyleSheet(label_qss)
		self.label2_4.setStyleSheet(label_qss)
		self.label2_5.setStyleSheet(label_qss)
		self.label2_6.setStyleSheet(label_qss)
		self.label2_7.setStyleSheet(label_qss)
		self.label3_a.setStyleSheet(label_qss)
		self.label3_1.setStyleSheet(label_qss)
		self.label4_a.setStyleSheet(label_qss)
		self.label4_1.setStyleSheet(label_qss)
		self.label4_2.setStyleSheet(label_qss)
		self.label5_a.setStyleSheet(label_qss)
		self.label5_1.setStyleSheet(label_qss)
		self.label5_b.setStyleSheet(label_qss)
		self.label5_2.setStyleSheet(label_qss)
		self.label6_a.setStyleSheet(label_qss)
		self.label6_1.setStyleSheet(label_qss)
		self.label6_b.setStyleSheet(label_qss)
		self.label6_2.setStyleSheet(label_qss)
		self.label_menu1.setStyleSheet(label_qss)
		self.label_menu2.setStyleSheet(label_qss)
		self.label_menu3.setStyleSheet(label_qss)
		self.label_menu4.setStyleSheet(label_qss)
		self.label_menu5.setStyleSheet(label_qss)
		self.label_menu6.setStyleSheet(label_qss)
		self.lineedit1_1.setStyleSheet(lineedit_qss)
		self.lineedit1_1_a.setStyleSheet(lineedit_qss)
		self.lineedit1_2.setStyleSheet(lineedit_qss)
		self.lineedit1_2_a.setStyleSheet(lineedit_qss)
		self.lineedit1_3.setStyleSheet(lineedit_qss)
		self.lineedit1_4.setStyleSheet(lineedit_qss)
		self.lineedit1_5.setStyleSheet(lineedit_qss)
		self.lineedit2_1.setStyleSheet(lineedit_qss)
		self.lineedit2_2.setStyleSheet(lineedit_qss)
		self.lineedit2_3.setStyleSheet(lineedit_qss)
		self.lineedit2_4.setStyleSheet(lineedit_qss)
		self.lineedit2_5.setStyleSheet(lineedit_qss)
		self.on_off.setStyleSheet(on_off_qss)
		self.check1_1.setStyleSheet(check_qss)
		self.check1_2.setStyleSheet(check_qss)
		self.combobox4_1.setStyleSheet(combobox_qss)
		self.textedit.setStyleSheet(textedit_qss)
		self.textedit.verticalScrollBar().setStyleSheet(vscrollbar_qss)
		#设置组件继承关系
		self.btn_close.setParent(self)
		self.btn4_1.setParent(self)
		self.btn_default.setParent(self)
		self.label_title.setParent(self)
		self.label_prompt.setParent(self)
		self.label_opacity.setParent(self)
		self.label1_a.setParent(self)
		self.label1_1.setParent(self)
		self.label1_1_a.setParent(self)
		self.label1_2.setParent(self)
		self.label1_2_a.setParent(self)
		self.label1_3.setParent(self)
		self.label1_4.setParent(self)
		self.label1_5.setParent(self)
		self.label1_6.setParent(self)
		self.label2_a.setParent(self)
		self.label_bg_2_a.setParent(self)
		self.label_bg_2_1.setParent(self)
		self.label_bg_2_2.setParent(self)
		self.label_bg_2_3.setParent(self)
		self.label_bg_2_4.setParent(self)
		self.label_bg_2_5.setParent(self)
		self.label2_1.setParent(self)
		self.label2_2.setParent(self)
		self.label2_3.setParent(self)
		self.label2_4.setParent(self)
		self.label2_5.setParent(self)
		self.label2_6.setParent(self)
		self.label2_7.setParent(self)
		self.label3_a.setParent(self)
		self.label3_1.setParent(self)
		self.label4_a.setParent(self)
		self.label4_1.setParent(self)
		self.label4_2.setParent(self)
		self.label5_a.setParent(self)
		self.label5_1.setParent(self)
		self.label5_b.setParent(self)
		self.label5_2.setParent(self)
		self.label6_a.setParent(self)
		self.label6_1.setParent(self)
		self.label6_b.setParent(self)
		self.label6_2.setParent(self)
		self.label_menu1.setParent(self)
		self.label_menu2.setParent(self)
		self.label_menu3.setParent(self)
		self.label_menu4.setParent(self)
		self.label_menu5.setParent(self)
		self.label_menu6.setParent(self)
		self.btn_menu1.setParent(self)
		self.btn_menu2.setParent(self)
		self.btn_menu3.setParent(self)
		self.btn_menu4.setParent(self)
		self.btn_menu5.setParent(self)
		self.btn_menu6.setParent(self)
		self.lineedit1_1.setParent(self)
		self.lineedit1_1_a.setParent(self)
		self.lineedit1_2.setParent(self)
		self.lineedit1_2_a.setParent(self)
		self.lineedit1_3.setParent(self)
		self.lineedit1_4.setParent(self)
		self.lineedit1_5.setParent(self)
		self.lineedit2_1.setParent(self)
		self.lineedit2_2.setParent(self)
		self.lineedit2_3.setParent(self)
		self.lineedit2_4.setParent(self)
		self.lineedit2_5.setParent(self)
		self.on_off.setParent(self)
		self.check1_1.setParent(self)
		self.check1_2.setParent(self)
		self.combobox4_1.setParent(self)
		self.textedit.setParent(self)
		#设置组件位置和尺寸
		self.btn_close.setGeometry(636, 5, 19, 19)
		self.btn4_1.setGeometry(210, 370, 104, 34)
		self.btn_default.setGeometry(166, 430, 91, 34)
		self.label_title.setGeometry(18, 18, 150, 21)
		self.label_prompt.setGeometry(370, 437, 200, 20)
		self.label_opacity.setGeometry(370, 437, 200, 20)
		self.label1_a.setGeometry(190, 70, 100, 20)		
		self.label1_1.setGeometry(200, 115, 90, 20)
		self.label1_1_a.setGeometry(440, 115, 25, 20)
		self.label1_2.setGeometry(200, 164, 90, 20)
		self.label1_2_a.setGeometry(440, 164, 25, 20)
		self.label1_3.setGeometry(200, 213, 90, 20)
		self.label1_4.setGeometry(200, 262, 90, 20)
		self.label1_5.setGeometry(210, 370, 200, 20)
		self.label1_6.setGeometry(422, 370, 100, 20)
		self.label2_a.setGeometry(190, 70, 100, 20)
		self.label_bg_2_a.setGeometry(210, 110, 360, 40)
		self.label_bg_2_1.setGeometry(210, 150, 360, 50)
		self.label_bg_2_2.setGeometry(210, 200, 360, 50)
		self.label_bg_2_3.setGeometry(210, 250, 360, 50)
		self.label_bg_2_4.setGeometry(210, 300, 360, 50)
		self.label_bg_2_5.setGeometry(210, 350, 360, 50)
		self.label2_1.setGeometry(235, 120, 130, 20)
		self.label2_2.setGeometry(415, 120, 130, 20)
		self.label2_3.setGeometry(235, 165, 130, 20)
		self.label2_4.setGeometry(235, 215, 130, 20)
		self.label2_5.setGeometry(235, 265, 130, 20)
		self.label2_6.setGeometry(235, 315, 130, 20)
		self.label2_7.setGeometry(235, 365, 130, 20)
		self.label3_a.setGeometry(190, 70, 100, 20)
		self.label3_1.setGeometry(210, 112, 100, 20)
		self.label4_a.setGeometry(190, 70, 100, 20)
		self.label4_1.setGeometry(210, 110, 120, 20)
		self.label4_2.setGeometry(210, 180, 240, 180)
		self.label5_a.setGeometry(190, 70, 100, 20)
		self.label5_1.setGeometry(210, 110, 400, 120)
		self.label5_b.setGeometry(190, 250, 100, 20)
		self.label5_2.setGeometry(210, 290, 400, 80)
		self.label6_a.setGeometry(190, 70, 100, 20)
		self.label6_1.setGeometry(210, 110, 400, 90)
		self.label6_b.setGeometry(190, 220, 100, 20)
		self.label6_2.setGeometry(210, 260, 400, 120)
		self.label_menu1.setGeometry(50, 60, 158, 40)
		self.label_menu2.setGeometry(50, 100, 158, 40)
		self.label_menu3.setGeometry(50, 140, 158, 40)
		self.label_menu4.setGeometry(50, 180, 158, 40)
		self.label_menu5.setGeometry(50, 220, 158, 40)
		self.label_menu6.setGeometry(50, 260, 158, 40)
		self.btn_menu1.setGeometry(2, 60, 158, 40)
		self.btn_menu2.setGeometry(2, 100, 158, 40)
		self.btn_menu3.setGeometry(2, 140, 158, 40)
		self.btn_menu4.setGeometry(2, 180, 158, 40)
		self.btn_menu5.setGeometry(2, 220, 158, 40)
		self.btn_menu6.setGeometry(2, 260, 158, 40)
		self.lineedit1_1.setGeometry(300, 108, 130, 34)
		self.lineedit1_1_a.setGeometry(475, 108, 45, 34)
		self.lineedit1_2.setGeometry(300, 157, 130, 34)
		self.lineedit1_2_a.setGeometry(475, 157, 45, 34)
		self.lineedit1_3.setGeometry(300, 206, 220, 34)
		self.lineedit1_4.setGeometry(300, 255, 220, 34)
		self.lineedit1_5.setGeometry(312, 363, 100, 34)
		self.lineedit2_1.setGeometry(415, 158, 130, 34)
		self.lineedit2_2.setGeometry(415, 208, 130, 34)
		self.lineedit2_3.setGeometry(415, 258, 130, 34)
		self.lineedit2_4.setGeometry(415, 308, 130, 34)
		self.lineedit2_5.setGeometry(415, 358, 130, 34)
		self.combobox4_1.setGeometry(210, 135, 190, 34)
		self.textedit.setGeometry(210, 138, 300, 200)
		self.label_title.setText(u'<p style="font:16px;color:#FFF"><img src="ui/images/icon_on.png">'
			u'&nbsp;&nbsp;Email My PC</p>')
		self.label_menu1.setText(u'<p style="color:#FFF">基本设置</p>')
		self.label_menu2.setText(u'<p>命令标签</p>')
		self.label_menu3.setText(u'<p>邮件过滤</p>')
		self.label_menu4.setText(u'<p>摄像头</p>')
		self.label_menu5.setText(u'<p>说明书</p>')
		self.label_menu6.setText(u'<p>关于</p>')
		self.label1_a.setText(u'<p style="font:17px;color:#E9E9E9">基本设置</p>')
		self.label1_1.setText(u'<p align=right>POP3服务器</p>')
		self.label1_1_a.setText(u'<p>端口</p>')
		self.label1_2.setText(u'<p align=right>SMTP服务器</p>')
		self.label1_2_a.setText(u'<p>端口</p>')
		self.label1_3.setText(u'<p align=right>邮箱地址</p>')
		self.label1_4.setText(u'<p align=right>授权密码</p>')
		self.label1_5.setText(u'<p>新邮件检测频率</p>')
		self.label1_6.setText(u'<p>秒/次</p>')
		self.label2_a.setText(u'<p style="font:17px;color:#E9E9E9">命令标签</p>')
		self.label2_1.setText(u'<p align=center>功能</p>')
		self.label2_2.setText(u'<p align=center>标签</p>')
		self.label2_3.setText(u'<p>关机</p>')
		self.label2_4.setText(u'<p>回传屏幕截图</p>')
		self.label2_5.setText(u'<p>回传摄像头画面</p>')
		self.label2_6.setText(u'<p>执行快捷键操作</p>')
		self.label2_7.setText(u'<p>执行CMD命令</p>')
		self.label3_a.setText(u'<p style="font:17px;color:#E9E9E9">邮件过滤</p>')
		self.label3_1.setText(u'<p style="color:#5E6268">邮件过滤白名单</p>')
		self.tip3_1.setToolTip(u'<p>白名单的格式是每行一个邮箱，程序仅会执行白名单中的邮箱发来的'
			u'命令。</p>')
		self.textedit.setText(whitelist)
		self.label4_a.setText(u'<p style="font:17px;color:#E9E9E9">摄像头</p>')
		self.label4_1.setText(u'<p>请选择使用的摄像头</p>')
		self.label4_2.setPixmap(QPixmap("ui/images/camera.png"))
		self.btn4_1.setText(u'打开预览画面')
		self.label5_a.setText(u'<p style="font:17px;color:#E9E9E9">功能简介</p>')
		self.label5_1.setText(u'<p>1. 远程监视开机情况<br>2. 遥控电脑关机<br>3. 远程监视屏幕<br>'
			u'4. 远程监视摄像头<br>5. 远程快捷键操作<br>6. 远程执行CMD命令</p>')
		self.label5_b.setText(u'<p style="font:17px;color:#E9E9E9">使用方法</p>')
		self.label5_2.setText(u'<p>首先你需要为你的邮箱开启STMP和POP3服务。<br>'
			u'<a style="text-decoration:none;color:#00AEFF" '
			u'href="http://service.mail.qq.com/cgi-bin/help?subtype=1&&id=28&&no=166">'
			u'QQ邮箱开启方法&nbsp;<img src="ui/images/link.png"></a>'
			u'<a style = "text-decoration:none;color:#00AEFF" '
			u'href="http://help.163.com/10/0312/13/61J0LI3200752CLQ.html">&nbsp;&nbsp;&nbsp;'
			u'163邮箱开启方法&nbsp;<img src="ui/images/link.png"></a><br>'
			u'<a style="text-decoration:none;color:#00AEFF" '
			u'href="http://kf.qq.com/faq/120322fu63YV130422nqIrqu.html">'
			u'QQ邮箱端口号&nbsp;<img src="ui/images/link.png"></a>'
			u'<a style="text-decoration:none;color:#00AEFF" '
			u'href="http://help.163.com/09/1223/14/5R7P3QI100753VB8.html">&nbsp;&nbsp;&nbsp;'
			u'163邮箱端口号&nbsp;<img src="ui/images/link.png"></a>'
			u'<br>使用时只需要将对应命令的标签作为邮件的标题给自己发邮件即可。<br></p>')
		self.label6_a.setText(u'<p style="font:17px;color:#E9E9E9">关于</p>')
		self.label6_1.setText(u'<p>当前版本：%s</p><p>官方网站：<a style="text-decoration:none;'
			u'color:#00AEFF" href="http://jackeriss.com/emp.htm">www.Jackeriss.com/emp.htm '
			u'<img src="ui/images/link.png"></a></p><p>软件作者：<a style="text-decoration:none;'
			u'color:#00AEFF" href="http://jackeriss.com">&copy;Jackeriss '
			u'<img src="ui/images/link.png"></a></p>'%version)
		self.label6_b.setText(u'<p style="font:17px;color:#E9E9E9">用户协议</p>')
		self.label6_2.setText(u'<p>1. 本软件全称“Email My PC”，以下简称“本软件”。<br>'
			u'2. 您必须阅读并同意此协议才能够使用本软件。<br>3. 严禁利用本软件进行任何侵犯他人合法权益'
			u'的活动。<br>4. 本软件仅用于学习交流，使用过程中出现任何问题都与原作者无关。<br>5. 本软件'
			u'的著作权归&copy;Jackeriss所有，作者保留所有权利。<br>6. 作者保留对本协议的最终解释权，并'
			u'有权随时对本协议进行修改。</p>')
		self.btn_default.setText(u'重设为默认')	
		#绑定触发事件	
		self.btn_close.clicked.connect(self.close_clicked)
		self.btn_menu1.pressed.connect(self.menu1_pressed)
		self.btn_menu2.pressed.connect(self.menu2_pressed)
		self.btn_menu3.pressed.connect(self.menu3_pressed)
		self.btn_menu4.pressed.connect(self.menu4_pressed)
		self.btn_menu5.pressed.connect(self.menu5_pressed)
		self.btn_menu6.pressed.connect(self.menu6_pressed)
		self.lineedit1_1.editingFinished.connect(self.lineedit1_1_edited)
		self.lineedit1_1_a.editingFinished.connect(self.lineedit1_1_a_edited)
		self.lineedit1_2.editingFinished.connect(self.lineedit1_2_edited)
		self.lineedit1_2_a.editingFinished.connect(self.lineedit1_2_a_edited)
		self.lineedit1_3.editingFinished.connect(self.lineedit1_3_edited)
		self.lineedit1_4.editingFinished.connect(self.lineedit1_4_edited)
		self.lineedit1_5.editingFinished.connect(self.lineedit1_5_edited)
		self.lineedit2_1.editingFinished.connect(self.lineedit2_1_edited)
		self.lineedit2_2.editingFinished.connect(self.lineedit2_2_edited)
		self.lineedit2_3.editingFinished.connect(self.lineedit2_3_edited)
		self.lineedit2_4.editingFinished.connect(self.lineedit2_4_edited)
		self.lineedit2_5.editingFinished.connect(self.lineedit2_5_edited)
		self.btn4_1.clicked.connect(self.btn4_1_clicked)
		self.btn_default.clicked.connect(self.btn_default_clicked)
		self.on_off.clicked.connect(self.alter)
		self.check1_1.clicked.connect(self.check_change1_1)
		self.check1_2.clicked.connect(self.check_change1_2)
		self.combobox4_1.currentIndexChanged.connect(self.combobox_change4_1)
		self.textedit.textChanged.connect(self.textedit_changed)
		self.cam_thread = Cam()
		self.cam_thread.trigger.connect(self.camera)
		self.reconnect_thread = Reconnect()
		self.reconnect_thread.trigger.connect(self.start_server)
		self.server_thread = Server()
		self.server_thread.trigger1.connect(self.server_trigger1)
		self.server_thread.trigger2.connect(self.server_trigger2)
		self.server_thread.trigger3.connect(self.server_trigger3)
		self.server_thread.trigger4.connect(self.server_trigger4)
		self.server_thread.trigger5.connect(self.server_trigger5)
		self.server_thread.trigger6.connect(self.server_trigger6)
		self.in_thread = In()
		self.in_thread.trigger.connect(self.trans)
		self.trans_thread = Trans()
		self.trans_thread.trigger.connect(self.trans)
		self.check1_1.setChecked(bool(int(autostart)))
		self.check1_2.setChecked(bool(int(startsend)))
		if self.check1_1.isChecked() == False:
			self.check1_2.setEnabled(False)
		if cam_no > i:
			cam_no = 0
			config.set("settings", "cam_no", cam_no)
		self.combobox4_1.setCurrentIndex(cam_no)
		self.label2_a.hide()
		self.label_bg_2_a.hide()
		self.label_bg_2_1.hide()
		self.label_bg_2_2.hide()
		self.label_bg_2_3.hide()
		self.label_bg_2_4.hide()
		self.label_bg_2_5.hide()
		self.label2_1.hide()
		self.label2_2.hide()
		self.label2_3.hide()
		self.label2_4.hide()
		self.label2_5.hide()
		self.label2_6.hide()
		self.label2_7.hide()
		self.lineedit2_1.hide()
		self.lineedit2_2.hide()
		self.lineedit2_3.hide()
		self.lineedit2_4.hide()
		self.lineedit2_5.hide()
		self.tip2_1.hide()
		self.tip2_2.hide()
		self.label3_a.hide()
		self.label3_1.hide()
		self.tip3_1.hide()
		self.textedit.hide()
		self.label4_a.hide()
		self.label4_1.hide()
		self.label4_2.hide()
		self.combobox4_1.hide()
		self.btn4_1.hide()
		self.tip4_1.hide()
		self.label5_a.hide()
		self.label5_1.hide()
		self.label5_b.hide()
		self.label5_2.hide()
		self.label6_a.hide()
		self.label6_1.hide()
		self.label6_b.hide()
		self.label6_2.hide()
		#任务栏通知中心菜单设置
		self.alterAction = QAction(u'开启服务', self, triggered = self.alter)
		self.boardAction = QAction(u'显示主面板', self, triggered = self.board)
		self.exitAction = QAction(u'退出', self, triggered = self.exit)
		self.trayIcon = QSystemTrayIcon()
		self.trayIconMenu = QMenu(self)
		self.trayIconMenu.setStyleSheet(menu_qss)
		self.trayIconMenu.addAction(self.alterAction)
		self.trayIconMenu.addAction(self.boardAction)
		self.trayIconMenu.addAction(self.exitAction)
		self.trayIcon.setContextMenu(self.trayIconMenu)
		self.trayIcon.activated.connect(self.trayClick)
		self.setWindowTitle(u'Email My PC')
		self.logo = QIcon('ui/images/logo.png')
		self.icon_on = QIcon('ui/images/icon_on.png')
		self.icon_off = QIcon('ui/images/icon_off.png')
		self.server_thread.start()
		self.start_server()
		self.setWindowIcon(self.logo)
		self.trayIcon.show()
		self.setWindowFlags(Qt.FramelessWindowHint)
		self.resize(664, 472)
		screen = QDesktopWidget().screenGeometry()
		size = self.geometry()
		self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)

	#点击关闭按钮时关闭窗口但不退出
	def closeEvent(self, event):
		self.hide()
		event.ignore()

	#绘制窗口
	def paintEvent(self, event):
		global ui_path
		path = QPainterPath()
		painter = QPainter(self)
		painter.setRenderHint(QPainter.Antialiasing, True)
		path.addRoundRect(0, 0, self.width(), self.height(), 0)
		painter.fillPath(path, QBrush(QPixmap('ui/images/background.png')))

	#鼠标按下事件
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton:
			self.dragPosition = event.globalPos()-self.frameGeometry().topLeft()
			event.accept()

	#鼠标移动事件
	def mouseMoveEvent(self, event):
		if event.buttons() & Qt.LeftButton:
			if self.dragPosition != None:
				if self.dragPosition.y() < 50:
					self.move(event.globalPos() - self.dragPosition)  
					event.accept()

	#鼠标弹起事件
	def mouseReleaseEvent(self, event):
		self.dragPosition = QPoint(0, 100)
		event.accept()

	#点击关闭按钮时关闭窗口但不退出
	def close_clicked(self):
		self.hide()

	#点击第一个导航时触发
	def menu1_pressed(self):
		global current_page
		current_page = 1
		self.label_menu1.setText(u'<p style="color:#FFF">基本设置</p>')
		self.label_menu2.setText(u'<p>命令标签</p>')
		self.label_menu3.setText(u'<p>邮件过滤</p>')
		self.label_menu4.setText(u'<p>摄像头</p>')
		self.label_menu5.setText(u'<p>说明书</p>')
		self.label_menu6.setText(u'<p>关于</p>')
		self.label1_a.show()
		self.label1_1.show()
		self.label1_1_a.show()
		self.label1_2.show()
		self.label1_2_a.show()
		self.label1_3.show()
		self.label1_4.show()
		self.label1_5.show()
		self.label1_6.show()
		self.lineedit1_1.show()
		self.lineedit1_1_a.show()
		self.lineedit1_2.show()
		self.lineedit1_2_a.show()
		self.lineedit1_3.show()
		self.lineedit1_4.show()
		self.lineedit1_5.show()
		self.tip1_1.show()
		self.tip1_2.show()
		self.tip1_3.show()
		self.tip1_4.show()
		self.tip1_5.show()
		self.check1_1.show()
		self.check1_2.show()
		self.label2_a.hide()
		self.label_bg_2_a.hide()
		self.label_bg_2_1.hide()
		self.label_bg_2_2.hide()
		self.label_bg_2_3.hide()
		self.label_bg_2_4.hide()
		self.label_bg_2_5.hide()
		self.label2_1.hide()
		self.label2_2.hide()
		self.label2_3.hide()
		self.label2_4.hide()
		self.label2_5.hide()
		self.label2_6.hide()
		self.label2_7.hide()
		self.lineedit2_1.hide()
		self.lineedit2_2.hide()
		self.lineedit2_3.hide()
		self.lineedit2_4.hide()
		self.lineedit2_5.hide()
		self.tip2_1.hide()
		self.tip2_2.hide()
		self.label3_a.hide()
		self.label3_1.hide()
		self.tip3_1.hide()
		self.textedit.hide()
		self.label4_a.hide()
		self.label4_1.hide()
		self.label4_2.hide()
		self.combobox4_1.hide()
		self.btn4_1.hide()
		self.tip4_1.hide()
		self.label5_a.hide()
		self.label5_1.hide()
		self.label5_b.hide()
		self.label5_2.hide()
		self.label6_a.hide()
		self.label6_1.hide()
		self.label6_b.hide()
		self.label6_2.hide()
		self.btn_default.show()

	#点击第二个导航时触发
	def menu2_pressed(self):
		global current_page
		current_page = 2
		self.label_menu1.setText(u'<p>基本设置</p>')
		self.label_menu2.setText(u'<p style="color:#FFF">命令标签</p>')
		self.label_menu3.setText(u'<p>邮件过滤</p>')
		self.label_menu4.setText(u'<p>摄像头</p>')
		self.label_menu5.setText(u'<p>说明书</p>')
		self.label_menu6.setText(u'<p>关于</p>')
		self.label1_a.hide()
		self.label1_1.hide()
		self.label1_1_a.hide()
		self.label1_2.hide()
		self.label1_2_a.hide()
		self.label1_3.hide()
		self.label1_4.hide()
		self.label1_5.hide()
		self.label1_6.hide()
		self.lineedit1_1.hide()
		self.lineedit1_1_a.hide()
		self.lineedit1_2.hide()
		self.lineedit1_2_a.hide()
		self.lineedit1_3.hide()
		self.lineedit1_4.hide()
		self.lineedit1_5.hide()
		self.tip1_1.hide()
		self.tip1_2.hide()
		self.tip1_3.hide()
		self.tip1_4.hide()
		self.tip1_5.hide()
		self.check1_1.hide()
		self.check1_2.hide()
		self.label2_a.show()
		self.label_bg_2_a.show()
		self.label_bg_2_1.show()
		self.label_bg_2_2.show()
		self.label_bg_2_3.show()
		self.label_bg_2_4.show()
		self.label_bg_2_5.show()
		self.label2_1.show()
		self.label2_2.show()
		self.label2_3.show()
		self.label2_4.show()
		self.label2_5.show()
		self.label2_6.show()
		self.label2_7.show()
		self.lineedit2_1.show()
		self.lineedit2_2.show()
		self.lineedit2_3.show()
		self.lineedit2_4.show()
		self.lineedit2_5.show()
		self.tip2_1.show()
		self.tip2_2.show()
		self.label3_a.hide()
		self.label3_1.hide()
		self.tip3_1.hide()
		self.textedit.hide()
		self.label4_a.hide()
		self.label4_1.hide()
		self.label4_2.hide()
		self.combobox4_1.hide()
		self.btn4_1.hide()
		self.tip4_1.hide()
		self.label5_a.hide()
		self.label5_1.hide()
		self.label5_b.hide()
		self.label5_2.hide()
		self.label6_a.hide()
		self.label6_1.hide()
		self.label6_b.hide()
		self.label6_2.hide()
		self.btn_default.show()

	#点击第三个导航时触发
	def menu3_pressed(self):
		global current_page
		current_page = 3
		self.label_menu1.setText(u'<p>基本设置</p>')
		self.label_menu2.setText(u'<p>命令标签</p>')
		self.label_menu3.setText(u'<p style="color:#FFF">邮件过滤</p>')
		self.label_menu4.setText(u'<p>摄像头</p>')
		self.label_menu5.setText(u'<p>说明书</p>')
		self.label_menu6.setText(u'<p>关于</p>')
		self.label1_a.hide()
		self.label1_1.hide()
		self.label1_1_a.hide()
		self.label1_2.hide()
		self.label1_2_a.hide()
		self.label1_3.hide()
		self.label1_4.hide()
		self.label1_5.hide()
		self.label1_6.hide()
		self.lineedit1_1.hide()
		self.lineedit1_1_a.hide()
		self.lineedit1_2.hide()
		self.lineedit1_2_a.hide()
		self.lineedit1_3.hide()
		self.lineedit1_4.hide()
		self.lineedit1_5.hide()
		self.tip1_1.hide()
		self.tip1_2.hide()
		self.tip1_3.hide()
		self.tip1_4.hide()
		self.tip1_5.hide()
		self.check1_1.hide()
		self.check1_2.hide()
		self.label2_a.hide()
		self.label_bg_2_a.hide()
		self.label_bg_2_1.hide()
		self.label_bg_2_2.hide()
		self.label_bg_2_3.hide()
		self.label_bg_2_4.hide()
		self.label_bg_2_5.hide()
		self.label2_1.hide()
		self.label2_2.hide()
		self.label2_3.hide()
		self.label2_4.hide()
		self.label2_5.hide()
		self.label2_6.hide()
		self.label2_7.hide()
		self.lineedit2_1.hide()
		self.lineedit2_2.hide()
		self.lineedit2_3.hide()
		self.lineedit2_4.hide()
		self.lineedit2_5.hide()
		self.tip2_1.hide()
		self.tip2_2.hide()
		self.label3_a.show()
		self.label3_1.show()
		self.tip3_1.show()
		self.textedit.show()
		self.label4_a.hide()
		self.label4_1.hide()
		self.label4_2.hide()
		self.combobox4_1.hide()
		self.btn4_1.hide()
		self.tip4_1.hide()
		self.label5_a.hide()
		self.label5_1.hide()
		self.label5_b.hide()
		self.label5_2.hide()
		self.label6_a.hide()
		self.label6_1.hide()
		self.label6_b.hide()
		self.label6_2.hide()
		self.btn_default.show()

	#点击第四个导航时触发
	def menu4_pressed(self):
		global current_page
		current_page = 4
		self.label_menu1.setText(u'<p>基本设置</p>')
		self.label_menu2.setText(u'<p>命令标签</p>')
		self.label_menu3.setText(u'<p>邮件过滤</p>')
		self.label_menu4.setText(u'<p style="color:#FFF">摄像头</p>')
		self.label_menu5.setText(u'<p>说明书</p>')
		self.label_menu6.setText(u'<p>关于</p>')
		self.label1_a.hide()
		self.label1_1.hide()
		self.label1_1_a.hide()
		self.label1_2.hide()
		self.label1_2_a.hide()
		self.label1_3.hide()
		self.label1_4.hide()
		self.label1_5.hide()
		self.label1_6.hide()
		self.lineedit1_1.hide()
		self.lineedit1_1_a.hide()
		self.lineedit1_2.hide()
		self.lineedit1_2_a.hide()
		self.lineedit1_3.hide()
		self.lineedit1_4.hide()
		self.lineedit1_5.hide()
		self.tip1_1.hide()
		self.tip1_2.hide()
		self.tip1_3.hide()
		self.tip1_4.hide()
		self.tip1_5.hide()
		self.check1_1.hide()
		self.check1_2.hide()
		self.label2_a.hide()
		self.label_bg_2_a.hide()
		self.label_bg_2_1.hide()
		self.label_bg_2_2.hide()
		self.label_bg_2_3.hide()
		self.label_bg_2_4.hide()
		self.label_bg_2_5.hide()
		self.label2_1.hide()
		self.label2_2.hide()
		self.label2_3.hide()
		self.label2_4.hide()
		self.label2_5.hide()
		self.label2_6.hide()
		self.label2_7.hide()
		self.lineedit2_1.hide()
		self.lineedit2_2.hide()
		self.lineedit2_3.hide()
		self.lineedit2_4.hide()
		self.lineedit2_5.hide()
		self.tip2_1.hide()
		self.tip2_2.hide()
		self.label3_a.hide()
		self.label3_1.hide()
		self.tip3_1.hide()
		self.textedit.hide()
		self.label4_a.show()
		self.label4_1.show()
		self.label4_2.show()
		self.combobox4_1.show()
		self.btn4_1.show()
		self.tip4_1.show()
		self.label5_a.hide()
		self.label5_1.hide()
		self.label5_b.hide()
		self.label5_2.hide()
		self.label6_a.hide()
		self.label6_1.hide()
		self.label6_b.hide()
		self.label6_2.hide()
		self.btn_default.show()

	#点击第五个导航时触发
	def menu5_pressed(self):
		global current_page
		current_page = 5
		self.label_menu1.setText(u'<p>基本设置</p>')
		self.label_menu2.setText(u'<p>命令标签</p>')
		self.label_menu3.setText(u'<p>邮件过滤</p>')
		self.label_menu4.setText(u'<p>摄像头</p>')
		self.label_menu5.setText(u'<p style="color:#FFF">说明书</p>')
		self.label_menu6.setText(u'<p>关于</p>')
		self.label1_a.hide()
		self.label1_1.hide()
		self.label1_1_a.hide()
		self.label1_2.hide()
		self.label1_2_a.hide()
		self.label1_3.hide()
		self.label1_4.hide()
		self.label1_5.hide()
		self.label1_6.hide()
		self.lineedit1_1.hide()
		self.lineedit1_1_a.hide()
		self.lineedit1_2.hide()
		self.lineedit1_2_a.hide()
		self.lineedit1_3.hide()
		self.lineedit1_4.hide()
		self.lineedit1_5.hide()
		self.tip1_1.hide()
		self.tip1_2.hide()
		self.tip1_3.hide()
		self.tip1_4.hide()
		self.tip1_5.hide()
		self.check1_1.hide()
		self.check1_2.hide()
		self.label2_a.hide()
		self.label_bg_2_a.hide()
		self.label_bg_2_1.hide()
		self.label_bg_2_2.hide()
		self.label_bg_2_3.hide()
		self.label_bg_2_4.hide()
		self.label_bg_2_5.hide()
		self.label2_1.hide()
		self.label2_2.hide()
		self.label2_3.hide()
		self.label2_4.hide()
		self.label2_5.hide()
		self.label2_6.hide()
		self.label2_7.hide()
		self.lineedit2_1.hide()
		self.lineedit2_2.hide()
		self.lineedit2_3.hide()
		self.lineedit2_4.hide()
		self.lineedit2_5.hide()
		self.tip2_1.hide()
		self.tip2_2.hide()
		self.label3_a.hide()
		self.label3_1.hide()
		self.tip3_1.hide()
		self.textedit.hide()
		self.label4_a.hide()
		self.label4_1.hide()
		self.label4_2.hide()
		self.combobox4_1.hide()
		self.btn4_1.hide()
		self.tip4_1.hide()
		self.label5_a.show()
		self.label5_1.show()
		self.label5_b.show()
		self.label5_2.show()
		self.label6_a.hide()
		self.label6_1.hide()
		self.label6_b.hide()
		self.label6_2.hide()
		self.btn_default.hide()

	#点击第六个导航时触发
	def menu6_pressed(self):
		global current_page
		current_page = 6
		self.label_menu1.setText(u'<p>基本设置</p>')
		self.label_menu2.setText(u'<p>命令标签</p>')
		self.label_menu3.setText(u'<p>邮件过滤</p>')
		self.label_menu4.setText(u'<p>摄像头</p>')
		self.label_menu5.setText(u'<p>说明书</p>')
		self.label_menu6.setText(u'<p style="color:#FFF">关于</p>')
		self.label1_a.hide()
		self.label1_1.hide()
		self.label1_1_a.hide()
		self.label1_2.hide()
		self.label1_2_a.hide()
		self.label1_3.hide()
		self.label1_4.hide()
		self.label1_5.hide()
		self.label1_6.hide()
		self.lineedit1_1.hide()
		self.lineedit1_1_a.hide()
		self.lineedit1_2.hide()
		self.lineedit1_2_a.hide()
		self.lineedit1_3.hide()
		self.lineedit1_4.hide()
		self.lineedit1_5.hide()
		self.tip1_1.hide()
		self.tip1_2.hide()
		self.tip1_3.hide()
		self.tip1_4.hide()
		self.tip1_5.hide()
		self.check1_1.hide()
		self.check1_2.hide()
		self.label2_a.hide()
		self.label_bg_2_a.hide()
		self.label_bg_2_1.hide()
		self.label_bg_2_2.hide()
		self.label_bg_2_3.hide()
		self.label_bg_2_4.hide()
		self.label_bg_2_5.hide()
		self.label2_1.hide()
		self.label2_2.hide()
		self.label2_3.hide()
		self.label2_4.hide()
		self.label2_5.hide()
		self.label2_6.hide()
		self.label2_7.hide()
		self.lineedit2_1.hide()
		self.lineedit2_2.hide()
		self.lineedit2_3.hide()
		self.lineedit2_4.hide()
		self.lineedit2_5.hide()
		self.tip2_1.hide()
		self.tip2_2.hide()
		self.label3_a.hide()
		self.label3_1.hide()
		self.tip3_1.hide()
		self.textedit.hide()
		self.label4_a.hide()
		self.label4_1.hide()
		self.label4_2.hide()
		self.combobox4_1.hide()
		self.btn4_1.hide()
		self.tip4_1.hide()
		self.label5_a.hide()
		self.label5_1.hide()
		self.label5_b.hide()
		self.label5_2.hide()
		self.label6_a.show()
		self.label6_1.show()
		self.label6_b.show()
		self.label6_2.show()
		self.btn_default.hide()

	#各个QLineedit组件被编辑后触发
	def lineedit1_1_edited(self):
		global popserver
		if popserver != str(unicode(self.lineedit1_1.text(), 'utf-8', 'ignore')):
			popserver = str(unicode(self.lineedit1_1.text(), 'utf-8', 'ignore'))
			config.set('mail', 'popserver', popserver)
			self.save()

	def lineedit1_1_a_edited(self):
		global popport
		if popport != str(unicode(self.lineedit1_1_a.text(), 'utf-8', 'ignore')):
			popport = str(unicode(self.lineedit1_1_a.text(), 'utf-8', 'ignore'))
			config.set('mail', 'popport', popport)
			self.save()

	def lineedit1_2_edited(self):
		global smtpserver
		if smtpserver != str(unicode(self.lineedit1_2.text(), 'utf-8', 'ignore')):
			smtpserver = str(unicode(self.lineedit1_2.text(), 'utf-8', 'ignore'))
			config.set('mail', 'smtpserver', smtpserver)
			self.save()

	def lineedit1_2_a_edited(self):
		global smtpport
		if smtpport != str(unicode(self.lineedit1_2_a.text(), 'utf-8', 'ignore')):
			smtpport = str(unicode(self.lineedit1_2_a.text(), 'utf-8', 'ignore'))
			config.set('mail', 'smtpport', smtpport)
			self.save()

	def lineedit1_3_edited(self):
		global user, whitelist
		if user != str(unicode(self.lineedit1_3.text(), 'utf-8', 'ignore')):
			user = str(unicode(self.lineedit1_3.text(), 'utf-8', 'ignore'))
			config.set('mail', 'user', user)
			if whitelist == '':
				self.textedit.setText(user)
				whitelist = user
				config.set('settings', 'whitelist', whitelist)
			self.save()

	def lineedit1_4_edited(self):
		global passwd
		if passwd != str(unicode(self.lineedit1_4.text(), 'utf-8', 'ignore')):
			passwd = str(unicode(self.lineedit1_4.text(), 'utf-8', 'ignore'))
			config.set('mail', 'passwd', passwd)
			self.save()

	def lineedit1_5_edited(self):
		global sleep
		if sleep != str(unicode(self.lineedit1_5.text(), 'utf-8', 'ignore')):
			sleep = str(unicode(self.lineedit1_5.text(), 'utf-8', 'ignore'))
			if sleep == '':
				sleep = '0'
				self.lineedit1_5.setText(sleep)
			config.set('settings', 'sleep', sleep)
			self.save()

	def lineedit2_1_edited(self):
		global tag_shutdown
		if tag_shutdown != str(unicode(self.lineedit2_1.text(), 'utf-8', 'ignore')):
			tag_shutdown = str(unicode(self.lineedit2_1.text(), 'utf-8', 'ignore'))
			config.set('commands', 'tag_shutdown', tag_shutdown)
			self.save()

	def lineedit2_2_edited(self):
		global tag_screen
		if tag_screen != str(unicode(self.lineedit2_2.text(), 'utf-8', 'ignore')):
			tag_screen = str(unicode(self.lineedit2_2.text(), 'utf-8', 'ignore'))
			config.set('commands', 'tag_screen', tag_screen)
			self.save()

	def lineedit2_3_edited(self):
		global tag_cam
		if tag_cam != str(unicode(self.lineedit2_3.text(), 'utf-8', 'ignore')):
			tag_cam = str(unicode(self.lineedit2_3.text(), 'utf-8', 'ignore'))
			config.set('commands', 'tag_cam', tag_cam)
			self.save()

	def lineedit2_4_edited(self):
		global tag_button
		if tag_button != str(unicode(self.lineedit2_4.text(), 'utf-8', 'ignore')):
			tag_button = str(unicode(self.lineedit2_4.text(), 'utf-8', 'ignore'))
			config.set('commands', 'tag_button', tag_button)
			self.save()

	def lineedit2_5_edited(self):
		global tag_cmd
		if tag_cmd != str(unicode(self.lineedit2_5.text(), 'utf-8', 'ignore')):
			tag_cmd = str(unicode(self.lineedit2_5.text(), 'utf-8', 'ignore'))
			config.set('commands', 'tag_cmd', tag_cmd)
			self.save()

	def btn4_1_clicked(self):
		global cam_open
		if cam_open == False:
			self.btn4_1.setText(u'关闭预览画面')
			cam_open = True
			self.cam_thread.start()
		else:
			self.btn4_1.setText(u'打开预览画面')
			cam_open = False
			cam.pop()
			cam.append(Device(devnum = cam_no))
			self.cam_thread.wait()

	#按下“重设为默认”按钮后触发
	def btn_default_clicked(self):
		global autostart, startsend, sleep, tag_shutdown, tag_screen, tag_cam, tag_button, \
		tag_cmd, whitelist, blacklist, cam_no
		if current_page == 1:
			self.lineedit1_1_a.setText(u'#110')
			self.lineedit1_2_a.setText(u'25')
			self.check1_1.setChecked(False)
			self.check1_2.setChecked(False)
			self.check1_2.setEnabled(False)
			self.lineedit1_5.setText(u'2')
			popport = '110'
			smtpport = '25'
			autostart = 0
			startsend = 0
			sleep = '2'
			config.set('mail', 'popport', popport)
			config.set('mail', 'smtpport', smtpport)
			config.set('settings', 'autostart', autostart)
			config.set('settings', 'startsend', startsend)
			config.set('settings', 'sleep', sleep)
		elif current_page == 2:
			self.lineedit2_1.setText(u'#shutdown')
			self.lineedit2_2.setText(u'#screen')
			self.lineedit2_3.setText(u'#cam')
			self.lineedit2_4.setText(u'#button')
			self.lineedit2_5.setText(u'#cmd')
			tag_shutdown = '#shutdown'
			tag_screen = '#screen'
			tag_cam = '#cam'
			tag_button = '#button'
			tag_cmd = '#cmd'
			config.set('commands', 'tag_shutdown', tag_shutdown)
			config.set('commands', 'tag_screen', tag_screen)
			config.set('commands', 'tag_cam', tag_cam)
			config.set('commands', 'tag_button', tag_button)
			config.set('commands', 'tag_cmd', tag_cmd)
		elif current_page == 3:
			self.textedit.setText(user)
			whitelist = user
			config.set('settings', 'whitelist', whitelist)
		elif current_page == 4:
			self.combobox4_1.setCurrentIndex(0)
			cam_no = 0
			config.set('settings', 'cam_no', cam_no)
		self.save()

	#各QCheckBox的状态有变化时触发
	def check_change1_1(self):
		global autostart, startsend
		if self.check1_1.isChecked() == True:
			self.check1_2.setEnabled(True)
			autostart = 1
			set_shortcut()
		else:
			self.check1_2.setChecked(False)
			self.check1_2.setEnabled(False)
			autostart = 0
			startsend = 0
			del_shortcut()
		config.set('settings', 'autostart', autostart)
		config.set('settings', 'startsend', startsend)
		self.save()

	def check_change1_2(self):
		global startsend
		if self.check1_2.isChecked() == True:
			startsend = 1
		else:
			startsend = 0
		config.set('settings', 'startsend', startsend)
		self.save()

	def combobox_change4_1(self):
		global cam_no
		cam_no = self.combobox4_1.currentIndex()
		config.set('settings', 'cam_no', cam_no)
		self.save()

	#self.textedit被编辑后触发
	def textedit_changed(self):
		global whitelist
		whitelist = str(unicode(self.textedit.toPlainText(), 'utf-8', 'ignore'))
		config.set('settings', 'whitelist', whitelist)
		self.save()

	#摄像头画面预览线程，每次拍照都会触发，用于实时更新摄像头预览画面
	def camera(self):
		time.sleep(0.01)
		try:
			self.label4_2.setPixmap(QPixmap.fromImage(img))
			if cam_open == False:
				self.label4_2.setPixmap(QPixmap('ui/images/camera.png'))
		except:
			pass

	#提示文字淡入淡出，用于更新画面
	def trans(self):
		self.label_opacity.setStyleSheet(u'QLabel{background:rgba(36, 48, 64, ' + str(opacity) + '%)}')
		self.update()

	#保存设置到config.ini
	def save(self):
		global new_trans
		config.write(open('config.ini', 'w'))
		self.label_prompt.setText(u'<p align=right style="font-family:Microsoft YaHei;font:13px;color:'
			u'#7DFF00">更改已保存<img src="ui/images/saved.png"></p>')
		new_trans = True
		time.sleep(0.01)
		self.trans_thread.start()
			
	#正在连接服务器
	def server_trigger1(self):
		global new_trans
		self.label_prompt.setText(u'<p align=right style="font-family:Microsoft YaHei;font:13px;'
			u'color:#4C8BF5">正在连接邮箱服务器...</p>')
		new_trans = True
		time.sleep(0.01)
		self.in_thread.start()

	#服务器连接失败
	def server_trigger2(self):
		global new_trans
		self.label_prompt.setText(u'<p align=right style="font-family:Microsoft YaHei;font:13px;'
			u'color:#DE5347">服务器连接失败！</p>')
		new_trans = True
		time.sleep(0.01)
		self.trans_thread.start()
		self.stop_server()
		self.reconnect_thread.start()

	#用户名或密码错误
	def server_trigger3(self):
		global new_trans
		self.label_prompt.setText(u'<p align=right style="font-family:Microsoft YaHei;font:13px;'
			u'color:#DE5347">用户名或密码错误！</p>')
		new_trans = True
		time.sleep(0.01)
		self.trans_thread.start()
		self.stop_server()
		self.reconnect_thread.start()

	#未知错误（已成功连接至邮箱服务器，大多是执行命令时的错误）
	def server_trigger4(self):
		global new_trans
		self.label_prompt.setText(u'<p align=right style="font-family:Microsoft YaHei;font:13px;'
			u'color:#DE5347">未知错误！</p>')
		new_trans = True
		time.sleep(0.01)
		self.trans_thread.start()
		self.stop_server()
		self.reconnect_thread.start()

	#成功连接到服务器
	def server_trigger5(self):
		global new_trans
		self.label_prompt.setText(u'<p align=right style="font-family:Microsoft YaHei;font:13px;'
			u'color:#7DFF00">成功连接至服务器！</p>')
		new_trans = True
		time.sleep(0.01)
		self.trans_thread.start()

	#执行拍照命令后关闭摄像头
	def server_trigger6(self):
		cam.pop()
		cam.append(Device(devnum = cam_no))

	#点击任务栏通知中心图标后显示主界面
	def trayClick(self, reason):
		if reason == QSystemTrayIcon.Trigger:
			self.show()
			self.activateWindow()

	#暂停邮箱服务
	def stop_server(self):
		global service, opacity
		service = False
		self.trayIcon.setToolTip(u'Email My PC - Off')
		self.trayIcon.setIcon(self.icon_off)
		self.alterAction.setText(u'开启服务')
		self.on_off.setChecked(False)
		opacity = 100
		self.label_opacity.setStyleSheet(u'QLabel{background:rgba(36, 48, 64, ' + str(opacity) + '%)}')

	#继续邮箱服务
	def start_server(self):
		global service
		if popserver != '' and smtpserver != '' and user != '' and passwd != '' and popport != '' and smtpport != '':
			service = True
			self.trayIcon.setToolTip(u'Email My PC - On')
			self.trayIcon.setIcon(self.icon_on)
			self.alterAction.setText(u'关闭服务')
			self.on_off.setChecked(True)
		else:
			self.stop_server()
			self.label_prompt.setText(u'<p align=right style="font-family:Microsoft YaHei;font:13px;'
				u'color:#4C8BF5">请完整填写邮箱服务器信息</p>')
			new_trans = True
			time.sleep(0.01)
			self.in_thread.start()

	#切换服务状态
	def alter(self):
		if service == True:
			try:
				self.stop_server()
			except:
				pass
		else:
			self.start_server()

	#点击“显示主界面”菜单后显示主界面
	def board(self):
		self.show()
		self.activateWindow()

	#退出程序
	def exit(self):
		self.cam_thread.terminate()
		self.server_thread.terminate()
		self.in_thread.terminate()
		self.trans_thread.terminate()
		self.trayIcon.hide()
		sys.exit()

#解析新邮件，获取其中的信息
def get_info(msg, indent = 0):
	subject = ''
	addr = ''
	content = ''
	if indent == 0:
		for header in ['From', 'Subject']:
			value = msg.get(header, '')
			if value:
				if header=='Subject':
					subject = decode_str(value)
				else:
					hdr, addr = parseaddr(value)
	if msg.is_multipart():
		parts = msg.get_payload()
		for n, part in enumerate(parts):
			content_value = get_info(part, indent + 1)[2]
			if content_value != '':
				content = content_value
	else:
		content_type = msg.get_content_type()
		if content_type=='text/plain':
			content = msg.get_payload(decode=True)
			charset = guess_charset(msg)
			if charset:
				content = content.decode(charset)
		else:
			content = ''
	return (subject, addr, content)

#解决邮件中的编码问题
def decode_str(s):
	value, charset = decode_header(s)[0]
	if charset:
		value = value.decode(charset)
	return value

#获取邮件的编码信息
def guess_charset(msg):
	charset = msg.get_charset()
	if charset is None:
		content_type = msg.get('Content-Type', '').lower()
		pos = content_type.find('charset=')
		if pos >= 0:
			charset = content_type[pos + 8:].strip()
	return charset

#快捷键处理函数
def button_event(content):
	key_table = {'BACKSPACE':8, 'TAB':9, 'TABLE':9, 'CLEAR':12, 'ENTER':13, 'SHIFT':16, 'CTRL':17, 
		'CONTROL':17, 'ALT':18, 'ALTER':18, 'PAUSE':19, 'BREAK':19, 'CAPSLK':20, 'CAPSLOCK':20, 'ESC':27, 
		'SPACE':32, 'SPACEBAR':32, 'PGUP':33, 'PAGEUP':33, 'PGDN':34, 'PAGEDOWN':34, 'END':35, 'HOME':36, 
		'LEFT':37, 'UP':38, 'RIGHT':39, 'DOWN':40, 'SELECT':41, 'PRTSC':42, 'PRINTSCREEN':42, 'SYSRQ':42, 
		'SYSTEMREQUEST':42, 'EXECUTE':43, 'SNAPSHOT':44, 'INSERT':45, 'DELETE':46, 'HELP':47, 'WIN':91, 
		'WINDOWS':91, 'F1':112, 'F2':113, 'F3':114, 'F4':115, 'F5':116, 'F6':117, 'F7':118, 'F8':119, 
		'F9':120, 'F10':121, 'F11':122, 'F12':123, 'F13':124, 'F14':125, 'F15':126, 'F16':127, 'NMLK':144, 
		'NUMLK':144, 'NUMLOCK':144, 'SCRLK':145, 'SCROLLLOCK':145, 'LEFTCLICK':999, 'RIGHTCLICK':1000}
	unrecognized = ''
	key_values = []
	keys = content.split('+')
	for key in keys:
		raw_key = key
		key = key.strip().replace(' ','').upper()
		if key in key_table:
			key_values.append(key_table.get(key))
		elif len(key) == 1:
			key_values.append(ord(key))
		else:
			if key != '':
				unrecognized = raw_key
	for key_value in key_values:
		if key_value == 999:
			win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
		elif key_value == 1000:
			win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
		else:
			win32api.keybd_event(key_value, 0, 0, 0)
		time.sleep(1)
	for i in range(len(key_values)-1, -1, -1):
		if key_value == 999:
			win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
		elif key_value == 1000:
			win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
		else:
			win32api.keybd_event(key_values[i], 0, win32con.KEYEVENTF_KEYUP, 0)
		time.sleep(1)
	return unrecognized

#设置开机启动快捷方式
def set_shortcut():
	startup_path = shell.SHGetPathFromIDList(shell.SHGetSpecialFolderLocation(0,shellcon.CSIDL_STARTUP))
	shortcut = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, \
		shell.IID_IShellLink)
	shortcut.SetPath(os.getcwd()+'\\Email My PC Launcher.exe')
	shortcut.SetWorkingDirectory(os.getcwd())
	shortcut.SetIconLocation(os.getcwd()+'\\ui\\images\\Icon.ico',0)
	shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(startup_path+'\\Emai My PC.lnk',0)

#删除开机启动快捷方式
def del_shortcut():
	startup_path = shell.SHGetPathFromIDList(shell.SHGetSpecialFolderLocation(0,shellcon.CSIDL_STARTUP))
	path = startup_path + '\\Emai My PC.lnk'
	if os.path.exists(path):
		os.remove(path)

#主函数，读取设置信息，并启动界面
def main():
	global config, popserver, popport, smtpserver, smtpport, user, passwd, autostart, startsend, sleep, \
	cam_no, whitelist, tag_shutdown, tag_screen, tag_cam, tag_button, tag_cmd, version, \
	service
	startup_path = shell.SHGetPathFromIDList(shell.SHGetSpecialFolderLocation(0, shellcon.CSIDL_STARTUP))
	service = True
	if os.path.isfile(startup_path + '/Emai My PC.lnk'):
		autostart = 1
	else:
		autostart = 0
	config = ConfigParser.ConfigParser()
	config.read('config.ini')
	popserver = config.get('mail', 'popserver')
	popport = config.get('mail', 'popport')
	smtpserver = config.get('mail', 'smtpserver')
	smtpport = config.get('mail', 'smtpport')
	user = config.get('mail', 'user')
	passwd = config.get('mail', 'passwd')
	startsend = config.get('settings', 'startsend')
	sleep = config.get('settings', 'sleep')
	cam_no = int(config.get('settings', 'cam_no'))
	whitelist = config.get('settings', 'whitelist')
	tag_shutdown = config.get('commands', 'tag_shutdown')
	tag_screen = config.get('commands', 'tag_screen')
	tag_cam = config.get('commands', 'tag_cam')
	tag_button = config.get('commands', 'tag_button')
	tag_cmd = config.get('commands', 'tag_cmd')
	version = config.get('version', 'version')
	app = QApplication(sys.argv)
	form = Setting_UI()
	sys.exit(app.exec_())

if __name__ == '__main__':
	myapp = singleinstance()
	if myapp.aleradyrunning():
		sys.exit(0)
	else:
		 main()
