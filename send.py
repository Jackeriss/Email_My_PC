#coding=utf-8
import smtplib,os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

def send(smtpserver, smtpport, user, mailto, passwd, title, msg=None, file_name=None):  
    msgRoot = MIMEMultipart('related')
    msgRoot['From'] = "Email_My_PC"
    msgRoot['Subject'] = title
    if msg != None:
        msgText = MIMEText('%s' % msg, 'html', 'utf-8')
        msgRoot.attach(msgText)
    if file_name != None:
        att = MIMEText(open('%s' % file_name, 'rb').read(), 'base64', 'utf-8')
        att["Content-Type"] = 'application/octet-stream'
        att["Content-Disposition"] = 'attachment; filename="%s"' % file_name
        msgRoot.attach(att)
    try_num = 0
    try_max = 10
    while 1:
        try_num += 1
        try:
            smtp.sendmail(user, mailto, msgRoot.as_string())
            break
        except:
            try:
                #绝大多数邮箱不开启加密时的SMTP端口为25
                if smtpport == '25':
                    smtp = smtplib.SMTP(smtpserver, smtpport)
                #587端口常用作TLS加密
                elif smtpport == '587':
                    smtp = smtplib.SMTP(smtpserver, smtpport)
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                else:
                    smtp = smtplib.SMTP_SSL(smtpserver, smtpport)
                smtp.login(user, passwd)
            except:
                if try_num > try_max:
                    break
                pass
    if file_name != None:
        path = os.getcwd() + "\\" + file_name
        if os.path.exists(path):
            os.remove(path)
