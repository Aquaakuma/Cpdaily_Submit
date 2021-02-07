# HFUT_AutoSubmit  

通过使用Github的Actions功能完成的合肥工业大学今日校园疫情信息收集自动打卡签到（针对2021年1月后启用的每日打卡保平安）

## 使用说明

1. **在右上角Fork本项目**  
   ![图示](https://cdn.jsdelivr.net/gh/qdddz/HFUT_AutoSubmit/docs/imgs/fork.jpg)  
2. **启用Actions**  
   1. 点击上方Actions按钮，并且启用
   ![图示](https://cdn.jsdelivr.net/gh/qdddz/HFUT_AutoSubmit/docs/imgs/actions1.jpg)  
   2. 启用Workflow
   ![图示](https://cdn.jsdelivr.net/gh/qdddz/HFUT_AutoSubmit/docs/imgs/actions2.jpg)  
3. **获取sckey，推送每日运行结果**  
   1. 前往 [sc.ftqq.com](http://sc.ftqq.com/3.version) 点击登入，创建账号（建议使用 GitHub 登录）。
   2. 点击[发送消息](http://sc.ftqq.com/?c=code) ，生成一个 Key。之后会将其增加到 Github Secrets 中，变量名为 `sckey`
   3. [绑定微信账号](http://sc.ftqq.com/?c=wechat&a=bind) ，开启微信推送。  ![图示](https://cdn.jsdelivr.net/gh/qdddz/HFUT_AutoSubmit/docs/imgs/serverpush.jpg)
4. **点击项目 Settings -> Secrets -> New Secrets 添加以下 3 个 Secrets，其中server酱微信推送的sckey可见上一步**  
   |Name|Value|
   |-----|-----|
   | username | 学号 |
   | password | 新信息门户密码 |
   | sckey | server酱推送的sckey |  

   ![图示](https://cdn.jsdelivr.net/gh/qdddz/HFUT_AutoSubmit/docs/imgs/secret.jpg)
5. **运行结果将在每天15点左右通过微信的server酱通知给您**  
   ![图示](https://cdn.jsdelivr.net/gh/qdddz/HFUT_AutoSubmit/docs/imgs/result.jpg)

## 后记  

1. 这破系统如果正常发requests请求要经过好几道验证，实属搞不来，只能用浏览器自动化这种蠢办法，如果有网安大佬带带我最好了！
2. 如果上面的图片无法正常加载，纯属github被墙了。。
3. 有问题请反馈至QQ：710830913

## 致谢

@JunzhouLiu/BILIBILI-HELPER 提供Action思路
