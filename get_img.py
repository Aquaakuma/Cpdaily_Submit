import logging
import os

import requests


def get_pic(apikey):
    logging.info('获取图片链接')
    res = requests.get(url="https://api.lolicon.app/setu/?apikey={apikey}".format(apikey=apikey))
    return res.json()

def download_pic(apikey):
    logging.info('下载图片')
    os.makedirs('./image/', exist_ok=True)
    IMAGE_URL = get_pic(apikey)['data'][0]['url']
    IMAGE_PATH = './image/' + 'sendPic' + '.' + IMAGE_URL.split('.')[-1]
    r = requests.get(IMAGE_URL)
    with open(IMAGE_PATH, 'wb') as f:
        f.write(r.content)
    logging.info('下载成功')
    return IMAGE_PATH
