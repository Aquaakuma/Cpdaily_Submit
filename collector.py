from login import Login
import logging
import json
import yaml


class Collector(Login):
    def __init__(self, username, password, school, address, photo) -> None:
        super(Collector, self).__init__(username, password, school, address)
        self.getApis().getSession()
        self.form = None
        self.collectWid = None
        self.formWid = None
        self.schoolTaskWid = None
        self.photo = photo

    # 普通收集的查询、填写、提交
    # 查询表单
    def queryForm(self):
        host = self.apis["host"]
        session = self.session
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Linux; Android 4.4.4; OPPO R11 Plus Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 okhttp/3.12.4",
            "content-type": "application/json",
            "Accept-Encoding": "gzip,deflate",
            "Accept-Language": "zh-CN,en-US;q=0.8",
            "Content-Type": "application/json;charset=UTF-8",
        }
        queryCollectWidUrl = "https://{host}/wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList".format(
            host=host
        )
        params = {"pageSize": 6, "pageNumber": 1}
        logging.info("正在查询最新待填写问卷。。。")
        res = session.post(queryCollectWidUrl, headers=headers, data=json.dumps(params))
        if len(res.json()["datas"]["rows"]) < 1:
            logging.info("没有新问卷")
            return self

        logging.info("找到新问卷")
        self.collectWid = res.json()["datas"]["rows"][0]["wid"]
        self.formWid = res.json()["datas"]["rows"][0]["formWid"]

        detailCollector = "https://{host}/wec-counselor-collector-apps/stu/collector/detailCollector".format(
            host=host
        )
        res = session.post(
            url=detailCollector,
            headers=headers,
            data=json.dumps({"collectorWid": self.collectWid}),
        )
        self.schoolTaskWid = res.json()["datas"]["collector"]["schoolTaskWid"]

        getFormFields = "https://{host}/wec-counselor-collector-apps/stu/collector/getFormFields".format(
            host=host
        )
        res = session.post(
            url=getFormFields,
            headers=headers,
            data=json.dumps(
                {
                    "pageSize": 100,
                    "pageNumber": 1,
                    "formWid": self.formWid,
                    "collectorWid": self.collectWid,
                }
            ),
        )

        self.form = res.json()["datas"]["rows"]
        return self

    # 生成表单
    def generate(self):
        form = self.form
        defaults = []
        sort = 1
        for formItem in form:
            if formItem["isRequired"] == 1:
                default = {}
                one = {}
                default["title"] = formItem["title"]
                default["type"] = formItem["fieldType"]
                print("问题%d：" % sort + default["title"])
                if default["type"] == 1 or default["type"] == 5:
                    default["value"] = input("请输入文本：")
                if default["type"] == 2:
                    fieldItems = formItem["fieldItems"]
                    num = 1
                    for fieldItem in fieldItems:
                        print("\t%d " % num + fieldItem["content"])
                        num += 1
                    choose = int(input("请输入序号："))
                    if choose < 1 or choose > num:
                        print("输入错误，请重新执行此脚本")
                        exit(-1)
                    default["value"] = fieldItems[choose - 1]["content"]
                if default["type"] == 3:
                    fieldItems = formItem["fieldItems"]
                    num = 1
                    for fieldItem in fieldItems:
                        print("\t%d " % num + fieldItem["content"])
                        num += 1
                    chooses = list(map(int, input("请输入序号（可输入多个，请用空格隔开）：").split()))
                    default["value"] = ""
                    for i in range(0, len(chooses)):
                        choose = chooses[i]
                        if choose < 1 or choose > num:
                            print("输入错误，请重新执行此脚本")
                            exit(-1)
                        if i != len(chooses) - 1:
                            default["value"] += fieldItems[choose - 1]["content"] + ","
                        else:
                            default["value"] += fieldItems[choose - 1]["content"]
                if default["type"] == 4:
                    default["value"] = input("请输入图片名称：")
                one["default"] = default
                defaults.append(one)
                sort += 1
        print("======================分隔线======================")
        print(yaml.dump(defaults, allow_unicode=True))

    # 填写form
    def fillForm(self, form):
        sort = 1
        Form = self.form
        if Form == None:
            raise Exception("填写问卷失败，可能是辅导员没有发布！")
        else:
            logging.info("找到新问卷，开始填写。。。")

        for formItem in Form[:]:
            # 只处理必填项
            if formItem["isRequired"] == 1:
                default = form["defaults"][sort - 1]["default"]
                if formItem["title"] != default["title"]:
                    logging.info("第%d个默认配置不正确，请检查" % sort)
                    raise Exception("第%d个默认配置不正确，请检查")
                # 文本直接赋值
                if formItem["fieldType"] == 1 or formItem["fieldType"] == 5:
                    formItem["value"] = default["value"]
                # 单选框需要删掉多余的选项
                if formItem["fieldType"] == 2:
                    # 填充默认值
                    formItem["value"] = default["value"]
                    fieldItems = formItem["fieldItems"]
                    for i in range(0, len(fieldItems))[::-1]:
                        if fieldItems[i]["content"] != default["value"]:
                            del fieldItems[i]
                # 多选需要分割默认选项值，并且删掉无用的其他选项
                if formItem["fieldType"] == 3:
                    fieldItems = formItem["fieldItems"]
                    defaultValues = default["value"].split(",")
                    for i in range(0, len(fieldItems))[::-1]:
                        flag = True
                        for j in range(0, len(defaultValues))[::-1]:
                            if fieldItems[i]["content"] == defaultValues[j]:
                                # 填充默认值
                                formItem["value"] += defaultValues[j] + " "
                                flag = False
                        if flag:
                            del fieldItems[i]
                # 图片需要上传到阿里云oss
                if formItem["fieldType"] == 4:
                    fileName = self.uploadPicture(
                        url="https://{host}/wec-counselor-sign-apps/stu/oss/getUploadPolicy".format(
                            host=self.apis["host"]
                        ),
                        image=self.photo,
                    )
                    formItem["value"] = self.getPictureUrl(
                        url="https://{host}/wec-counselor-sign-apps/stu/sign/previewAttachment".format(
                            host=self.apis["host"]
                        ),
                        fileName=fileName,
                    )
                logging.info("必填问题%d：" % sort + formItem["title"])
                logging.info("答案%d：" % sort + formItem["value"])
                sort += 1
            else:
                Form["form"].remove(formItem)
        logging.info("填写成功")
        self.form = Form
        return self

    # 提交表单
    def submitForm(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 4.4.4; OPPO R11 Plus Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 okhttp/3.12.4",
            "CpdailyStandAlone": "",
            "extension": "1",
            "Cpdaily-Extension": "Ew9uONYq03Siz+VLCzZ4RiWRaXXBubIGc1d7ecaS2YmSDf1+elDL0gdwAw977HbPzvgR3pkeyW3djmnPOMxYro3Tps7PNmLoqfNTAECZqcM1LAyx+2zTfDExNa4yDWs83AyTnSKXs7oHQvFOfXhKNY1OXVzIdnwOkgaNw7XxzM1+2efCWAJgUBoHNV3n3MayLqOwPvSCvBke+SHC/Hy/53+ehU9A1lst6JlpGiFhlEOUybo5s5/o+b/XLUexuEE50IQgdPL4Hi4vPe4yVzA8QLpIMKSFIaRm",
            "Content-Type": "application/json; charset=utf-8",
            # 请注意这个应该和配置文件中的host保持一致
            "Host": self.apis["host"],
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
        }

        # 默认正常的提交参数json
        params = {
            "formWid": self.formWid,
            "address": self.address,
            "collectWid": self.collectWid,
            "schoolTaskWid": self.schoolTaskWid,
            "form": self.form,
            "uaIsCpadaily": True,
        }

        logging.info("正在提交问卷")
        submitForm = "https://{host}/wec-counselor-collector-apps/stu/collector/submitForm".format(
            host=self.apis["host"]
        )
        r = self.session.post(url=submitForm, headers=headers, data=json.dumps(params))
        msg = r.json()["message"]
        if msg != "SUCCESS":
            logging.info("提交失败。。。")
            logging.info("错误是" + msg)
            raise Exception(msg)
        logging.info("提交成功! ")
        return msg
