import os

import requests


def get_pic(apikey):
    res = requests.get(url="https://api.lolicon.app/setu/?apikey={apikey}".format(apikey=apikey))
    return res.json()

def download_pic(apikey):
    os.makedirs('./image/', exist_ok=True)
    IMAGE_URL = get_pic(apikey)['data'][0]['url']
    IMAGE_NAME = './image/' + IMAGE_URL.split('/')[-1]
    r = requests.get(IMAGE_URL)
    with open(IMAGE_NAME, 'wb') as f:
        f.write(r.content)
    return IMAGE_NAME
