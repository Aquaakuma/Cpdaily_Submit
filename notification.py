# -*- coding: utf-8 -*-
import logging
import smtplib
from datetime import datetime, timedelta, timezone
from email.header import Header
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from get_img import download_pic


class notification(object):
    def __init__(self, **smtp):
        self.smtp_from = smtp["smtp_from"]  # 发件人邮箱账号
        self.smtp_pass = smtp["smtp_pass"]  # 发件人邮箱密码
        self.apikey = smtp["apikey"]

    # 获取当前utc时间，并格式化为北京时间
    @staticmethod
    def getTimeStr():
        utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
        bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
        return bj_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 发送邮件通知
    def sendQmail(self, email, title, content, picture=None):
        smtp_to = email  # 收件人邮箱账号，我这边发送给自己
        logging.info("填写邮件内容。。。")
        msg = MIMEMultipart("related")

        msg["From"] = self.smtp_from
        msg["To"] = smtp_to
        msg["Subject"] = Header(str(title), "utf-8").encode()

        logging.info("发送邮件")
        try:
            if picture == None:
                picture = download_pic(self.apikey)
            with open(picture, "rb") as f:
                msg_str = """
                    <p>{content}</p>
                    <img src="cid:pixiv">
                    """.format(
                    content=content
                )
                pic = MIMEImage(f.read())
                pic.add_header("Content-ID", "<pixiv>")
                msg.attach(MIMEText(msg_str, "html", "utf-8"))
                msg.attach(pic)
            self.send = smtplib.SMTP_SSL("smtp.qq.com")
            self.send.login(self.smtp_from, self.smtp_pass)
            self.send.sendmail(self.smtp_from, smtp_to, msg.as_string())
            logging.info("发送成功")
        except:
            logging.info("发送失败")

        self.send.quit()
