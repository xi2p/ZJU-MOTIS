from typing import *

class Strategy:
    def __init__(self, hot, normal, cold):
        """
        用于描述选一门课的三个志愿的策略。用户可以通过这个类来描述自己的选课策略。
        hot表示热门班级数量，normal表示普通班级数量，cold表示冷门班级数量。
        三个参数的和应该等于3。
        :param hot:
        :param normal:
        :param cold:
        """
        if hot + normal + cold != 3:
            raise ValueError("Unable to create Strategy object: hot + normal + cold should be 3")
        self.hot = hot
        self.normal = normal
        self.cold = cold

