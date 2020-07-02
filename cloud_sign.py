import os
import time
import asyncio
import re
import json
import requests
import random
from config import *
from lxml import etree
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings()


class AutoSign(object):

    def __init__(self, username, password, schoolid=None):
        """初始化就进行登录"""
        self.headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.100 Safari/537.36'}
        self.session = requests.session()
        self.session.headers = self.headers
        self.username = username
        # 读取指定用户的cookies
        if self.check_cookies_status(username) is False:
            self.login(password, schoolid, username)
            self.save_cookies(username)

    def save_cookies(self, username):
        """保存cookies"""
        new_cookies = self.session.cookies.get_dict()
        with open(cookies_file_path, "r") as f:
            data = json.load(f)
            data[username] = new_cookies
            with open(cookies_file_path, 'w') as f2:
                json.dump(data, f2)

    def check_cookies_status(self, username):
        """检测json文件内是否存有cookies,有则检测，无则登录"""
        if "cookies.json" not in os.listdir(cookies_path):
            with open(cookies_file_path, 'w+') as f:
                f.write("{}")

        with open(cookies_file_path, 'r') as f:
            # json文件有无账号cookies, 没有，则直接返回假
            try:
                data = json.load(f)
                cookies = data[username]
            except Exception:
                return False

            # 找到后设置cookies
            cookies_jar = requests.utils.cookiejar_from_dict(cookies)
            self.session.cookies = cookies_jar

            # 检测cookies是否有效
            r = self.session.get(
                'http://mooc1-1.chaoxing.com/api/workTestPendingNew', allow_redirects=False)
            if r.status_code != 200:
                print("COOKIES CHECK FAIL | RETRY")
                return False
            else:
                if len(self.get_all_classid()) == 0:
                    print("COOKIES CHECK FAIL | RETRY")
                    return False
                print("COOKIES CHECK PASS")
                return True

    def login(self, password, schoolid, username):
        # 登录-手机邮箱登录
        if schoolid:
            r = self.session.post(
                'http://passport2.chaoxing.com/api/login?name={}&pwd={}&schoolid={}&verify=0'.format(username, password,
                                                                                                     schoolid))
            if json.loads(r.text)['result']:
                print("LOGIN SUCCESS")
            else:
                print("LOGIN FAIL | CHECK ACCOUNT INFO")

        else:
            r = self.session.get(
                'https://passport2.chaoxing.com/api/login?name={}&pwd={}&schoolid=&verify=0'.format(
                    username, password),
                headers=self.headers)
            if json.loads(r.text)['result']:
                print("LOGIN SUCCESS")
            else:
                print("LOGIN FAIL | CHECK ACCOUNT INFO")

    def check_activeid(self, activeid):
        """检测activeid是否存在，不存在则添加"""
        activeid += self.username
        if "activeid.json" not in os.listdir(activeid_path):
            with open(activeid_file_path, 'w+') as f:
                f.write("{}")

        with open(activeid_file_path, 'r') as f:
            try:
                # 读取文件
                data = json.load(f)
                if data[activeid]:
                    return True
            except:
                # 如果出错，则表示没有此activeid，添加此activeid
                with open(activeid_file_path, 'w') as f2:
                    data[activeid] = True
                    json.dump(data, f2)
                return False

    def get_all_classid(self) -> list:
        """获取课程主页中所有课程的classid和courseid"""
        print("GET CLASS INFO")
        res = []
        r = self.session.get(
            'http://mooc1-2.chaoxing.com/visit/interaction', headers=self.headers)
        soup = BeautifulSoup(r.text, "lxml")
        courseId_list = soup.find_all('input', attrs={'name': 'courseId'})
        classId_list = soup.find_all('input', attrs={'name': 'classId'})
        classname_list = soup.find_all('h3', class_="clearfix")
        for i, v in enumerate(courseId_list):
            res.append((v['value'], classId_list[i]['value'],
                        classname_list[i].find_next('a')['title']))
        # print(res)
        return res

    def get_token(self):
        """获取上传文件所需参数token"""
        url = 'https://pan-yz.chaoxing.com/api/token/uservalid'
        res = self.session.get(url, headers=self.headers)
        token_dict = json.loads(res.text)
        return (token_dict['_token'])

    def upload_img(self):
        """上传图片"""
        # 从图片文件夹内随机选择一张图片
        try:
            all_img = os.listdir(IMAGE_PATH)
        except Exception as e:
            os.mkdir(IMAGE_PATH)
            all_img = 0

        if len(all_img) == 0:
            return "a5d588f7bce1994323c348982332e470"
        else:
            img = IMAGE_PATH + random.choice(all_img)
            uid = self.session.cookies.get_dict()['UID']
            url = 'https://pan-yz.chaoxing.com/upload'
            files = {'file': (img, open(img, 'rb'),
                              'image/webp,image/*',), }
            res = self.session.post(
                url,
                data={
                    'puid': uid,
                    '_token': self.get_token()},
                files=files,
                headers=self.headers)
            res_dict = json.loads(res.text)
            return (res_dict['objectId'])

    async def get_activeid(self, classid, courseid, classname):
        """访问任务面板获取课程的活动id"""
        # re_rule = r'<div class="Mct" onclick="activeDetail\((.*),2,null\)">[\s].*[\s].*[\s].*[\s].*<dd class="green">.*</dd>[\s]+[\s]</a>[\s]+</dl>[\s]+<div class="Mct_center wid660 fl">[\s]+<a href="javascript:;" shape="rect">(.*)</a>'
        re_rule = r'([\d]+),2'
        r = self.session.get(
            'https://mobilelearn.chaoxing.com/widget/pcpick/stu/index?courseId={}&jclassId={}'.format(
                courseid, classid), headers=self.headers, verify=False)
        # res = re.findall(re_rule, r.text)
        res = []
        h = etree.HTML(r.text)
        activeid_list = h.xpath('//*[@id="startList"]/div/div/@onclick')
        sign_type_list = h.xpath('//*[@id="startList"]/div/div/div/a/text()')
        for activeid, sign_type in zip(activeid_list, sign_type_list):
            activeid = re.findall(re_rule, activeid)
            if not activeid:
                continue
            res.append((activeid[0], sign_type))

        n = len(res)
        if n == 0:
            return None
        else:
            d = {'num': n, 'class': {}}
            for i in range(n):
                # 预防同一门课程多个签到任务的情况
                d['class'][i] = {
                    'classid': classid,
                    'courseid': courseid,
                    'activeid': res[i][0],
                    'classname': classname,
                    'sign_type': res[i][1]
                }
            return d

    def general_sign(self, classid, courseid, activeid):
        """普通签到"""
        print("CHECK IN")
        r = self.session.get(
            'https://mobilelearn.chaoxing.com/widget/sign/pcStuSignController/preSign?activeId={}&classId={}&fid=39037&courseId={}'.format(
                activeid, classid, courseid), headers=self.headers, verify=False)
        title = re.findall('<title>(.*)</title>', r.text)[0]
        if "签到成功" not in title:
            # 网页标题不含签到成功，则为拍照签到
            return self.tphoto_sign(activeid)
        else:
            sign_date = re.findall('<em id="st">(.*)</em>', r.text)[0]
            s = {
                'date': sign_date,
                'status': title
            }
            return s

    def hand_sign(self, classid, courseid, activeid):
        """手势签到"""
        print("HAND SIGN")
        hand_sign_url = "https://mobilelearn.chaoxing.com/widget/sign/pcStuSignController/signIn?&courseId={}&classId={}&activeId={}".format(
            courseid, classid, activeid)
        r = self.session.get(hand_sign_url, headers=self.headers, verify=False)
        title = re.findall('<title>(.*)</title>', r.text)
        sign_date = re.findall('<em id="st">(.*)</em>', r.text)[0]
        s = {
            'date': sign_date,
            'status': title
        }
        return s

    def qcode_sign(self, activeId):
        """二维码签到"""
        print("QCODE SIGN")
        params = {
            'name': '',
            'activeId': activeId,
            'uid': '',
            'useragent': '',
            'clientip': clientip,
            'latitude': latitude,
            'longitude': longitude,
            'fid': '',
            'appType': '15'
        }
        res = self.session.get(
            'https://mobilelearn.chaoxing.com/pptSign/stuSignajax', params=params)
        s = {
            'date': time.strftime("%m-%d %H:%M", time.localtime()),
            'status': res.text
        }
        return s

    def addr_sign(self, activeId):
        """位置签到"""
        print("LOCATION SIGN")
        params = {
            'name': '',
            'activeId': activeId,
            'address': address,
            'uid': '',
            'clientip': clientip,
            'latitude': latitude,
            'longitude': longitude,
            'fid': '',
            'appType': '15',
            'ifTiJiao': '1'
        }
        res = self.session.get(
            'https://mobilelearn.chaoxing.com/pptSign/stuSignajax', params=params)
        s = {
            'date': time.strftime("%m-%d %H:%M", time.localtime()),
            'status': res.text
        }
        return s

    def tphoto_sign(self, activeId):
        """拍照签到"""
        print("PHOTO SIGN")
        objectId = self.upload_img()
        params = {
            'name': '',
            'activeId': activeId,
            'address': address,
            'uid': '',
            'clientip': clientip,
            'latitude': latitude,
            'longitude': longitude,
            'fid': '',
            'appType': '15',
            'ifTiJiao': '1',
            'objectId': objectId
        }
        res = self.session.get(
            'https://mobilelearn.chaoxing.com/pptSign/stuSignajax', params=params)
        s = {
            'date': time.strftime("%m-%d %H:%M", time.localtime()),
            'status': res.text
        }
        return s

    def sign_in(self, classid, courseid, activeid, sign_type):
        """签到类型的逻辑判断"""
        if self.check_activeid(activeid):
            return

        if "手势" in sign_type:
            # test:('拍照签到', 'success')
            return self.hand_sign(classid, courseid, activeid)

        elif "二维码" in sign_type:
            return self.qcode_sign(activeid)

        elif "位置" in sign_type:
            return self.addr_sign(activeid)

        else:
            # '[2020-03-20 14:42:35]-[签到成功]'
            r = self.general_sign(classid, courseid, activeid)
            return r

    def sign_tasks_run(self):
        """开始所有签到任务"""
        tasks = []
        final_msg = []

        # 获取所有课程的classid和course_id
        classid_courseId = self.get_all_classid()

        # 获取所有课程activeid和签到类型
        for i in classid_courseId:
            coroutine = self.get_activeid(i[1], i[0], i[2])
            tasks.append(coroutine)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(asyncio.gather(*tasks))
        for r in result:
            if r:
                for d in r['class'].values():
                    s = self.sign_in(d['classid'], d['courseid'],
                                     d['activeid'], d['sign_type'])
                    if s:
                        # 签到课程， 签到时间， 签到状态
                        sign_msg = {
                            'name': d['classname'],
                            'date': s['date'],
                            'status': s['status']
                        }
                        final_msg.append(sign_msg)
        return final_msg


def server_chan_send(msg):
    """server酱将消息推送至微信"""
    print("PUSH TO WECHAT")
    desp = ''
    for d in msg:
        desp = '|  **课程名**  |   ' + \
            str(d['name'])+'   |\r| :----------: | :---------- |\r'
        desp += '| **签到时间** |   '+str(d['date'])+'   |\r'
        desp += '| **签到状态** |   '+str(d['status'])+'   |\r'

    params = {
        'text': str(msg[0]['name'])+"-"+str(msg[0]['status']),
        'desp': desp
    }

    requests.get(server_chan['url'], params=params)


def telegram_push_send(msg):
    """Telegrambot 推送"""
    print("PUSH TO TELEGRAM")
    desp = ''
    for d in msg:
        desp = "课程:{}%0A".format(d['name'])
        desp += "时间:{}%0A".format(d['date'])
        desp += "状态:{}".format(d['status'])

    requests.get(telegram_push['url'] + desp)


def local_run():
    # 本地运行使用
    print("START CHECK")
    s = AutoSign(user_info['username'], user_info['password'])
    result = s.sign_tasks_run()
#    result=[{"name":"test","date":"test","status":"test"}]
    if result:
        if server_chan['status']:
            server_chan_send(result)
        if telegram_push['status']:
            telegram_push_send(result)
        return result
    else:
        return "NO TASK NOW"


if __name__ == '__main__':
    # try:
    # 	print(local_run())
    # except Exception as e:
    # 	print(e)
    print(local_run())
