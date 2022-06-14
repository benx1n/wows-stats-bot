"""这是一份实例配置文件
"""

# hoshino监听的端口与ip
PORT = 8080
# HOST = '127.0.0.1'          # 本地部署使用此条配置（QQ客户端和bot端运行在同一台计算机）
HOST = '0.0.0.0'          # 开放公网访问使用此条配置（不安全）

DEBUG = False               # 调试模式

BLACK_LIST = [1974906693]   # 黑名单，权限为 BLACK = -999
WHITE_LIST = []             # 白名单，权限为 WHITE = 51
SUPERUSERS = [10000]        # 填写超级用户的QQ号，可填多个用半角逗号","隔开，权限为 SUPERUSER = 999
NICKNAME = ''               # 机器人的昵称。呼叫昵称等同于@bot，可用元组配置多个昵称

COMMAND_START = {''}        # 命令前缀（空字符串匹配任何消息）
COMMAND_SEP = set()         # 命令分隔符（hoshino不需要该特性，保持为set()即可）


# 启用的模块(打包的bot无法添加模块！可以启用或禁用模块)
MODULES_ON = {
    # 'botmanage',
    'groupmaster',
    'wows-stats-bot'
}
