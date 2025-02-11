"""
这个模块负责从zdbk获取数据
"""
from Entities.Course import Course
from Entities.WishList import WishList
import requests as r
import re
import json

GNMKDM = "N253530"
XN = "2024-2025"
XQ = "2"
NJ = "2024"
ZYDM = "1102"
JXJHH = "20241102"
XNXQ = f"({XN}-{XQ})-"

headers = {
    "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.58'
}

session = r.session()

# 本地不保存用户名和密码，防止泄露。
username = ""
password = ""

chosenClasses = None

def encrypt(publicExponent, modulus, password):
    passwordInt = int.from_bytes(bytes(password, 'ascii'), 'big')
    resultInt = pow(passwordInt, int(publicExponent, 16), int(modulus, 16))
    return hex(resultInt)[2:].rjust(128, '0')


def loginZDBK() -> bool:
    """
    登录浙江大学本科教务系统
    :return: 登录是否成功 True/False
    """
    if username == "" or password == "":
        return False

    response = session.post(
        "http://zjuam.zju.edu.cn/cas/login?service=http%3A%2F%2Fzdbk.zju.edu.cn%2Fjwglxt%2Fxtgl%2Flogin_ssologin.html",
        headers=headers
    )
    execution = re.findall(r"\"execution\" value=\"(.*?)\"", response.text)[0]
    response = session.get("https://zjuam.zju.edu.cn/cas/v2/getPubKey", headers=headers)
    modulus = re.findall(r"\"modulus\":\"(.*?)\"", response.text)[0]
    exponent = re.findall(r"\"exponent\":\"(.*?)\"", response.text)[0]

    encryptedPassword = encrypt(exponent, modulus, password)

    response = session.post(
        "http://zjuam.zju.edu.cn/cas/login?service=http%3A%2F%2Fzdbk.zju.edu.cn%2Fjwglxt%2Fxtgl%2Flogin_ssologin.html",
        headers=headers,
        data={
            "username": username,
            "password": encryptedPassword,
            "execution": execution,
            "_eventId": "submit",
        }
    )
    for cookie in session.cookies:
        if cookie.name == "iPlanetDirectoryPro":
            return True
    return False


def getChosenClasses():
    """
    获取已选课程
    :return: json格式的已选课程
    """
    global chosenClasses
    if chosenClasses is not None:
        return chosenClasses
    response = session.post(
        f"http://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbChoosed.html?gnmkdm={GNMKDM}&su={username}",
        data={
            "xn": XN,
            "xq": XQ
        },
        headers=headers
    )
    chosenClasses = response.json()
    return chosenClasses


def updateCoursesJson(doubleVar):
    """
    更新courses.json文件
    :param doubleVar: DoubleVar对象。用于显示进度条
    """
    courses = []
    codes = []
    def _updateCourseJson(dl, xkmc):
        url = f"http://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbKcList.html?gnmkdm={GNMKDM}&su={username}"
        data = {
            "lx": "bl",
            "nj": NJ,
            "xn": XN,
            "xq": XQ,
            "zydm": ZYDM,
            "jxjhh": JXJHH,
            "xnxq": XNXQ,
            "kspage": "1",
            "jspage": "10000",
            "dl": dl,
            "xkmc": xkmc
        }
        response = session.post(url, data=data, headers=headers)     # 通识必修课
        j = response.json()
        for course in j:
            code = course["xskcdm"]
            if code not in codes:
                codes.append(code)
                courses.append(course)

    _updateCourseJson("xk_b", "全部课程")
    doubleVar.set(0.2)

    _updateCourseJson("xk_n", "全部课程")
    doubleVar.set(0.4)

    _updateCourseJson("xk_8", "体育课程")
    doubleVar.set(0.6)

    _updateCourseJson("xk_zyjckc", "专业基础课程")
    doubleVar.set(0.8)

    _updateCourseJson("zy_qb", "所有类（专业）")
    doubleVar.set(1.0)

    with open("courses.json", "w", encoding="UTF-8") as f:
        json.dump(courses, f, ensure_ascii=False)


def updateClassJson(wishList: WishList, doubleVar):
    """
    更新classes.json文件
    :param wishList: wishList对象。本方法只会获取wishList中的课程，以减少网络请求时间。
    :param doubleVar: DoubleVar对象。用于显示进度条
    """
    url = f"http://zdbk.zju.edu.cn/jwglxt/xsxk/zzxkghb_cxZzxkGhbJxbList.html?gnmkdm={GNMKDM}&su={username}"
    with open("courses.json", "r", encoding="UTF-8") as f:
        course_data = json.load(f)

    courseCodeContained = []
    details = []
    for wish in wishList.wishes:
        doubleVar.set(wishList.wishes.index(wish) / len(wishList.wishes) / 2)
        for course in course_data:
            if Course.isEqualCourseCode(course["kcdm"], wish.courseCode):
                courseCodeContained.append(course["kcdm"])
                data = {
                    "dl": "",
                    "xn": XN,
                    "xq": XQ,
                    "kcdm": course["kcdm"],
                    "xkkh": course["xkkh"],
                    "ylxs": "0"
                }
                response = session.post(url, data=data, headers=headers)
                details.append(response.json())
                break
    for class_ in getChosenClasses():
        doubleVar.set(0.5 + getChosenClasses().index(class_) / len(getChosenClasses()) / 2)
        if class_["t_kcdm"] not in courseCodeContained:
            # class和course的xkkh不一样
            for course in course_data:
                if Course.isEqualCourseCode(course["kcdm"],class_["t_kcdm"]):
                    courseCodeContained.append(course["kcdm"])
                    data = {
                        "dl": "",
                        "xn": XN,
                        "xq": XQ,
                        "kcdm": course["kcdm"],
                        "xkkh": course["xkkh"],
                        "ylxs": "0"
                    }
                    response = session.post(url, data=data, headers=headers)
                    details.append(response.json())
                    break
            else:
                # 已经选上的课，在courses.json中找不到对应的课程。例如形势与政策I，秋学期选的，春学期找不到。
                ...



    with open("classes.json", "w", encoding="UTF-8") as f:
        json.dump(details, f, ensure_ascii=False)

