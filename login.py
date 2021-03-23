# -*- coding: utf-8 -*-

import base64
import json
import logging
import uuid
from urllib.parse import urlparse

import oss2
import requests
from pyDes import CBC, PAD_PKCS5, des
from retrying import retry


class lazyproperty:
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        if instance is None:
            return self
        else:
            value = self.func(instance)
            setattr(instance, self.func.__name__, value)
            return value


class Cpdaily(object):
    api = "http://www.zimo.wiki:8080/wisedu-unified-login-api-v1.0/api/login"

    logging.basicConfig(format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',
                level=logging.INFO)

    def __init__(self, username, password, email, school, address, lon='', lat='', photo='', abnormalReason=''):
        self.username = username
        self.password = password
        self.email = email
        self.school = school
        self.address = address
        self.lon = lon
        self.lat = lat
        self.abnormalReason = abnormalReason
        self.photo = photo


    # 获取今日校园api
    @lazyproperty
    def apis(self):
        apis = {}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36 Edg/89.0.774.54",
            "Host": "mobile.campushoy.com"
        }
        schools = requests.get(
            url='https://mobile.campushoy.com/v6/config/guest/tenant/list', headers=headers).json()['data']
        flag = True
        for one in schools:
            if one['name'] == self.school:
                if one['joinType'] == 'NONE':
                    logging.info(self.school + ' 未加入今日校园')
                    exit(-1)
                flag = False
                params = {
                    'ids': one['id']
                }
                res = requests.get(url='https://mobile.campushoy.com/v6/config/guest/tenant/info', params=params, headers=headers)
                data = res.json()['data'][0]
                # joinType = data['joinType']
                idsUrl = data['idsUrl']
                ampUrl = data['ampUrl']
                if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
                    parse = urlparse(ampUrl)
                    host = parse.netloc
                    res = requests.get(parse.scheme + '://' + host)
                    parse = urlparse(res.url)
                    apis[
                        'login-url'] = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                    apis['host'] = host

                ampUrl2 = data['ampUrl2']
                if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
                    parse = urlparse(ampUrl2)
                    host = parse.netloc
                    res = requests.get(parse.scheme + '://' + host)
                    parse = urlparse(res.url)
                    apis[
                        'login-url'] = idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                    apis['host'] = host
                break
        if flag:
            logging.info(self.school + ' 未找到该院校信息，请检查是否是学校全称错误')
            exit(-1)
        logging.info(apis)
        return apis


    # 如果没有session, 重试
    def retry_if_vaule_error(exception): 
        if isinstance(exception, BaseException):
            logging.info("失败，重试中。。。")
        return isinstance(exception, BaseException)

    # 登陆并返回session
    @lazyproperty
    @retry(stop_max_attempt_number=5, retry_on_exception=retry_if_vaule_error)
    def session(self):

        params = {
            'login_url': self.apis['login-url'],
            'password': self.password,
            'username': self.username
            
        }

        cookies = {}
        # 借助上一个项目开放出来的登陆API，模拟登陆
        logging.info("尝试登陆中。。。")
        res = requests.post(self.api, params=params)
        cookieStr = str(res.json()['cookies'])
        logging.info(cookieStr)
        if cookieStr == 'None':
            logging.info(res.json())
            raise Exception("登录失败，原因可能是学号或密码错误，请检查配置后，重启脚本。。。")
        
        logging.info("登录成功。。。")
        # 解析cookie
        for line in cookieStr.split(';'):
            name, value = line.strip().split('=', 1)
            cookies[name] = value
        session = requests.session()
        session.cookies = requests.utils.cookiejar_from_dict(cookies)
        return session

    # 提交图片的处理
    # 上传图片到阿里云oss
    @retry(stop_max_attempt_number=5, retry_on_exception=retry_if_vaule_error)
    def uploadPicture(self, url, image):
        session = self.session
        res = session.post(url=url, headers={
                        'content-type': 'application/json'}, data=json.dumps({'fileType':1}))
        datas = res.json().get('datas')
        #log(datas)
        #new_api_upload
        fileName = datas.get('fileName') + '.png'
        accessKeyId = datas.get('accessid')
        xhost = datas.get('host')
        xpolicy = datas.get('policy')
        signature = datas.get('signature')
        #new_api_upload
        #new_api_upload2
        url = xhost + '/'
        data={
            'key':fileName,
            'policy':xpolicy,
            'OSSAccessKeyId':accessKeyId,
            'success_action_status':'200',
            'signature':signature
        }
        data_file = {
            'file':('blob',open(image,'rb'),'image/jpg')
        }
        res =  session.post(url=url,data=data,files=data_file)
        if(res.status_code == requests.codes.ok):
            return fileName
        #new_api_upload2
        #log(res)
        return ''


    # 获取图片上传位置
    @retry(stop_max_attempt_number=5, retry_on_exception=retry_if_vaule_error)
    def getPictureUrl(self, url, fileName):
        data = {
            'ossKey': fileName
        }
        res = self.session.post(url=url, headers={'content-type': 'application/json'}, data=json.dumps(data))
        photoUrl = res.json().get('datas')
        return photoUrl
    
    # 今日校园的DES加解密
    # DES加密
    def DESEncrypt(self, s, key='b3L26XNL'):
        key = key
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        encrypt_str = k.encrypt(s)
        return base64.b64encode(encrypt_str).decode()


    # DES解密
    def DESDecrypt(self, s, key='b3L26XNL'):
        s = base64.b64decode(s)
        iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
        return k.decrypt(s)


    # 普通收集的查询、填写、提交
    # 查询表单
    @retry(stop_max_attempt_number=5, retry_on_exception=retry_if_vaule_error)
    def queryForm(self):
        host = self.apis['host']
        session = self.session
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; OPPO R11 Plus Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 yiban/8.1.11 cpdaily/8.1.11 wisedu/8.1.11',
            'content-type': 'application/json',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,en-US;q=0.8',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        queryCollectWidUrl = 'https://{host}/wec-counselor-collector-apps/stu/collector/queryCollectorProcessingList'.format(
            host=host)
        params = {
            'pageSize': 6,
            'pageNumber': 1
        }
        logging.info('正在查询最新待填写问卷。。。')
        res = session.post(queryCollectWidUrl, headers=headers,
                        data=json.dumps(params))
        if len(res.json()['datas']['rows']) < 1:
            logging.info('没有新问卷')
            return None

        logging.info('找到新问卷')
        collectWid = res.json()['datas']['rows'][0]['wid']
        formWid = res.json()['datas']['rows'][0]['formWid']

        detailCollector = 'https://{host}/wec-counselor-collector-apps/stu/collector/detailCollector'.format(
            host=host)
        res = session.post(url=detailCollector, headers=headers,
                        data=json.dumps({"collectorWid": collectWid}))
        schoolTaskWid = res.json()['datas']['collector']['schoolTaskWid']

        getFormFields = 'https://{host}/wec-counselor-collector-apps/stu/collector/getFormFields'.format(
            host=host)
        res = session.post(url=getFormFields, headers=headers, data=json.dumps(
            {"pageSize": 100, "pageNumber": 1, "formWid": formWid, "collectorWid": collectWid}))

        form = res.json()['datas']['rows']
        return {'collectWid': collectWid, 'formWid': formWid, 'schoolTaskWid': schoolTaskWid, 'form': form}


    # 填写form
    def fillForm(self, form):
        sort = 1
        Form = self.queryForm()
        if Form == None:
            raise Exception("填写问卷失败，可能是辅导员没有发布！")
        else:
            logging.info('找到新问卷，开始填写。。。')

        for formItem in Form['form'][:]:
            # 只处理必填项
            if formItem['isRequired'] == 1:
                default = form['defaults'][sort - 1]['default']
                if formItem['title'] != default['title']:
                    logging.info('第%d个默认配置不正确，请检查' % sort)
                    raise Exception("第%d个默认配置不正确，请检查")
                # 文本直接赋值
                if formItem['fieldType'] == 1 or formItem['fieldType'] == 5:
                    formItem['value'] = default['value']
                # 单选框需要删掉多余的选项
                if formItem['fieldType'] == 2:
                    # 填充默认值
                    formItem['value'] = default['value']
                    fieldItems = formItem['fieldItems']
                    for i in range(0, len(fieldItems))[::-1]:
                        if fieldItems[i]['content'] != default['value']:
                            del fieldItems[i]
                # 多选需要分割默认选项值，并且删掉无用的其他选项
                if formItem['fieldType'] == 3:
                    fieldItems = formItem['fieldItems']
                    defaultValues = default['value'].split(',')
                    for i in range(0, len(fieldItems))[::-1]:
                        flag = True
                        for j in range(0, len(defaultValues))[::-1]:
                            if fieldItems[i]['content'] == defaultValues[j]:
                                # 填充默认值
                                formItem['value'] += defaultValues[j] + ' '
                                flag = False
                        if flag:
                            del fieldItems[i]
                # 图片需要上传到阿里云oss
                if formItem['fieldType'] == 4:
                    fileName = self.uploadPicture(url="https://{host}/wec-counselor-sign-apps/stu/oss/getUploadPolicy".format(host=self.apis['host']), image=self.photo)
                    formItem['value'] = self.getPictureUrl(url="https://{host}/wec-counselor-sign-apps/stu/sign/previewAttachment".format(host=self.apis['host']), fileName=fileName)
                logging.info('必填问题%d：' % sort + formItem['title'])
                logging.info('答案%d：' % sort + formItem['value'])
                sort += 1
            else:
                Form['form'].remove(formItem)
        logging.info('填写成功')
        return Form

    # 提交表单
    def submitForm(self, form):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; OPPO R11 Plus Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 okhttp/3.12.4',
            'CpdailyStandAlone': '0',
            'extension': '1',
            'Cpdaily-Extension': 'Ew9uONYq03Siz+VLCzZ4RiWRaXXBubIGc1d7ecaS2YmSDf1+elDL0gdwAw977HbPzvgR3pkeyW3djmnPOMxYro3Tps7PNmLoqfNTAECZqcM1LAyx+2zTfDExNa4yDWs83AyTnSKXs7oHQvFOfXhKNY1OXVzIdnwOkgaNw7XxzM1+2efCWAJgUBoHNV3n3MayLqOwPvSCvBke+SHC/Hy/53+ehU9A1lst6JlpGiFhlEOUybo5s5/o+b/XLUexuEE50IQgdPL4Hi4vPe4yVzA8QLpIMKSFIaRm',
            'Content-Type': 'application/json; charset=utf-8',
            # 请注意这个应该和配置文件中的host保持一致
            'Host': self.apis['host'],
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }

        Form = self.fillForm(form)

        # 默认正常的提交参数json
        params = {"formWid": Form['formWid'], "address": self.address, "collectWid": Form['collectWid'], "schoolTaskWid": Form['schoolTaskWid'],
                    "form": Form['form'],"uaIsCpadaily":True}
        # print(params)
        submitForm = 'https://{host}/wec-counselor-collector-apps/stu/collector/submitForm'.format(
            host=self.apis['host'])
        logging.info('正在提交问卷')
        r = self.session.post(url=submitForm, headers=headers,
                            data=json.dumps(params))
        msg = r.json()['message']
        return msg

 
    # 查寝的获取、填写、提交
    # 获取最新未签到任务
    @retry(stop_max_attempt_number=5, retry_on_exception=retry_if_vaule_error)
    def getUnSignedTasks(self):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'content-type': 'application/json',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,en-US;q=0.8',
            'Content-Type': 'application/json;charset=UTF-8'
        }
        logging.info('正在获取签到任务')
        # 第一次请求每日签到任务接口，主要是为了获取MOD_AUTH_CAS
        res = self.session.post(
            url='https://{host}/wec-counselor-attendance-apps/student/attendance/getStuAttendacesInOneDay'.format(
                host=self.apis['host']),
            headers=headers, data=json.dumps({}))
        # 第二次请求每日签到任务接口，拿到具体的签到任务
        res = self.session.post(
            url='https://{host}/wec-counselor-attendance-apps/student/attendance/getStuAttendacesInOneDay'.format(
                host=self.apis['host']),
            headers=headers, data=json.dumps({}))
        if len(res.json()['datas']['unSignedTasks']) < 1:
            logging.info('当前没有未签到任务')
            raise Exception('当前没有未签到任务')
        # log(res.json())
        latestTask = res.json()['datas']['unSignedTasks'][0]
        logging.info('获取成功')
        return {
            'signInstanceWid': latestTask['signInstanceWid'],
            'signWid': latestTask['signWid']
        }


    # 获取签到任务详情
    @retry(stop_max_attempt_number=5, retry_on_exception=retry_if_vaule_error)
    def getDetailTask(self):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
            'content-type': 'application/json',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Language': 'zh-CN,en-US;q=0.8',
            'Content-Type': 'application/json;charset=UTF-8'
        }

        params = self.getUnSignedTasks()
        logging.info('获取签到任务详情。。。')
        res = self.session.post(url='https://{host}/wec-counselor-attendance-apps/student/attendance/detailSignInstance'.format(
            host=self.apis['host']), headers=headers, data=json.dumps(params))
        data = res.json()['datas']
        logging.info('获取成功')
        return data


    # 填充表单
    def fillSignForm(self):
        task = self.getDetailTask()
        form = {}
        logging.info('正在填写签到表单!')
        form['signInstanceWid'] = task['signInstanceWid']
        form['longitude'] = self.lon
        form['latitude'] = self.lat
        form['isMalposition'] = task['isMalposition']
        # form['isMalposition'] = '1'
        form['abnormalReason'] = self.abnormalReason
        if task['isPhoto'] == 1:
            fileName = self.uploadPicture(url="https://{host}/wec-counselor-sign-apps/stu/oss/getUploadPolicy".format(host=self.apis['host']), image=self.photo)
            form['signPhotoUrl'] = self.getPictureUrl(url="https://{host}/wec-counselor-sign-apps/stu/sign/previewAttachment".format(host=self.apis['host']), fileName=fileName)
        else:
            form['signPhotoUrl'] = ''
        form['position'] = self.address
        form['qrUuid'] = ''
        form['uaIsCpadaily'] = True
        logging.info('填写成功')
        logging.info(form)
        return form
    
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
            "deviceId": str(uuid.uuid1())
        }
        headers = {
            # 'tenantId': apis['tenantId'],
            'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; PCRT00 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Mobile Safari/537.36 okhttp/3.8.1',
            'CpdailyStandAlone': '0',
            'extension': '1',
            # 'Cpdaily-Extension': '1wAXD2TvR72sQ8u+0Dw8Dr1Qo1jhbem8Nr+LOE6xdiqxKKuj5sXbDTrOWcaf v1X35UtZdUfxokyuIKD4mPPw5LwwsQXbVZ0Q+sXnuKEpPOtk2KDzQoQ89KVs gslxPICKmyfvEpl58eloAZSZpaLc3ifgciGw+PIdB6vOsm2H6KSbwD8FpjY3 3Tprn2s5jeHOp/3GcSdmiFLYwYXjBt7pwgd/ERR3HiBfCgGGTclquQz+tgjJ PdnDjA==',
            'Cpdaily-Extension': self.DESEncrypt(json.dumps(extension)),
            'Content-Type': 'application/json; charset=utf-8',
            'Host': self.apis['host'],
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
        }
        form = self.fillSignForm()
        # session.cookies.set('AUTHTGC', session.cookies.get('CASTGC'))
        logging.info('正在提交签到任务。。。')
        res = self.session.post(
            url='https://{host}/wec-counselor-attendance-apps/student/attendance/submitSign'.format(host=self.apis['host']),
            headers=headers, data=json.dumps(form))
        
        message = res.json()['message']
        if message != 'SUCCESS':
            raise Exception('自动查寝提交失败，原因是：' + message)
        logging.info('提交成功')
        
        return message

