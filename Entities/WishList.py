"""
想要选什么课
----------------
特别更新：2025 蛇年大吉！     2025-01-28
----------------
"""
from typing import *
from .Course import Course


class WishList:
    def __init__(self):
        self.wishes : List[Course] = []
        self.maxPriority = -1

    def append(self, course) -> Course:
        self.wishes.append(course)
        return course
