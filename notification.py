# -*- coding: utf-8 -*-
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from get_img import download_pic


# 获取当前utc时间，并格式化为北京时间
def getTimeStr():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")

# 输出调试信息，并及时刷新缓冲区
def log(content):
    print(getTimeStr() + ' ' + str(content))
    sys.stdout.flush()

# server酱通知
def sendServerChan(msg, sckey):
    log('正在发送Server酱。。。')
    res = requests.post(url='https://sctapi.ftqq.com/{0}.send'.format(sckey),
                            data={'title': '今日校园疫情上报结果通知', 'desp': getTimeStr() + "\n" + str(msg)})
    code = res.json()['data']['error']
    if code == 'SUCCESS':
        log('发送Server酱通知成功。。。')
    else:
        log('发送Server酱通知失败。。。')
        log('Server酱返回结果'+code)


# 发送邮件通知
def sendMessage(msg, email):
    if email != '':
        log('正在发送邮件通知。。。')
        res = requests.post(url='http://www.zimo.wiki:8080/mail-sender/sendMail',
                            data={'title': str(msg), 'content': "此邮件为今日校园疫情上报结果通知！如签到成功，不用理会即可。", 'to': email})

        code = res.json()['code']
        if code == 0:
            log('发送邮件通知成功。。。')
        else:
            log('发送邮件通知失败。。。')
            log(res.json())

# def sendEmail(msg, email, smtp_profile):
#     smtp_from= smtp_profile['smtp_from']  # 发件人邮箱账号
#     smtp_pass = smtp_profile['smtp_pass']         # 发件人邮箱密码
#     smtp_to = email      # 收件人邮箱账号，我这边发送给自己
#     try:
#         msg=MIMEText(getTimeStr() + '此邮件为今日校园疫情上报结果通知！如签到成功，不用理会即可。','plain','utf-8')
#         msg['From']=formataddr(["bot",smtp_from])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
#         msg['To']=formataddr([smtp_profile['email'],smtp_to])              # 括号里的对应收件人邮箱昵称、收件人邮箱账号
#         msg['Subject']=str(msg)               # 邮件的主题，也可以说是标题

#         server=smtplib.SMTP_SSL(smtp_profile['smtp_server'], smtp_profile['smtp_port'])  # 发件人邮箱中的SMTP服务器，端口是25
#         server.login(smtp_from, smtp_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
#         server.sendmail(smtp_from,[smtp_to,],msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
#         server.quit()  # 关闭连接
#     except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
#         log("邮件发送失败")
#     else: print("邮件发送成功")
def sendQmail(picture, title, smtp_profile):
    smtp_from = smtp_profile['smtp_from']  # 发件人邮箱账号
    smtp_pass = smtp_profile['smtp_pass']         # 发件人邮箱密码
    smtp_to = smtp_profile['email']      # 收件人邮箱账号，我这边发送给自己
    msg = MIMEMultipart('related')
    msg_str = """
    <p>以下是TUT的老婆</p>
    <img src="cid:pixiv">
    """
    msg.attach(MIMEText(msg_str, 'html', 'utf-8'))
    with open(picture, 'rb') as f:
        pic = MIMEImage(f.read())
        pic.add_header('Content-ID', '<pixiv>')
        msg.attach(pic)

    msg['From'] = smtp_from
    msg['To'] = smtp_to
    msg['Subject'] = Header(str(title), 'utf-8').encode()
    smtp = smtplib.SMTP_SSL('smtp.qq.com')
    try:
        smtp.login(smtp_from, smtp_pass)
    except Exception as e:
        raise e
    smtp.sendmail(smtp_from, smtp_to, msg.as_string())
    smtp.quit()


# 综合提交
def InfoSubmit(msg, msg_profile):
    if('apikey' in msg_profile.keys() and msg_profile['apikey']):
        picture = download_pic(msg_profile['apikey'])
        print("获取图片建议使用apikey, 了解详情: https://api.lolicon.app/#/setu")
    else:
        picture = download_pic('')
    if ('email' in msg_profile.keys()):
        if('smtp_from' in msg_profile.keys() and 'smtp_pass' in msg_profile.keys()):
            sendQmail(picture, msg, msg_profile)
        else:
            print("smtp账户或密码不存在, 尝试使用第三方服务发送邮件")
            sendMessage(msg_profile['email'] , msg)
    else:
        print("没有邮箱接收地址，将不会发送邮件通知")
    if('sckey' in msg_profile.keys()):
        if(msg_profile['sckey']): sendServerChan(msg, msg_profile['sckey'])
    else:
        print("没有server酱sckey，将不会发送微信通知")
