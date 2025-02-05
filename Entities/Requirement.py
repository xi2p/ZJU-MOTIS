"""
对选课的限制、要求
"""
from typing import *



class CourseRequirement:
    def __init__(self):
        # 需要详细设计...
        pass


class GlobalRequirement:
    def __init__(self):
        self.creditSuperiorLimit = None
        self.creditInferiorLimit = None

    def setCreditSuperiorLimit(self, credit: float):
        self.creditSuperiorLimit = credit
        return self

    def setCreditInferiorLimit(self, credit: float):
        self.creditInferiorLimit = credit
        return self


