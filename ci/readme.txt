这个文件仅打包了Hikari Bot，仍需要自行配置go-cqhttp以运行bot

1. 编辑wwsbotconfig.json，替换申请到的token,格式为token: "api_key:token"
2. 编辑hoshino_config.py，可以修改端口号超级管理员等
3. 双击exe运行bot，注意bot会读取当前工作目录的2个配置文件
注意：你仍需要运行go-cqhttp完整启动bot