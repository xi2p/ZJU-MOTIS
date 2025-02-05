"""
特别说明：这个文件中定义的所有类都没有被用到过。
这个文件放在这里以防以后会用到(*╹▽╹*)
"""
from typing import *


class CourseGPARanking:
    """
    课程GPA排名
    根据老师名称和课程名称从chalaoshi获取数据这门课各个老师的平均GPA
    """
    def __init__(self, teacherName: str, courseName: str, rankingList: List[Tuple[str, float]]):
        """
        :param teacherName: 教师姓名
        :param courseName: 课程名称
        :param rankingList: GPA排行榜 [(老师姓名, 平均GPA), ...]
        """
        self.teacherName = teacherName
        self.courseName = courseName
        self.rankingList = rankingList.sort(key=lambda x: x[1], reverse=True)

    @property
    def rank(self):
        index = len(self.rankingList)
        for i in range(len(self.rankingList)):
            if self.rankingList[i][0] == self.teacherName:
                index = i + 1
                break
        return index

    @property
    def proportion(self):
        # 返回老师的GPA的排名是前百分之多少
        if len(self.rankingList) <= 1:
            # 如果只有一个老师，那么排名就是前0%
            return 0.0
        return self.rank / len(self.rankingList)


class Teacher:
    def __init__(self, teacherName: str, courseName: str, rating: float, courseGPARankingList: List[CourseGPARanking]):
        """
        某门课的教师。不同的课程但同一个教师的，需要新建一个Teacher对象。
        :param teacherName: 教师姓名
        :param courseName: 课程名称
        :param rating: 教师评分
        :param courseGPARankingList: 课程GPA排名列表
        """
        self.teacherName = teacherName
        self.courseName = courseName
        self.rating = rating
        self.courseGPARankingList = courseGPARankingList
