# =================配置区start===================
# 学习通账号密码
user_info = {'username': '',
             'password': '',
             'schoolid': ''  # 学号登录才需要填写
             }
# server酱
# 申请地址http://sc.ftqq.com/3.version
server_chan_sckey = ''
server_chan = {
    'status': True,  # 如果关闭server酱功能，请改为False
    'url': 'https://sc.ftqq.com/{}.send'.format(server_chan_sckey)
}
# Telegram bot
telegram_bot_token = ''
telegram_user_id = ''
telegram_push = {
    'status': True,
    'url': 'https://api.telegram.org/bot{}/sendMessage?chat_id={}&text='.format(telegram_bot_token, telegram_user_id)
}
# 学习通账号cookies缓存文件路径
cookies_path = "./"
cookies_file_path = cookies_path + "cookies.json"
# activeid保存文件路径
activeid_path = "./"
activeid_file_path = activeid_path + "activeid.json"

IMAGE_PATH = "./img"

clientip = "1.1.1.1"
latitude = "-1"
longitude = "-1"
address = "中国"
# =================配置区end===================
