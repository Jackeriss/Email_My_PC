#coding=utf-8
import smtplib,os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
smtp = smtplib.SMTP()
def send(smtpserver, user, passwd, title, msg = None, file_name = None):
    msgRoot = MIMEMultipart('related')
    msgRoot['From'] = "Email My PC"
    msgRoot['Subject'] = title
    if msg != None:
        msgText = MIMEText('%s'%msg,'html','utf-8')
        msgRoot.attach(msgText)
    if file_name != None:
        att = MIMEText(open('%s'%file_name, 'rb').read(), 'base64', 'utf-8')
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment; filename="%s"'%file_name
        msgRoot.attach(att)
    while 1:
        try:
            smtp.sendmail(user, user, msgRoot.as_string())
            break
        except:
            try:
                smtp.connect(smtpserver)
                smtp.login(user, passwd)
            except:
                pass
    if file_name != None:
        path = os.getcwd() + "\\" + file_name
        if os.path.exists(path):
            os.remove(path)
