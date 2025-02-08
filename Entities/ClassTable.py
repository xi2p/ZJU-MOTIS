"""
课表对象
"""
from typing import *
from .Class import Class, ClassTime, ExamTime
from .Course import Course


class ClassTable:
    def __init__(self):
        self.classes : List[Class] = []

    def isConflict(self, item: Class) -> bool:
        """
        判断一个班级是否和当前课表有时间上的冲突
        :param item: 课程对象
        :return: bool
        """
        for class_ in self.classes:
            if class_.isConflict(item):
                return True
        return False

    def append(self, item: Class):
        if self.getNumberOfCandidates(item.course) >= 3:
            raise ValueError(
                "A course can only have at most 3 candidates!"
            )
        if self.isConflict(item):
            raise ValueError(
                "Cannot append a class that is conflict with current ClassTable!"
            )
        self.classes.append(item)

    def removeClass(self, item: Class):
        while item in self.classes:
            self.classes.remove(item)


    def removeCourse(self, course: Course):
        """
        从课表中删除某门课程的所有班级
        :param course: Course对象
        """
        classToRemove = []
        for class_ in self.classes:
            if Course.isEqualCourseCode(class_.course.courseCode, course.courseCode):
                classToRemove.append(class_)

        for class_ in classToRemove:
            self.classes.remove(class_)

    def getNumberOfCandidates(self, course):
        """
        获取某门课程的志愿数量
        :param course: Course对象
        :return: 这门课程现在的志愿数量
        """
        return len([class_ for class_ in self.classes if Course.isEqualCourseCode(class_.course.courseCode, course.courseCode)])

    def pop(self):
        return self.classes.pop()

    def clear(self):
        self.classes.clear()

    def extend(self, classTable):
        classTable: ClassTable
        self.classes.extend(classTable.classes)

    def copyTo(self, classTable):
        classTable: ClassTable
        classTable.classes.clear()
        classTable.classes.extend(self.classes)