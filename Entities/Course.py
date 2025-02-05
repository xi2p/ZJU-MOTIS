from typing import *
from .Strategy import Strategy
from .Constants import STRATEGY_DEFAULT
from .Time import *


class CourseType:
    def __init__(self, sort: str, belonging: str, mark: str, identification: str):
        """
        课程类别由多个属性组成
        :param sort: 课程类别，如通识、专业基础课程、专业课等
        :param belonging: 课程归属，如当代社会、博雅技艺、思政类\军体类等
        :param mark: 课程标记，是否为通识核心课程
        :param identification: 认定类别，如美育类、创新创业类等
        """
        self.sort = sort
        self.belonging = belonging
        self.mark = mark
        self.identification = identification

    def __repr__(self):
        return f"CourseType({self.sort}, {self.belonging}, {self.mark}, {self.identification})"


class Course:
    def __init__(self, courseCode, courseName, credit, courseType: CourseType, academy, status: str):
        """
        :param courseCode: 课程代码
        :param courseName: 课程名称
        :param credit: 学分
        :param courseType: 课程类别
        :param academy: 开课学院
        :param status: 选择状态 @see: Constants.CourseStatus
        这些属性都是可以从json文件中读取的
        """
        self.courseCode = courseCode
        self.courseName = courseName
        self.credit = credit
        self.courseType = courseType
        self.academy = academy
        self.status = status

        # 以下为选课策略
        self.priority = 0       # 选课优先级。数字越大，优先级越高。非负整数
        self.strategy = Strategy(*STRATEGY_DEFAULT)

        self.autoTeacherGroup = True    # 是否自动划分教师组（按照査老师数据划分）
        self.rated = False      # 是否已经给各班级评分。设置这个属性是为了减少网络IO
        self.classScoreList : List[List] = [] # [[class1, score1], ... ] # 存储各班级的评分
        self.teacherGroup = [[], [], [], []]
        self.requiredTeachers = []
        self.avoidedTeachers = []

        self.expectedTimeList : List[ClassTime] = []  # 期望上课时间
        self.avoidTimeList : List[ClassTime] = [] # 避免上课时间

        self.teacherFactor = 1.0  # 教师因素权重
        self.timeFactor = 1.0    # 时间因素权重
        self.possibilityFactor = 3.0    # 选上的概率的权重

        # 三个选课志愿
        self.candidates = []    # List[Course]

    def withPriority(self, priority: int):
        if priority < 0 or not isinstance(priority, int):
            raise ValueError(
                "Priority must be a non-negative integer!"
            )
        self.priority = priority
        return self

    def withStrategy(self, strategy: Strategy):
        self.strategy = strategy
        return self

    def onlyChooseFromTheseTeachers(self, *teacherName):
        self.autoTeacherGroup = False
        self.requiredTeachers.extend(teacherName)
        return self

    def preferredTeacher(self, *teacherName):
        self.autoTeacherGroup = False
        self.teacherGroup[0].extend(teacherName)
        return self

    def goodTeacher(self, *teacherName):
        self.autoTeacherGroup = False
        self.teacherGroup[1].extend(teacherName)
        return self

    def normalTeacher(self, *teacherName):
        self.autoTeacherGroup = False
        self.teacherGroup[2].extend(teacherName)
        return self

    def badTeacher(self, *teacherName):
        self.autoTeacherGroup = False
        self.teacherGroup[3].extend(teacherName)
        return self

    def avoidTeacher(self, *teacherName):
        self.avoidedTeachers.extend(teacherName)
        return self

    def expectClassAt(self, classTime: ClassTime):
        self.expectedTimeList.append(classTime)
        return self

    def avoidClassAt(self, classTime: ClassTime):
        self.avoidTimeList.append(classTime)
        return self

    def withTeacherFactor(self, factor: float):
        self.teacherFactor = factor
        return self

    def withTimeFactor(self, factor: float):
        self.timeFactor = factor
        return self

    def withPossibilityFactor(self, factor: float):
        self.possibilityFactor = factor
        return self

    def withStatus(self, status: str):      # 测试接口！！！
        self.status = status
        return self

    def __repr__(self):
        return f"Course({self.courseCode}, {self.courseName}, {self.credit}, {self.courseType}, {self.academy}, {self.status})"

    @staticmethod
    def isEqualCourseCode(code1:str, code2:str) -> bool:
        """
        用于判断两个课程代码是否相同。
        课程代码有时候会有括号，有时候没有。括号外和括号内的内容都是课程代码，只是版本不同。
        括号内的内容是新版课程代码，括号外的内容是旧版课程代码。但他们都指向同一门课。
        """
        if '（' in code1:
            new1, old1 = code1.split('（')
            old1 = old1[:-1]
        else:
            new1 = old1 = code1
        if '（' in code2:
            new2, old2 = code2.split('（')
            old2 = old2[:-1]
        else:
            new2 = old2 = code2
        return any([
            new1 == new2, new1 == old2, old1 == new2, old1 == old2
        ])
