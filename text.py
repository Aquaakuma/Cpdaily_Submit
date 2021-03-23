import yaml
from login import Cpdaily


# 读取yml配置
def getYmlConfig(yaml_file):
    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)


# 全局配置
config = getYmlConfig(yaml_file='config.yml')

submitForm = Cpdaily(
    username = config['users'][0]['user']['username'], 
    password = config['users'][0]['user']['password'], 
    email = config['users'][0]['user']['email'], 
    address = config['users'][0]['user']['address'], 
    school = config['users'][0]['user']['school'],
    lon = config['users'][0]['user']['lon'],
    lat = config['users'][0]['user']['lat'],
    photo = config['users'][0]['user']['photo'],
    abnormalReason = config['users'][0]['user']['abnormalReason']
)

print(submitForm.session)

fileName = submitForm.uploadPicture("https://fafu.campusphere.net/wec-counselor-sign-apps/stu/oss/getUploadPolicy", './photo.jpg')
submitForm.getPictureUrl("https://fafu.campusphere.net/wec-counselor-sign-apps/stu/sign/previewAttachment", fileName)