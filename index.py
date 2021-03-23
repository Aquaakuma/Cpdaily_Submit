import logging

import yaml

from login import Cpdaily
from notification import notification


# 读取yml配置
def getYmlConfig(yaml_file):
    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)


# 全局配置
config = getYmlConfig(yaml_file='config.yml')



# 提供给腾讯云函数调用的启动函数
def main_handler(event, context):

    logging.basicConfig(format='%(asctime)s  %(filename)s : %(levelname)s  %(message)s',
                    level=logging.INFO)

    for user in config['users']:
        submitForm = Cpdaily(
            username = user['username'], 
            password = user['password'], 
            email = user['email'], 
            address = user['address'], 
            school = user['school'],
            lon = user['lon'],
            lat = user['lat'],
            photo = user['photo'],
            abnormalReason = user['abnormalReason']
        )
        smtp = config['SMTP']
        send = notification(**smtp)
        if event["Message"] == "普通收集":
            try:
                # 开始登录
                logging.info('当前用户：' + str(user['username']))
                form = config['cpdaily']
                msg = submitForm.submitForm(form)

                if msg == 'SUCCESS':
                    logging.info('自动提交成功！')
                elif msg == '该收集已填写无需再次填写':
                    logging.info('今日已提交！')
                    # InfoSubmit('今日已提交！')
                else:
                    logging.info('自动提交失败。。。')
                    logging.info('错误是' + msg)
                    raise Exception(msg)

            except Exception as e:
                send.sendQmail(user['email'], str(e), "以下是我的老婆")
                raise e
            
            send.sendQmail(user['email'], str(msg), "以下是我的老婆")
            return str(msg)
        
        elif event["Message"] == "查寝":
            try:
                # 开始登录
                logging.info('当前用户：' + str(user['username']))
                msg = submitForm.signIn()

                if msg == 'SUCCESS':
                    logging.info('签到成功！')
                else:
                    logging.info('签到失败。。。')
                    logging.info('错误是' + msg)
                    raise Exception(msg)

            except Exception as e:
                logging.info("错误：" + str(e))
                # send.sendQmail(user['email'], str(e), "以下是我的老婆")
                raise e
            
            # send.sendQmail(user['email'], str(msg), "以下是我的老婆")
            return str(msg)


# main_handler({

#     "Type": "timer",

#     "TriggerName": "EveryDay",

#     "Time": "2019-02-21T11:49:00Z",

#     "Message": "查寝"
# }, {})
