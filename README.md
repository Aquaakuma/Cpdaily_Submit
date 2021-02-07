# AutoSubmit  

通过使用Github的Actions功能完成今日校园疫情信息收集自动打卡签到，[auto-submit](https://github.com/ZimoLoveShuang/auto-submit) 项目的Action版本。

## 前提条件
- [x] Github账号
- [x] Server酱的SCKEY

## 使用说明

1. **在右上角Fork本项目**  
2. **启用Actions**
3. **编辑要提交的问题**
   根据个人情况修改 config.yml 中的内容。
   如果不懂如何配置请用 [auto-submit](https://github.com/ZimoLoveShuang/auto-submit) 项目中的 generate.py 生成一个配置文件。
4. **获取sckey，推送每日运行结果**  
   1. 前往 [sc.ftqq.com](http://sc.ftqq.com/3.version) 点击登入，创建账号（建议使用 GitHub 登录）。
   2. 点击[发送消息](http://sc.ftqq.com/?c=code) ，生成一个 Key。之后会将其增加到 Github Secrets 中，变量名为 `sckey`
   3. [绑定微信账号](http://sc.ftqq.com/?c=wechat&a=bind) ，开启微信推送。  ![图示]()
5. **点击项目 Settings -> Secrets -> New repository secrets 逐个添加以下 Secrets，其中server酱微信推送的sckey可见上一步**  
   |Name|Value|
   |-----|-----|
   | username | 学号 |
   | password | 新信息门户密码 |
   | address | 定位地址 |
   | school | 学校 |
   | sckey | server酱推送的sckey |  

   ![图示](https://github.com/TUT123456/Cpdaily_Submit/docs/imgs/secret.png)
5. **运行结果将在每天15点左右通过微信的server酱通知给您**  
   ![图示](https://github.com/TUT123456/Cpdaily_Submit/docs/imgs/result.jpg)

## 其他
   - 本脚本根据 [auto-submit](https://github.com/ZimoLoveShuang/auto-submit) 云函数代码修改而来，所以原项目中能用云函数实现签到的情况在这里应该适用。
   - 脚本中只提供了Server酱的推送方式，因为我觉得这种方式简单方便，如果想用其他推送方式，如邮箱推送，可以参考 auto-submit。
   - 默认每天0点(UTC时区，即北京时间8点。)签到，可以到 [`.github/workflows/python_auto.yml`](https://github.com/TUT123456/Cpdaily_Submit/blob/77c5810562005bde2dba37306deb99ad057d6d17/.github/workflows/python_auto.yml#L12) 修改，cron格式，第二位数字代表当天时间，以此类推。
## 致谢

@ZimoLoveShuang/auto-submit 提供签到代码
@qdddz/HFUT_AutoSubmit 提供Action思路
