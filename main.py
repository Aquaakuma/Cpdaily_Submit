import logging
from collector import Collector
from attendance import Attendance
import yaml
import click
from notification import notification


# 读取yml配置
def getYmlConfig(yaml_file):
    file = open(yaml_file, "r", encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)


# 提供给腾讯云函数调用的启动函数
@click.command()
@click.option("--config", default="./config.yml", help="配置文件")
@click.option("--generate", "-g", is_flag=True, help="生成表单")
@click.option("--attendance", "-a", is_flag=True, help="查寝")
@click.option("--collector", "-c", is_flag=True, help="普通收集")
def main(config, generate, attendance, collector):
    config = getYmlConfig(yaml_file=config)
    smtp = config["SMTP"]
    send = notification(**smtp)

    if attendance:
        for user in config["users"]:
            cpdaily = Attendance(
                username=user["user"]["username"],
                password=user["user"]["password"],
                address=user["user"]["address"],
                school=user["user"]["school"],
                lon=user["user"]["lon"],
                lat=user["user"]["lat"],
                photo=user["user"]["photo"],
                abnormalReason=user["user"]["abnormalReason"],
            )
            try:
                msg = cpdaily.getUnSignedTasks().getDetailTask().fillForm().signIn()
                send.sendQmail(email=user["user"]["email"], title=msg, content="这是我老婆")
            except Exception as e:
                send.sendQmail(
                    email=user["user"]["email"], title=str(e), content="这是我老婆"
                )
                pass
    elif collector:
        for user in config["users"]:
            cpdaily = Collector(
                username=user["user"]["username"],
                password=user["user"]["password"],
                address=user["user"]["address"],
                lon=user["user"]["lon"],
                lat=user["user"]["lat"],
                school=user["user"]["school"],
                photo=user["user"]["photo"],
            )
            try:
                msg = cpdaily.queryForm().fillForm(config["cpdaily"]).submitForm()
                send.sendQmail(email=user["user"]["email"], title=msg, content="这是我老婆")
            except Exception as e:
                send.sendQmail(
                    email=user["user"]["email"], title=str(e), content="这是我老婆"
                )
                pass
    elif generate:
        for user in config["users"]:
            cpdaily = Collector(
                username=user["user"]["username"],
                password=user["user"]["password"],
                address=user["user"]["address"],
                school=user["user"]["school"],
                photo=user["user"]["photo"],
            )
            cpdaily.queryForm().generate()


if __name__ == "__main__":
    main()