from .Course import Course
from .Time import *


class Class:
    def __init__(self, classCode: str,
                 course: Course, teacherNames: List[str], semester: str,
                 classTime: ClassTime, examTimeList: List[ExamTime],
                 available: int, unfiltered: int, status: str,
                 originClassTimeStr: str, originSemesterStr:str, location: str):
        """
        教学班
        :param classCode: 班级代码
        :param course: 课程
        :param teacherNames: 教师姓名列表。一门课可能有多个老师
        :param semester: 学期
        :param classTime: 上课时间
        :param examTimeList: 考试时间列表。一门课可能有多个考试。
        :param available: 余量
        :param unfiltered: 待筛选人数
        :param status: 课程筛选状态   see: Constants.ClassStatus
        :param originClassTimeStr: 原始的上课时间字符串
        :param originSemesterStr: 原始的学期字符串
        :param location: 上课地点
        """
        self.classCode = classCode
        self.course = course
        self.teacherNames = teacherNames
        self.semester = semester
        self.classTime = classTime
        self.examTimeList = examTimeList
        self.available = available
        self.unfiltered = unfiltered
        self.status = status

        self.originClassTimeStr = originClassTimeStr
        self.originSemesterStr = originSemesterStr
        self.location = location

        self._rate : Union[float, None] = None   # 系统给这门课算出的评分。由data.py中的calculateClassRate(course)函数计算并填充。
        self._teacherRate : Union[float, None] = None  # 教师评分。由data.py中的calculateClassRate(course)函数计算并填充。
        self._timeRate : Union[float, None] = None  # 时间评分。由data.py中的calculateClassRate(course)函数计算并填充。
        self._possibilityRate : Union[float, None] = None  # 选上概率评分。由data.py中的calculateClassRate(course)函数计算并填充。

    def isConflict(self, item):
        if not isinstance(item, Class):
            raise TypeError(
                "item must be an instance of Class"
            )
        if self.course.courseCode == item.course.courseCode:
            # 同一个课程的不同班级之间不会冲突
            # 因为你只能选上一个班级
            return False

        return any(
            [
                self.classTime.isOverlapped(item.classTime),
                any(
                    [
                        any(
                            [
                                itemExamTime.isOverlapped(examTime)
                                for examTime in self.examTimeList
                            ]
                        ) for itemExamTime in item.examTimeList
                    ]
                )
            ]
        )

    @property
    def rate(self):
        if self._rate is None:
            raise ValueError("Rate is not calculated yet. Use data.calculateClassRate() ahead.")
        return self._rate

    @rate.setter
    def rate(self, value):
        self._rate = value

    @property
    def teacherRate(self):
        if self._teacherRate is None:
            raise ValueError("Possibility is not calculated yet. Use data.calculateClassRate() ahead.")
        return self._teacherRate

    @teacherRate.setter
    def teacherRate(self, value):
        self._teacherRate = value

    @property
    def timeRate(self):
        if self._timeRate is None:
            raise ValueError("Possibility is not calculated yet. Use data.calculateClassRate() ahead.")
        return self._timeRate

    @timeRate.setter
    def timeRate(self, value):
        self._timeRate = value

    @property
    def possibilityRate(self):
        if self._possibilityRate is None:
            raise ValueError("Possibility is not calculated yet. Use data.calculateClassRate() ahead.")
        return self._possibilityRate

    @possibilityRate.setter
    def possibilityRate(self, value):
        self._possibilityRate = value

    def __eq__(self, other):
        if not isinstance(other, Class):
            raise TypeError(
                "item must be an instance of Class"
            )
        return self.classCode == other.classCode

    def __hash__(self):
        return hash(self.classCode)

    def __repr__(self):
        return f"Class({self.classCode}, {self.teacherNames}, {self.rate})"
        # return f"Class({self.classCode}, {self.course}, {self.teacherNames}, {self.semester}, {self.classTime}, {self.examTimeList}, {self.available}, {self.unfiltered})"


if __name__ == '__main__':
    cl = Class("123", Course("123", "123", 3, "123", "123", "123"), ["123"], "123", None, None, 1, 1, 1)
    print(cl)
    cl.rate = 1.0
    print(cl.rate)
