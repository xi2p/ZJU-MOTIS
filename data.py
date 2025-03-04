"""
这个模块负责读取本地json数据，
并将数据转换为python对象
"""
import json
from typing import *
from Entities import Course, Class, Time, Constants, ClassTable
import re
import network
import os

courseData = []
classData = []

with open("teacher.json", "r", encoding="utf-8") as f:
    teacher_data = json.load(f)


NULL_TEACHER_SCORE = -1 # 无法查到教师评分时的返回值。应当小于所有可能的评分值
teacherRatePool = {}  # 用于缓存教师评分。避免重复查找

def getTeacherRate(teacherName: str) -> float:
    """
    获取老师在査老师上的评分。査老师的数据已经被爬取并保存在teacher.json中
    :param teacherName: 教师名
    :return: 评分。如果查不到，返回NULL_TEACHER_SCORE
    """
    if teacherName in teacherRatePool:
        return teacherRatePool[teacherName]
    for teacher in teacher_data["teachers"]:
        if teacher["name"] == teacherName:
            try:
                teacherRatePool[teacherName] = float(teacher["rate"])
                return float(teacher["rate"])
            except:     # 查不到、分数为N/A，这样
                teacherRatePool[teacherName] = NULL_TEACHER_SCORE
                return NULL_TEACHER_SCORE
    teacherRatePool[teacherName] = NULL_TEACHER_SCORE
    return NULL_TEACHER_SCORE


# class ClassSet:
#     """
#     所有课程班级的集合。
#     可以通过施加各种限定条件来减少集合内的班级数量。
#     """
#     def __init__(self):
#         self.classes = deepcopy(all_class_set)
courseObjectPool = []

def getCourseFromCourseCode(courseCode: str) -> Course.Course:
    """
    通过课程代码获取课程信息
    :param courseCode: 课程代码
    :return: 课程信息(courseCode, courseName, credit, courseType: CourseType, academy, status)
    """

    for course in courseObjectPool:
        if Course.Course.isEqualCourseCode(courseCode, course.courseCode):
            return course

    target: Union[Dict, None] = None
    for course in courseData:
        if Course.Course.isEqualCourseCode(courseCode, course["xskcdm"]):
            target = course
            break

    if target is None:
        raise ValueError(f"未找到课程代码匹配的课程'{courseCode}'")

    courseType = Course.CourseType(
        target.get("kclb", ""),  # 课程类别
        target.get("kcgs", ""),  # 课程归属
        target.get("kcbs", ""),  # 课程标识
        target.get("rdlb", "")  # 认定类别
    )
    course = Course.Course(
        target["xskcdm"],  # 课程代码
        target["kcmc"],  # 课程名称
        float(re.findall(r"~(.*?)~", target["kcxx"])[0]),  # 学分
        courseType,  # 课程类别
        target["kkxy"],  # 开课学院
        Constants.CourseStatus.NOT_SELECTED
        # Constants.CourseStatus.SELECTED if int(target["kcxzzt"]) else Constants.CourseStatus.NOT_SELECTED  # 课程选择状态
    )
    courseObjectPool.append(course)
    return course


def getClassTimeFromString(time: str, semester) -> Time.ClassTime:
    """
    从字符串中解析出时间
    :param time: 时间字符串 "周一第3,4,5节;周二第9节;周三第1,2节"
    :param semester: 学期字符串 "春夏"
    :return: 时间对象
    """
    # print("ClassTime:", time)
    if time in ["待定", "--", ""]:
        return Time.ClassTime([], [])
    time = time.replace("<br>", ";")
    # Failed(Invalid day) to create class (2024-2025-2)-PHIL0702G-0007632-1E
    firstHalfTimeList: List[Tuple[int, int]] = []
    secondHalfTimeList: List[Tuple[int, int]] = []
    for piece in time.split(";"):
        # 以下代码用于正确解析课程的时间
        # 有的课程的时间是这样的：time="春周三第9,10节<br>夏周三第9,10节", semester="春夏"
        # 为了适应所有情况，我设计了以下代码
        firstHalf, secondHalf = False, False
        day, classTimeStr = piece.split("第")
        if "春" in day or "秋" in day:
            firstHalf = True
            day = day[1:]
        if "夏" in day or "冬" in day:
            secondHalf = True
            day = day[1:]

        if semester == "春" or semester == "秋":
            firstHalf = True
        if semester == "夏" or semester == "冬":
            secondHalf = True

        if not firstHalf and not secondHalf:
            firstHalf = secondHalf = True

        if day == "周一":
            day = Constants.Weekday.Monday
        elif day == "周二":
            day = Constants.Weekday.Tuesday
        elif day == "周三":
            day = Constants.Weekday.Wednesday
        elif day == "周四":
            day = Constants.Weekday.Thursday
        elif day == "周五":
            day = Constants.Weekday.Friday
        elif day == "周六":
            day = Constants.Weekday.Saturday
        elif day == "周日":
            day = Constants.Weekday.Sunday
        else:
            raise ValueError("Invalid day")
        classTimeStr = classTimeStr.split("节")[0]
        classTimeStr = [int(i) for i in classTimeStr.split(",")]
        for i in classTimeStr:
            if firstHalf:
                firstHalfTimeList.append((day, i))
            if secondHalf:
                secondHalfTimeList.append((day, i))
    return Time.ClassTime(firstHalfTimeList, secondHalfTimeList)


def getExamTimeListFromString(time: str) -> List[Time.ExamTime]:
    """
    从字符串中解析出考试时间
    :param time: 时间字符串 "2025年04月12日(14:00-16:00);2025年06月13日(08:00-10:00)"。若没有考试，则time输入""
    :return: 考试时间对象
    """
    import datetime
    # print("ExamTime", time)
    if time in ["待定", "--", ""]:
        return [Time.ExamTime(datetime.datetime(1970, 1, 1), datetime.datetime(1970, 1, 1), True)]
    time = time.replace("<br>", ";").split(";")
    timeList = []
    for exam in time:
        # 用re.findall提取时间
        (
            year, month, day,
            start_hour, start_minute,
            end_hour, end_minute
        ) = re.findall(r"(.*?)年(.*?)月(.*?)日\((.*?):(.*?)-(.*?):(.*?)\)", exam)[0]
        # 转换为datetime对象
        startTime = datetime.datetime(int(year), int(month), int(day), int(start_hour), int(start_minute))
        endTime = datetime.datetime(int(year), int(month), int(day), int(end_hour), int(end_minute))
        timeList.append(Time.ExamTime(startTime, endTime))

    return timeList


def loadCourseData():
    """
    从本地json文件中加载课程数据
    :return:
    """
    courseData.clear()
    if os.path.exists("courses.json"):
        with open("courses.json", "r", encoding="utf-8") as f:
            courseData.extend(json.load(f))

allClassSet = []

"""
运行时序：
1. 程序运行开始，先调用loadCourseData()，加载课程数据。然后等待用户登录。
2. 等待用户输入选课代码，然后开始执行选课算法。此时loadClassData()仍未被调用，无法获取班级对象。
3. 选课算法开始执行，首先调用updateClassJson()。updateClassJson首先获取用户的选课数据。选课数据里有用户已选的课程的课程代码和班级代码
4. 接下来下载程序运行需要的班级数据。这个过程中要下载wishList中的课程以及用户已有的选课数据中的课程的班级数据。
5. 接下来调用loadClassData()，加载班级数据。这个过程中需要正确填充status属性。之后就可以获取班级对象了。
6. 将已选的课程对象插入classTable中，然后开始正式执行选课算法。
"""
def loadClassData(doubleVar):
    """
    从本地json文件中加载班级数据
    :param doubleVar: 用于显示进度条
    """
    classData.clear()
    with open("classes.json", "r", encoding="utf-8") as f:
        classData.extend(json.load(f))

    confirmedClassCodeSet = []
    toBeFilteredClassCodeSet = []
    for class_ in network.getChosenClasses():
        if class_["sxbj"] == "1":
            confirmedClassCodeSet.append(class_["xkkh"])
            try:
                # 标记课程状态为已选
                getCourseFromCourseCode(class_["t_kcdm"]).status = Constants.CourseStatus.SELECTED
            except ValueError:
                pass    # 已经选上的课，在courses.json中找不到对应的课程。例如形势与政策I，秋学期选的，春学期找不到。
        else:
            toBeFilteredClassCodeSet.append(class_["xkkh"])

    allClassSet.clear()
    total = len(classData)
    for i, course in enumerate(classData):
        doubleVar.set(i / total)
        for class_ in course:
            try:
                if class_["xkkh"] in confirmedClassCodeSet:
                    class_status = Constants.ClassStatus.CONFIRMED
                elif class_["xkkh"] in toBeFilteredClassCodeSet:
                    class_status = Constants.ClassStatus.TO_BE_FILTERED
                else:
                    class_status = Constants.ClassStatus.NOT_SELECTED

                available = int(class_["rs"].split("/")[0])
                unfiltered = int(class_["yxrs"].split("~")[1])

                allClassSet.append(
                    Class.Class(
                        class_["xkkh"],
                        getCourseFromCourseCode(re.findall(r"\)-(.*?)-", class_["xkkh"])[0]),
                        class_["jsxm"].split("<br>"),
                        class_["xxq"],
                        getClassTimeFromString(class_["sksj"], class_["xxq"]),
                        getExamTimeListFromString(class_.get("kssj", "")),
                        available,
                        unfiltered,
                        class_status,
                        class_["sksj"],
                        class_["xxq"],
                        class_["skdd"]
                    )
                )
            except Exception as e:
                print(f"Failed({e}) to create class", class_["xkkh"])



    # print(f"Succeeded to load all classes({len(all_class_set)} classes in total)")


def filterClassSetByCondition(condition: Callable[[Class.Class], bool], srcSet=None) -> List[Class.Class]:
    """
    通过条件过滤班级集合
    调用示例：
    filterClassSetByCondition(lambda x: (Course.Course.isEqualCourseCode("MATH1136G", x.course.courseCode)))
    :param condition: 一个函数，接受一个班级对象，返回一个bool值
    :param srcSet: 源班级集合。默认为所有班级集合
    :return: 符合条件的班级集合
    """
    if srcSet is None:
        srcSet = allClassSet
    classSet = []
    for class_ in srcSet:
        if condition(class_):
            classSet.append(class_)
    return classSet


def filterCourseSetByCondition(condition: Callable[[Course.Course], bool]) -> Course.CourseList:
    """
    通过条件过滤课程集合
    :param condition: 一个函数，接受一个课程对象，返回一个bool值
    :return: 符合条件的课程列表
    """
    result = Course.CourseList()

    for course in courseData:
        courseType = Course.CourseType(
            course.get("kclb", ""),  # 课程类别
            course.get("kcgs", ""),  # 课程归属
            course.get("kcbs", ""),  # 课程标识
            course.get("rdlb", "")  # 认定类别
        )
        course = Course.Course(
            course["xskcdm"],  # 课程代码
            course["kcmc"],  # 课程名称
            float(re.findall(r"~(.*?)~", course["kcxx"])[0]),  # 学分
            courseType,  # 课程类别
            course["kkxy"],  # 开课学院
            Constants.CourseStatus.NOT_SELECTED
            # Constants.CourseStatus.SELECTED if int(target["kcxzzt"]) else Constants.CourseStatus.NOT_SELECTED  # 课程选择状态
        )
        if condition(course):
            result.append(getCourseFromCourseCode(course.courseCode))
    return result


def initClassTable(classTable: ClassTable.ClassTable):
    """
    获取zdbk上用户已经选的课程，然后将这些课程插入到classTable中
    :param classTable: classTable对象
    """
    for chosenClassData in network.getChosenClasses():
        classes = filterClassSetByCondition(
            lambda x: (x.classCode == chosenClassData["xkkh"] and x.status == Constants.ClassStatus.CONFIRMED)
        )
        if len(classes) != 0:
            classTable.append(
                classes[0]
            )

    # 处理assumeNotSelectCourse
    for course in classTable.getAssumeNotSelectCourse():
        classTable.removeCourse(course)
        course.status = Constants.CourseStatus.NOT_SELECTED
        classes = filterClassSetByCondition(
            lambda x: (Course.Course.isEqualCourseCode(course.courseCode, x.course.courseCode) and x.status == Constants.ClassStatus.CONFIRMED)
        )
        for class_ in classes:
            class_.status = Constants.ClassStatus.NOT_SELECTED