<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <a href="https://github.com/benx1n/HikariBot"><img src="https://s2.loli.net/2022/05/28/SFsER8m6TL7jwJ2.png" alt="Hikari " style="width:200px; height:200px" ></a>
</p>

<div align="center">

# Hikari

<!-- prettier-ignore-start -->
<!-- markdownlint-disable-next-line MD036 -->
战舰世界水表BOT
<!-- prettier-ignore-end -->

</div>

<p align="center">
  <a href="https://pypi.python.org/pypi/hikari-bot">
    <img src="https://img.shields.io/pypi/v/hikari-bot" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.8.0+-blue" alt="python">
  <a href="https://jq.qq.com/?_wv=1027&k=S2WcTKi5">
    <img src="https://img.shields.io/badge/QQ%E7%BE%A4-967546463-orange?style=flat-square" alt="QQ Chat Group">
  </a>
</p>

## 简介
战舰世界水表查询插件，基于hoshinobot V2<br>
水表人，出击！wws me recent！！！<br>
如果觉得本插件还不错的话请点个Star哦~<br>
Nonebot2版：[Hikari](https://github.com/benx1n/HikariBot)——更易部署的战绩Bot，如果您没有一定的python基础请点击链接，搭建该Bot
## 特点

- [x] 账号总体、单船、近期战绩
- [x] 全指令支持参数乱序
- [x] 快速切换绑定账号
- [x] 支持@快速查询
- [x] 全异步，高并发下性能更优
## 一键使用
1. 下载[最新Release](https://github.com/benx1n/wows-stats-bot/releases/download/Latest/release_windows.zip)中的压缩包，按流程走
## 完整安装（首次部署Hoshino）
>
>以下部分将教你如何通过conda或Docker用以避免部署Hoshino时可能遇到的问题<br>
>如果您已经成功运行Hohisno，请跳过此节转到插件部署
>
>注：本插件不支持Centos！
>
### Windows系统
1. 下载[notepad++](https://notepad-plus-plus.org/downloads/)和[Git](https://git-scm.com/download/win)并安装
2. 打开一个合适的文件夹，鼠标右键——Git Bash here，输入以下命令克隆Hoshino仓库
    ```
    git clone https://github.com/Ice-Cirno/HoshinoBot.git
    ```
3. 进入`hoshinio`文件夹，将`config_example`文件夹复制一份，并重命名为`config`,然后右键使用Notepad++打开其中的`__bot__.py`，按照其中的注释说明进行编辑。
    >请在SUPERUSERS中添加你的QQ号
    >
    >如果您不清楚某项设置的作用，请保持默认。

3. 下载[Miniconda](https://docs.conda.io/en/latest/miniconda.html)
    >Conda是一个优秀的包、环境管理器，通过它你可以快速创建或切换不同版本的python环境，本文仅通过Conda创建python环境，不做包管理用

4. 双击Miniconda，安装时请选择如下配置
    >`Just Me`
    >
    >`保持默认路径`
    >
    >`不要`勾选“Add Anaconda to my PATH environment variable”

5. 安装完成后，开始菜单——右键点击Anaconda Prompt → 以管理员身份运行”，在Anaconda Prompt中输入 conda list ，可以查看已经安装的包名和版本号。若结果可以正常显示，则说明安装成功

6. 在Anaconda Prompt逐条以下命令
    ```
    conda config --add channels http://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/
    conda config --add channels http://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/msys2/
    conda config --add channels http://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
    conda config --set ssl_verify false
    conda config --remove channels defaults
    conda create --name py3.8 python=3.8
    输入Y确认安装
    ```
7. 完成上述步骤后，您现在通过`conda env list`应该已经可以看到创建了一个名为py3.8的虚拟环境，请继续执行以下步骤
    ```
    activate py3.8
    cd 您的Hoshino根目录
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```
    >您的Hoshino根目录即为存在requirements.txt的文件夹（Windows可以通过右键标题栏，将地址复制为文本）
    >
    >若此处有报错信息，请务必解决，大部分错误可通过本文结尾附录查找对应解决办法，如没有请提 issue或自行百度

8. 输入以下命令，启动 HoshinoBot
    ```
    python run.py
    ```
    > 若能看到日志`INFO: Running on 127.0.0.1:8080`，说明HoshinoBot启动成功。您可以忽略启动时的WARNING信息。如果出现ERROR，说明部分功能可能加载失败。

    至此，HoshinoBot的“大脑”已部署成功。接下来我们需要部署无头qq客户端，作为HoshinoBot的“口”和“耳”，收发消息。

9. 下载 go-cqhttp 至合适的文件夹

    - github 发布页：https://github.com/Mrs4s/go-cqhttp/releases

    > 您需要根据自己的机器架构选择版本，Windows一般为x86/64架构，通常选择[go-cqhttp_windows_386.exe](https://github.com/Mrs4s/go-cqhttp/releases/download/v1.0.0-rc1/go-cqhttp_windows_386.exe)

10. 双击go-cqhttp，提示释出bat，重新运行bat，选择websocket反向代理，go-cqhttp将会在同文件夹内自动创建一个`config.yml`，右键使用notepad++打开，根据注释填写QQ账号密码，并将以下内容写入文件结尾：

    ```yaml
      - ws-reverse:
          universal: ws://127.0.0.1:8080/ws/
          reconnect-interval: 5000
          middlewares:
            <<: *default
    ```
    
    > 关于go-cqhttp的配置，你可以在[这里](https://docs.go-cqhttp.org/guide/config.html#%E9%85%8D%E7%BD%AE%E4%BF%A1%E6%81%AF)找到更多说明。

11. 启动go-cqhttp，按照提示登录。

    登陆成功后，私聊机器人发送`在？`，若机器人有回复，恭喜您，您已经成功搭建起HoshinoBot了！
    
    注意，此时您的机器人功能还不完全，部分功能可能无法正常工作。若希望您的机器人可以发送图片，或使用其他进阶功能，请参考Hoshino仓库中的说明。

## 首次部署插件（以conda环境为例）
1. 打开Anaconda Prompt
    ```
    cd 插件目录
    git clone https://github.com/benx1n/wows-stats-bot.git
    cd wows-stats-bot
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    ```
    >您的插件目录即为`HoshinoBot/hoshino/moudles`（Windows可以通过右键标题栏，将地址复制为文本）
    >
    >若此处有报错信息，请务必解决，大部分错误可通过本文结尾附录查找对应解决办法，如没有请提 issue或自行百度

3. 将配置文件 `config_example.json` 拷贝一份后重命名为 `config.json` , 修改配置文件中的设置<br>
    ```
    "token":"api_key:token"    //请加群联系雨季获取api_key和token api_key即您申请TOKEN时使用的QQ号，token即回复您的邮件
    ```
    >总之最后应该长这样
   >
   >"token":"123764323:ba1f2511fc30423bdbb183fe33"
4. 在 `config/__bot__.py`的模块列表里加入 `wows-stats-bot`’

5. 在Anaconda Prompt中重启hoshinoBot（您可以使用多次敲击ctrl+C结束进程，并通过方向键上快速选择上一次的启动命令）
    >若此处有关于wos-stats-bot的报错信息，请自行百度或加群联系，理论上按步骤走下来这里可以直接通过

6. 在群聊中发送wws help查看帮助，首次使用插件时playwright会自动下载chromium，可在控制台中查看进度

## 更新

1. 在项目文件夹下执行
    >```
    >git pull
    >pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    >```
2. 对比config_example中是否有新增配置项，同步至本地config

3. 重启hoshinobot
    >若您是使用conda安装的hoshino，则重启步骤为
    >```
    >在Anaconda Prompt 中ctrl+C 结束进程
    >输入python run.py
    >```

## 指令列表
向bot发送wws help即可查看
## 预览
好累啊待会再加吧
## DLC

- **私聊支持：（可能会引起其他插件部分功能异常）<br>**
    >修改Hoshinobot文件夹中`.\hoshino\priv.py`内check_priv函数，返回值改为True
    >
    >```
    >def check_priv(ev: CQEvent, require: int) -> bool:
    >if ev['message_type'] == 'group':
    >    return bool(get_user_priv(ev) >= require)
    >else:
    >    return True
    >```
    >注释Hoshinobot文件夹中`.\hoshino\msghandler.py`内下方代码
    >
    >```
    >if event.detail_type != 'group':
    >    return
    >```
        >修改Hoshinobot文件夹中`.\hoshino\service.py`内on_message函数,将event='group'及结尾的event替换为*events
    >
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
1. 请使用python 3.8，更高版本可能不兼容部分依赖，若不按本文使用conda部署请自行寻找解决办法
2. linux 安装依赖时请带上sudo
2. pip install时出现SSL ERROR，请关闭您的本地代理工具（科学上网）或切换至PAC模式
3. windows下出现如下报错，请下载vs生成工具，选择工作负荷-使用C++的桌面开发
    ```
    error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
    ```
4. 使用pypi和清华镜像安装依赖都不成功时先尝试更换阿里源`pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`
5. 出现如下报错，首先请输入pip show markupsafe，如果提示本地存在，尝试重新安装低版本的包`pip install markupsafe==2.0.1`
    ```
    can not import name 'soft_unicode' from 'markupsafe'
    ```

6. 出现如下报错，首先请输入`pip uninstall werkzeug`，重新安装最新版本依赖`pip install werkzeug`
    ```
    no moudle named 'werkzeug.sansio'
    ```

### Recent和绑定提示'鉴权失败'
1. 检查Token是否配置正确，token格式为`XXXXX:XXXXXX`
2. 如果配置正确可能是Token失效了，请重新申请
## 感谢

[HoshinoBot](https://github.com/Ice-Cirno/HoshinoBot)<br>
[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)<br>
[战舰世界API平台](https://wows.shinoaki.com/)<br>

## 开源协议

GPL-3.0 License
