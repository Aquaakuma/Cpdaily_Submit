from login import Login
import logging
import uuid
import json


class Attendance(Login):
    def __init__(
        self, username, password, school, address, lon, lat, photo, abnormalReason
    ) -> None:
        super(Attendance, self).__init__(username, password, school, address)
        self.getApis().getSession()
        self.lon = lon
        self.lat = lat
        self.photo = photo
        self.abnormalReason = abnormalReason
        self.form = {}
        self.signTask = None
        self.unSignedTasks = {}

    # 查寝的获取、填写、提交
    # 获取最新未签到任务
    def getUnSignedTasks(self):
        session = self.session
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "content-type": "application/json",
            "Accept-Encoding": "gzip,deflate",
            "Accept-Language": "zh-CN,en-US;q=0.8",
            "Content-Type": "application/json;charset=UTF-8",
        }
        logging.info("正在获取签到任务")
        # 第一次请求每日签到任务接口，主要是为了获取MOD_AUTH_CAS
        res = session.post(
            url="https://{host}/wec-counselor-attendance-apps/student/attendance/getStuAttendacesInOneDay".format(
                host=self.apis["host"]
            ),
            headers=headers,
            data=json.dumps({}),
        )
        # 第二次请求每日签到任务接口，拿到具体的签到任务
        res = session.post(
            url="https://{host}/wec-counselor-attendance-apps/student/attendance/getStuAttendacesInOneDay".format(
                host=self.apis["host"]
            ),
            headers=headers,
            data=json.dumps({}),
        )
        if len(res.json()["datas"]["unSignedTasks"]) < 1:
            logging.info("当前没有未签到任务")
            raise Exception("当前没有未签到任务")

        latestTask = res.json()["datas"]["unSignedTasks"][0]
        logging.info("获取成功")
        self.unSignedTasks["signInstanceWid"] = latestTask["signInstanceWid"]
        self.unSignedTasks["signWid"] = latestTask["signWid"]

        return self

    # 获取签到任务详情
    def getDetailTask(self):
        session = self.session
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "content-type": "application/json",
            "Accept-Encoding": "gzip,deflate",
            "Accept-Language": "zh-CN,en-US;q=0.8",
            "Content-Type": "application/json;charset=UTF-8",
        }

        params = self.unSignedTasks
        logging.info("获取签到任务详情。。。")
        res = session.post(
            url="https://{host}/wec-counselor-attendance-apps/student/attendance/detailSignInstance".format(
                host=self.apis["host"]
            ),
            headers=headers,
            data=json.dumps(params),
        )
        data = res.json()["datas"]
        logging.info("获取成功")
        self.signTask = data
        return self

    # 填充表单
    def fillForm(self):
        logging.info("正在填写签到表单!")
        self.form["signInstanceWid"] = self.signTask["signInstanceWid"]
        self.form["longitude"] = self.lon
        self.form["latitude"] = self.lat
        self.form["isMalposition"] = self.signTask["isMalposition"]
        # form['isMalposition'] = '1'
        self.form["abnormalReason"] = self.abnormalReason
        if self.signTask["isPhoto"] == 1:
            fileName = self.uploadPicture(
                url="https://{host}/wec-counselor-sign-apps/stu/oss/getUploadPolicy".format(
                    host=self.apis["host"]
                ),
                image=self.photo,
            )
            self.form["signPhotoUrl"] = self.getPictureUrl(
                url="https://{host}/wec-counselor-sign-apps/stu/sign/previewAttachment".format(
                    host=self.apis["host"]
                ),
                fileName=fileName,
            )
        else:
            self.form["signPhotoUrl"] = ""
        self.form["position"] = self.address
        self.form["qrUuid"] = ""
        self.form["uaIsCpadaily"] = True
        logging.info("填写成功")
        logging.info(self.form)
        return self

    # 提交签到任务
    def signIn(self):
        # Cpdaily-Extension
        extension = {
            "lon": self.lon,
            "model": "PCRT00",
            "appVersion": "8.2.14",
            "systemVersion": "4.4.4",
            "userId": self.username,
            "systemName": "android",
            "lat": self.lat,
            "deviceId": str(uuid.uuid1()),
        }
        headers = {
            # 'tenantId': apis['tenantId'],
            "User-Agent": "Mozilla/5.0 (Linux; Android 4.4.4; PCRT00 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Mobile Safari/537.36 okhttp/3.8.1",
            "CpdailyStandAlone": "0",
            "extension": "1",
            # 'Cpdaily-Extension': '1wAXD2TvR72sQ8u+0Dw8Dr1Qo1jhbem8Nr+LOE6xdiqxKKuj5sXbDTrOWcaf v1X35UtZdUfxokyuIKD4mPPw5LwwsQXbVZ0Q+sXnuKEpPOtk2KDzQoQ89KVs gslxPICKmyfvEpl58eloAZSZpaLc3ifgciGw+PIdB6vOsm2H6KSbwD8FpjY3 3Tprn2s5jeHOp/3GcSdmiFLYwYXjBt7pwgd/ERR3HiBfCgGGTclquQz+tgjJ PdnDjA==',
            "Cpdaily-Extension": self.DESEncrypt(json.dumps(extension)),
            "Content-Type": "application/json; charset=utf-8",
            "Host": self.apis["host"],
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }

        # session.cookies.set('AUTHTGC', session.cookies.get('CASTGC'))
        logging.info("正在提交签到任务。。。")
        res = self.session.post(
            url="https://{host}/wec-counselor-attendance-apps/student/attendance/submitSign".format(
                host=self.apis["host"]
            ),
            headers=headers,
            data=json.dumps(self.form),
        )

        message = res.json()["message"]
        if message != "SUCCESS":
            raise Exception("自动查寝提交失败，原因是：" + message)
        logging.info("提交成功")
        return message
