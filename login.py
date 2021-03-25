# -*- coding: utf-8 -*-

import base64
import os
import json
import logging
import uuid
from urllib.parse import urlparse
import pickle

import requests
from pyDes import CBC, PAD_PKCS5, des
from requests.sessions import session
from retrying import retry


class Login(object):
    api = "http://www.zimo.wiki:8080/wisedu-unified-login-api-v1.0/api/login"

    logging.basicConfig(
        format="%(asctime)s  %(filename)s : %(levelname)s  %(message)s",
        level=logging.INFO,
    )

    def __init__(self, username, password, school, address):
        self.username = username
        self.password = password
        self.school = school
        self.address = address
        self.apis = {}
        self.session = None

    # 获取今日校园api
    def getApis(self):
        logging.info("获取学校apis")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.54",
            "Host": "mobile.campushoy.com",
        }
        schools = requests.get(
            url="https://mobile.campushoy.com/v6/config/guest/tenant/list",
            headers=headers,
        ).json()["data"]
        flag = True
        for one in schools:
            if one["name"] == self.school:
                if one["joinType"] == "NONE":
                    logging.info(self.school + " 未加入今日校园")
                    exit(-1)
                flag = False
                params = {"ids": one["id"]}
                res = requests.get(
                    url="https://mobile.campushoy.com/v6/config/guest/tenant/info",
                    params=params,
                    headers=headers,
                )
                data = res.json()["data"][0]
                # joinType = data['joinType']
                idsUrl = data["idsUrl"]
                ampUrl = data["ampUrl"]
                if "campusphere" in ampUrl or "cpdaily" in ampUrl:
                    parse = urlparse(ampUrl)
                    host = parse.netloc
                    res = requests.get(parse.scheme + "://" + host)
                    parse = urlparse(res.url)
                    self.apis["login-url"] = (
                        idsUrl
                        + "/login?service="
                        + parse.scheme
                        + r"%3A%2F%2F"
                        + host
                        + r"%2Fportal%2Flogin"
                    )
                    self.apis["host"] = host

                ampUrl2 = data["ampUrl2"]
                if "campusphere" in ampUrl2 or "cpdaily" in ampUrl2:
                    parse = urlparse(ampUrl2)
                    host = parse.netloc
                    res = requests.get(parse.scheme + "://" + host)
                    parse = urlparse(res.url)
                    self.apis["login-url"] = (
                        idsUrl
                        + "/login?service="
                        + parse.scheme
                        + r"%3A%2F%2F"
                        + host
                        + r"%2Fportal%2Flogin"
                    )
                    self.apis["host"] = host
                break
        if flag:
            logging.info(self.school + " 未找到该院校信息，请检查是否是学校全称错误")
            raise Exception("未找到该院校信息，请检查是否是学校全称错误")
        logging.info(self.apis)
        self.apis = self.apis
        return self

    # 如果请求返回的数据非200 重试
    def retry_if_vaule_error(exception):
        if isinstance(exception, BaseException):
            logging.info("失败，重试中。。。")
        return isinstance(exception, BaseException)

    # 读取cookies
    def cookies_read(self):
        logging.info("读取本地储存的cookies")
        cookies_file = self.username + "_" + "cookies.txt"
        if os.path.exists(cookies_file):
            with open(cookies_file, "rb") as f:
                cookies_dict = pickle.load(f)
                cookies = requests.utils.cookiejar_from_dict(cookies_dict)
        else:
            raise Exception("文件不存在")
        return cookies

    @retry(stop_max_attempt_number=5, retry_on_exception=retry_if_vaule_error)
    def getCookies(self):
        params = {
            "login_url": self.apis["login-url"],
            "password": self.password,
            "username": self.username,
        }

        cookies = {}
        # 借助上一个项目开放出来的登陆API，模拟登陆
        logging.info("尝试登陆中。。。")
        res = requests.post(self.api, params=params)
        cookieStr = str(res.json()["cookies"])
        logging.info(cookieStr)
        if cookieStr == "None":
            logging.info(res.json())
            raise Exception("登录失败，原因可能是学号或密码错误，请检查配置后，重启脚本。。。")

        logging.info("登录成功。。。")
        # 解析cookie
        for line in cookieStr.split(";"):
            name, value = line.strip().split("=", 1)
            cookies[name] = value

        with open(self.username + "_" + "cookies.txt", "wb") as f:
            pickle.dump(cookies, f)

    # 登陆并返回session
    def getSession(self):
        session = requests.session()
        apis = self.apis
        try:
            cookies = self.cookies_read()
            session.cookies = cookies
            res = session.post(
                url="https://{host}/personCenter/user/getUserInfo".format(
                    host=apis["host"]
                ),
                headers={"content-type": "application/json"},
                data=json.dumps({}),
            )
            name = res.json().get("datas").get("userInfo")["userName"]
            logging.info("本地cookies登录成功")
            logging.info("当前用户: " + name)

        except Exception as e:
            logging.info(str(e))
            self.getCookies()
            cookies = self.cookies_read()
            session.cookies = cookies
            res = session.post(
                url="https://{host}/personCenter/user/getUserInfo".format(
                    host=apis["host"]
                ),
                headers={"content-type": "application/json"},
                data=json.dumps({}),
            )
            name = res.json().get("datas").get("userInfo")["userName"]
            logging.info("当前用户: " + name)

        self.session = session

        return self

    # 提交图片的处理
    # 上传图片到阿里云oss
    def uploadPicture(self, url, image):
        session = self.session
        res = session.post(
            url=url,
            headers={"content-type": "application/json"},
            data=json.dumps({"fileType": 1}),
        )
        datas = res.json().get("datas")
        # log(datas)
        # new_api_upload
        fileName = datas.get("fileName") + ".png"
        accessKeyId = datas.get("accessid")
        xhost = datas.get("host")
        xpolicy = datas.get("policy")
        signature = datas.get("signature")
        # new_api_upload
        # new_api_upload2
        url = xhost + "/"
        data = {
            "key": fileName,
            "policy": xpolicy,
            "OSSAccessKeyId": accessKeyId,
            "success_action_status": "200",
            "signature": signature,
        }
        data_file = {"file": ("blob", open(image, "rb"), "image/jpg")}
        res = session.post(url=url, data=data, files=data_file)
        if res.status_code == requests.codes.ok:
            return fileName
        # new_api_upload2
        # log(res)
        return ""

    # 获取图片上传位置
    @retry(stop_max_attempt_number=5, retry_on_exception=retry_if_vaule_error)
    def getPictureUrl(self, url, fileName):
        data = {"ossKey": fileName}
        res = self.session.post(
            url=url, headers={"content-type": "application/json"}, data=json.dumps(data)
        )
        photoUrl = res.json().get("datas")
        return photoUrl

    # 今日校园的DES加解密
    # DES加密
    @staticmethod
    def DESEncrypt(s, key="b3L26XNL"):
        key = key
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        encrypt_str = k.encrypt(s)
        return base64.b64encode(encrypt_str).decode()

    # DES解密
    @staticmethod
    def DESDecrypt(s, key="b3L26XNL"):
        s = base64.b64decode(s)
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        return k.decrypt(s)
