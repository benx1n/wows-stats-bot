# wows-stats-bot
战舰世界水表查询插件，基于hoshinobot V2<br>
水表人，出击！wws me recent！！！

## 特点

- [x] 账号总体、单船、近期战绩
- [x] 全指令支持参数乱序
- [x] 快速切换绑定账号
- [x] 支持@快速查询

## 首次部署
>```
>以下部分以默认您成功部署并启动HoshinoBot和go-cqhttp，如未安装，请查看HoshinoBot仓库中的部署教程，本文附录中也收录了一些安装HoshinoBot时可能跟遇到的问题
>```
1. 在[HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot)的插件目录modules下clone本项目 `git clone https://github.com/benx1n/wows-stats-bot.git`
2. 在项目文件夹下执行`pip install -r requirements.txt`安装依赖
3. 将配置文件 `config_example.json` 拷贝一份后重命名为 `config.json` , 修改配置文件中的设置<br>
    >```
    >"token":"api_key:token"    //请加群联系雨季获取api_key和token
    >```
4. 在 `config/__bot__.py`的模块列表里加入 `wows-stats-bot.git`
5. 重启hoshinoBot
6. 发送wws help查看帮助，首次使用插件时playwright会自动下载chromium，可在控制台中查看进度

## 更新

1. 在项目文件夹下执行
    >```
    >git pull
    >```
2. 对比config_example中是否有新增配置项，同步至本地config
3. 重启hoshinobot

## 指令列表
向bot发送wws help即可查看
## 预览
好累啊待会再加吧
## DLC

- **私聊支持：（可能会引起其他插件部分功能异常）<br>**
    >修改Hoshinobot文件夹中`.\hoshino\priv.py`内check_priv函数，返回值改为True<br>
    >```
    >def check_priv(ev: CQEvent, require: int) -> bool:
    >if ev['message_type'] == 'group':
    >    return bool(get_user_priv(ev) >= require)
    >else:
    >    return True
    >```
    >注释Hoshinobot文件夹中`.\hoshino\msghandler.py`内下方代码<br>
    >```
    >if event.detail_type != 'group':
    >    return
    >```
        >修改Hoshinobot文件夹中`.\hoshino\service.py`内on_message函数,将event='group'及结尾的event替换为*events<br>
    >```
    >def on_message(self, *events) -> Callable:
    >def deco(func) -> Callable:
    >    @wraps(func)
    >    async def wrapper(ctx):
    >        if self._check_all(ctx):
    >            try:
    >                return await func(self.bot, ctx)
    >            except Exception as e:
    >                self.logger.error(f'{type(e)} occured when {func.__name__} handling message {ctx["message_id"]}.')
    >                self.logger.exception(e)
    >            return
    >    return self.bot.on_message(*events)(wrapper)
    >return deco
    >```

## HoshinoBot安装报错解决
1. 请使用python 3.8，更高版本可能不兼容部分依赖，请自行寻找解决办法
2. windows下出现如下报错，请下载vs生成工具，选择工作负荷-使用C++的桌面开发
>```
>error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
>```