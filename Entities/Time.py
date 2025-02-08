from copy import deepcopy
from datetime import datetime
from typing import *


class ClassTime:
    def __init__(self, firstHalfTimeList: List[Tuple[int, int]], secondHalfTimeList: List[Tuple[int, int]]):
        """
        上课时间
        :param firstHalfTimeList: 上半学期的课表 [(周几, 第几节课), ...]
        :param secondHalfTimeList: 下半学期的课表 [(周几, 第几节课), ...]
        """
        self.firstHalfTimeList = firstHalfTimeList
        self.firstHalfTimeList.sort(key=lambda x: (x[0], x[1]))
        self.secondHalfTimeList = secondHalfTimeList
        self.secondHalfTimeList.sort(key=lambda x: (x[0], x[1]))

    def isOverlapped(self, item):
        if isinstance(item, ClassTime):
            return (
                    any(i in self.firstHalfTimeList for i in item.firstHalfTimeList)
                    or any(i in self.secondHalfTimeList for i in item.secondHalfTimeList)
            )
        raise TypeError("item must be an instance of ClassTime")

    def __add__(self, other):
        if not isinstance(other, ClassTime):
            raise TypeError(
                "item must be an instance of ClassTime"
            )
        first_half_time_list = deepcopy(self.firstHalfTimeList)
        for i in other.firstHalfTimeList:
            if i not in first_half_time_list:
                first_half_time_list.append(i)

        second_half_time_list = deepcopy(self.secondHalfTimeList)
        for i in other.secondHalfTimeList:
            if i not in second_half_time_list:
                second_half_time_list.append(i)

        return ClassTime(first_half_time_list, second_half_time_list)

    def __sub__(self, other):
        """
        重载减法运算符，本质上是获取self和other的差集。具体来说，是获取self中有而other中没有的元素。
        :param other: 另一个ClassTime对象
        :return: 取差集后的ClassTime对象
        """
        if not isinstance(other, ClassTime):
            raise TypeError(
                "item must be an instance of ClassTime"
            )
        firstHalfTimeList = deepcopy(self.firstHalfTimeList)
        for i in other.firstHalfTimeList:
            if i in firstHalfTimeList:
                firstHalfTimeList.remove(i)

        secondHalfTimeList = deepcopy(self.secondHalfTimeList)
        for i in other.secondHalfTimeList:
            if i in secondHalfTimeList:
                secondHalfTimeList.remove(i)

        return ClassTime(firstHalfTimeList, secondHalfTimeList)

    def __mul__(self, other):
        """
        重载乘法运算符，本质上是获取self和other的交集。具体来说，是获取self和other中都有的元素。
        :param other: 另一个ClassTime对象
        :return: 取交集后的ClassTime对象
        """
        if not isinstance(other, ClassTime):
            raise TypeError(
                "item must be an instance of ClassTime"
            )
        firstHalfTimeList = [i for i in self.firstHalfTimeList if i in other.firstHalfTimeList]
        secondHalfTimeList = [i for i in self.secondHalfTimeList if i in other.secondHalfTimeList]
        return ClassTime(firstHalfTimeList, secondHalfTimeList)

    def __eq__(self, other):
        if not isinstance(other, ClassTime):
            raise TypeError(
                "item must be an instance of ClassTime"
            )
        return self.firstHalfTimeList == other.firstHalfTimeList and self.secondHalfTimeList == other.secondHalfTimeList

    def __contains__(self, item):
        # 对应表达式： item in self
        if isinstance(item, ClassTime):
            return (
                all(i in self.firstHalfTimeList for i in item.firstHalfTimeList)
                and all(i in self.secondHalfTimeList for i in item.secondHalfTimeList)
            )
        raise TypeError("item must be an instance of ClassTime")

    def __repr__(self):
        # return f"ClassTime()"
        return f"ClassTime({self.firstHalfTimeList}, {self.secondHalfTimeList})"



class ExamTime:
    def __init__(self, startTime: datetime, endTime: datetime, noExam:bool=False):
        """
        考试时间
        :param startTime: 考试开始时间
        :param endTime: 考试结束时间
        """
        self.startTime = startTime
        self.endTime = endTime
        self.noExam : bool = noExam

    def isOverlapped(self, item):
        if isinstance(item, ExamTime):
            if self.noExam or item.noExam:
                return False
            return not (self.endTime < item.startTime or self.startTime > item.endTime)
        raise TypeError("item must be an instance of ExamTime")

    def __repr__(self):
        return f"ExamTime({self.startTime}, {self.endTime}, {self.noExam})"