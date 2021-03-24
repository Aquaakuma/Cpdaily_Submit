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
        cpdaily = Cpdaily(
            username = user['user']['username'], 
            password = user['user']['password'], 
            email = user['user']['email'], 
            address = user['user']['address'], 
            school = user['user']['school'],
            lon = user['user']['lon'],
            lat = user['user']['lat'],
            photo = user['user']['photo'],
            abnormalReason = user['user']['abnormalReason']
        )
        smtp = config['SMTP']
        send = notification(**smtp)
        try:
            try:
                # 开始登录
                form = config['cpdaily']
                if event['Message'] == "普通收集":
                    msg = cpdaily.queryForm().fillForm(form).submitForm()
                elif event["Message"] == "查寝":
                    msg = cpdaily.getUnSignedTasks().getDetailTask().fillSignForm().signIn()

                if msg == 'SUCCESS':
                    logging.info('签到成功！')
                    msg = '签到成功'
                elif msg == '该收集已填写无需再次填写':
                    logging.info('今日已提交！')
                    msg = '今日已提交'
                    # InfoSubmit('今日已提交！')
                else:
                    logging.info('自动提交失败。。。')
                    logging.info('错误是' + msg)
                    raise Exception(msg)

            except Exception as e:
                # send.sendQmail(user['user']['email'], str(e), "以下是我的老婆")
                logging.info(str(e))
                raise e
            
            # send.sendQmail(user['user']['email'], str(msg), "以下是我的老婆")
            return str(msg)

        except:
            pass

main_handler(event={
    'Message': '查寝'
}, context={})