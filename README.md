# Email_My_PC
[![Software License](https://img.shields.io/badge/license-MIT-brightgreen.svg?style=flat-square)](LICENSE.txt) 
[![versions](https://img.shields.io/badge/versions%20-%20%201.2.3-blue.svg?style=flat-square)]() [![platform](https://img.shields.io/badge/platform%20-%20Windows-lightgrey.svg?style=flat-square)]()  
通过邮件远程监控你的电脑，在特定场景下很好用。
## 下载
[for Windows](http://download.jackeriss.com/works/Email_My_PC_1.2.3.zip)
## 截图
![1](https://ooo.0o0.ooo/2017/03/15/58c9338d443a6.png)  
# 使用指南
## 引言
本软件基本的使用流程是用户在软件中配置好自己的邮箱后即可通过给这个邮箱发命令的方式来监视、控制电脑。具体操作如下：

## 开启 POP3/SMTP 服务
用于接收命令的邮箱需要开启 POP3/SMTP 服务，下面以 QQ 邮箱为例来展示一下大致流程：  
1. 登陆 QQ 邮箱网页版，在正上方找到“设置”选项，点击“账户“选项卡。  
![](http://service.mail.qq.com/images/faq/pop.imap001.jpg)  
2. 然后，在“帐户”设置中，找到设置项，进行设置，如下：  
![](http://service.mail.qq.com/images/faq/mailsettings20120418003.jpg)  
3. 保存设置，即打开了相应的服务。  
4. 之后就可以获取授权密码了，点击“生成授权码”  
![](http://service.mail.qq.com/images/faq/76FD1EA3-AC06-4938-9E2F-E6789AA04996.jpeg)  
5. 接下来按要求验证密保手机就行了。  


## 选择端口号
大部分邮箱默认的不加密的端口号如下：  
POP3：110  
SMTP：25  
  
QQ邮箱的加密端口号：  
POP3：995  
SMTP：465 或 587  

163邮箱的加密端口号：  
POP3：995  
SMTP：465 或 994  
  
其他邮箱具体的端口号请自行搜索。  

## 其他基础配置
- 勾选“开机发送邮件通知”选项后，Email My PC 会在开机后为您的邮箱发送一封包含计算机名、开机时间、IP地址和地理位置等信息的邮件，方便您实时掌控您电脑的状态，防止电脑被他人使用。  

- 新邮件检测频率表示检测并执行新命令的频率，如果间隔太大会导致命令迟迟不会执行，推荐 1 到 2 秒为宜。  

- 所有发送命令的邮箱必须加入白名单其命令才会被执行。  

- 所有配置都会自动保存并应用，如发现更改未应用请重启软件。  

- 完成配置后请点击软件右下角的开关来开启服务，开关显示“ON”或通知栏图标为白色则表示服务已开启，开关显示“OFF”或通知栏图标为灰色则表示服务已关闭。  

## 发送命令邮件
将命令标签作为邮件标题发送至你在 Email My PC 中配置的邮箱。例如：你想查看桌面截图，就将“#screen”作为邮件的标题，正文空着就可以了。如果该命令需要参数，就把参数写在正文中。如你想执行快捷键“Win + L”，只需把“#button"作为邮件的标题，然后将”Win + L"作为正文即可。

## 接收结果
命令执行的结果会在几秒内发回发送该命令的邮箱。桌面截图和摄像头画面会以附件的形式发送。请一并查看垃圾箱以免遗漏。

## 常见问题
Q：为什么总是提示“服务器连接失败”或者“用户名或密码错误“？  
A：如果您使用的是 163 邮箱，163 邮箱的 POP3/SMTP 服务有访问频率限制，频率过大会被禁用，不适合作为 Email My PC 接受命令的邮箱。如果您使用的是 QQ 邮箱，则可能是 DNS 解析存在问题，请更改本机的 DNS 服务器地址后再次尝试，具体更改步骤不再赘述，推荐使用 114DNS, 如果问题依然存在，请尝试使用 gmail 或 hotmail。  
  
Q：连接没问题，发命令怎么没收到反馈？  
A：请检查是否已将发送命令的邮箱加入 Email My PC 的白名单中。  
