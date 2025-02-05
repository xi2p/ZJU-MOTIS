"""
这个模块负责读取本地json数据，
并将数据转换为python对象
"""
import json
from typing import *
from Entities import Course, Class, Time, Constants, ClassTable
import re
import network

course_data = []
class_data = []

with open("teacher.json", "r", encoding="utf-8") as f:
    teacher_data = json.load(f)


NULL_TEACHER_SCORE = -1 # 无法查到教师评分时的返回值。应当小于所有可能的评分值
teacher_rate_pool = {}  # 用于缓存教师评分。避免重复查找

def getTeacherRate(teacherName: str) -> float:
    """
    获取老师在査老师上的评分。査老师的数据已经被爬取并保存在teacher.json中
    :param teacherName: 教师名
    :return: 评分。如果查不到，返回NULL_TEACHER_SCORE
    """
    if teacherName in teacher_rate_pool:
        return teacher_rate_pool[teacherName]
    for teacher in teacher_data["teachers"]:
        if teacher["name"] == teacherName:
            try:
                teacher_rate_pool[teacherName] = float(teacher["rate"])
                return float(teacher["rate"])
            except:     # 查不到、分数为N/A，这样
                teacher_rate_pool[teacherName] = NULL_TEACHER_SCORE
                return NULL_TEACHER_SCORE
    teacher_rate_pool[teacherName] = NULL_TEACHER_SCORE
    return NULL_TEACHER_SCORE


# class ClassSet:
#     """
#     所有课程班级的集合。
#     可以通过施加各种限定条件来减少集合内的班级数量。
#     """
#     def __init__(self):
#         self.classes = deepcopy(all_class_set)
course_object_pool = []

def getCourseFromCourseCode(courseCode: str) -> Course.Course:
    """
    通过课程代码获取课程信息
    :param courseCode: 课程代码
    :return: 课程信息(courseCode, courseName, credit, courseType: CourseType, academy, status)
    """

    ambiguous = False  # 是否有多个课程匹配。这是异常情况。
    target: Union[Course.Course, None] = None
    for course in course_object_pool:
        if Course.Course.isEqualCourseCode(courseCode, course.courseCode):
            return course

    target: Union[Dict, None] = None
    for course in course_data:
        if Course.Course.isEqualCourseCode(courseCode, course["xskcdm"]):
            target = course
            break

    if target is None:
        raise ValueError(f"未找到课程代码匹配的课程'{courseCode}'")

    course_type = Course.CourseType(
        target.get("kclb", ""),  # 课程类别
        target.get("kcgs", ""),  # 课程归属
        target.get("kcbs", ""),  # 课程标识
        target.get("rdlb", "")  # 认定类别
    )
    course = Course.Course(
        target["xskcdm"],  # 课程代码
        target["kcmc"],  # 课程名称
        float(re.findall(r"~(.*?)~", target["kcxx"])[0]),  # 学分
        course_type,  # 课程类别
        target["kkxy"],  # 开课学院
        Constants.CourseStatus.NOT_SELECTED
        # Constants.CourseStatus.SELECTED if int(target["kcxzzt"]) else Constants.CourseStatus.NOT_SELECTED  # 课程选择状态
    )
    course_object_pool.append(course)
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
    first_half_time_list: List[Tuple[int, int]] = []
    second_half_time_list: List[Tuple[int, int]] = []
    for piece in time.split(";"):
        # 以下代码用于正确解析课程的时间
        # 有的课程的时间是这样的：time="春周三第9,10节<br>夏周三第9,10节", semester="春夏"
        # 为了适应所有情况，我设计了以下代码
        first_half, second_half = False, False
        day, class_time = piece.split("第")
        if "春" in day or "秋" in day:
            first_half = True
            day = day[1:]
        if "夏" in day or "冬" in day:
            second_half = True
            day = day[1:]

        if semester == "春" or semester == "秋":
            first_half = True
        if semester == "夏" or semester == "冬":
            second_half = True

        if not first_half and not second_half:
            first_half = second_half = True

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
        class_time = class_time.split("节")[0]
        class_time = [int(i) for i in class_time.split(",")]
        for i in class_time:
            if first_half:
                first_half_time_list.append((day, i))
            if second_half:
                second_half_time_list.append((day, i))
    return Time.ClassTime(first_half_time_list, second_half_time_list)


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
    time_list = []
    for exam in time:
        # 用re.findall提取时间
        (
            year, month, day,
            start_hour, start_minute,
            end_hour, end_minute
        ) = re.findall(r"(.*?)年(.*?)月(.*?)日\((.*?):(.*?)-(.*?):(.*?)\)", exam)[0]
        # 转换为datetime对象
        start_time = datetime.datetime(int(year), int(month), int(day), int(start_hour), int(start_minute))
        end_time = datetime.datetime(int(year), int(month), int(day), int(end_hour), int(end_minute))
        time_list.append(Time.ExamTime(start_time, end_time))

    return time_list


def loadCourseData():
    course_data.clear()
    with open("courses.json", "r", encoding="utf-8") as f:
        course_data.extend(json.load(f))

all_class_set = []

"""
运行时序：
1. 程序运行开始，先调用loadCourseData()，加载课程数据。然后等待用户登录。
2. 等待用户输入选课代码，然后开始执行选课算法。此时loadClassData()仍未被调用，无法获取班级对象。
3. 选课算法开始执行，首先调用updateClassJson()。updateClassJson首先获取用户的选课数据。选课数据里有用户已选的课程的课程代码和班级代码
4. 接下来下载程序运行需要的班级数据。这个过程中要下载wishList中的课程以及用户已有的选课数据中的课程的班级数据。
5. 接下来调用loadClassData()，加载班级数据。这个过程中需要正确填充status属性。之后就可以获取班级对象了。
6. 将已选的课程对象插入classTable中，然后开始正式执行选课算法。
"""
def loadClassData():
    class_data.clear()
    with open("classes.json", "r", encoding="utf-8") as f:
        class_data.extend(json.load(f))

    confirmed_class_code_set = []
    to_be_filtered_class_code_set = []
    for class_ in network.getChosenClasses():
        if class_["sxbj"] == "1":
            confirmed_class_code_set.append(class_["xkkh"])
            try:
                getCourseFromCourseCode(class_["t_kcdm"]).status = Constants.CourseStatus.SELECTED
            except ValueError:
                pass    # 已经选上的课，在courses.json中找不到对应的课程。例如形势与政策I，秋学期选的，春学期找不到。
        else:
            to_be_filtered_class_code_set.append(class_["xkkh"])

    all_class_set.clear()
    for course in class_data:
        for class_ in course:
            try:
                if class_["xkkh"] in confirmed_class_code_set:
                    class_status = Constants.ClassStatus.CONFIRMED
                elif class_["xkkh"] in to_be_filtered_class_code_set:
                    class_status = Constants.ClassStatus.TO_BE_FILTERED
                else:
                    class_status = Constants.ClassStatus.NOT_SELECTED

                all_class_set.append(
                    Class.Class(
                        class_["xkkh"],
                        getCourseFromCourseCode(re.findall(r"\)-(.*?)-", class_["xkkh"])[0]),
                        class_["jsxm"].split("<br>"),
                        class_["xxq"],
                        getClassTimeFromString(class_["sksj"], class_["xxq"]),
                        getExamTimeListFromString(class_.get("kssj", "")),
                        int(class_["rs"].split("/")[0]),
                        int(class_["yxrs"].split("~")[1]),
                        class_status,
                        class_["sksj"],
                        class_["xxq"],
                        class_["skdd"]
                    )
                )
            except Exception as e:
                print(f"Failed({e}) to create class", class_["xkkh"])



    # print(f"Succeeded to load all classes({len(all_class_set)} classes in total)")


def filterClassSetByCondition(condition: Callable[[Class.Class], bool], src_set=None) -> List[Class.Class]:
    """
    通过条件过滤班级集合
    调用示例：
    filterClassSetByCondition(lambda x: (Course.Course.isEqualCourseCode("MATH1136G", x.course.courseCode)))
    :param condition: 一个函数，接受一个班级对象，返回一个bool值
    :param src_set: 源班级集合。默认为所有班级集合
    :return: 符合条件的班级集合
    """
    if src_set is None:
        src_set = all_class_set
    class_set = []
    for class_ in src_set:
        if condition(class_):
            class_set.append(class_)
    return class_set


def initClassTable(classTable: ClassTable.ClassTable):
    """
    获取zdbk上用户已经选的课程，然后将这些课程插入到classTable中
    :param classTable: classTable对象
    """
    for class_data in network.getChosenClasses():
        classes = filterClassSetByCondition(
            lambda x: x.classCode == class_data["xkkh"]
        )
        if len(classes) != 0:
            classTable.append(
                classes[0]
            )

if __name__ == '__main__':
    loadClassData()
    print("Start testing data.py")
    c = filterClassSetByCondition(lambda x: (Course.Course.isEqualCourseCode("MATH1136G", x.course.courseCode)))
    print(c)
    print(len(course_object_pool))

    course1 = getCourseFromCourseCode("MATH1136G")
    course2 = getCourseFromCourseCode("MATH1136G")
    print(course1 == course2)

    print(getTeacherRate("汪国军"))
    print(getTeacherRate("汪国"))