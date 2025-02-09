from interface import *

wishList = WishList()
classTable = ClassTable()

wishList.append("MATH1136G").withPriority(10)  # 微积分
wishList.append("PHY1001G").withPriority(9)  # 大学物理
wishList.append("MATH1138F").withPriority(9).onlyChooseOneTime()  # 常微分方程
wishList.append("ME1103F").withPriority(9)  # 机械制图及CAD基础
wishList.append("MARX1002G").withPriority(8)  # 史纲
wishList.append("ME1002F").withPriority(7)  # 工程训练
wishList.append("CS1241G").withPriority(7)  # 人工智能基础
wishList.append("EDU2001G").withPriority(6)  # 军事理论
wishList.append("PHIL0902G").withPriority(6)  # 希腊罗马哲学
wishList.append("PPAE1100G").withPriority(5)  # 体素
wishList.append("PPAE0065G").withPriority(4)  # 体育
wishList.append("BEFS0402G").withPriority(3)  # 微电子技术与纳米制造
wishList.append("HIST0200G").withPriority(2)  # 近代中日关系史

wishList.seek(
    lambda course: course.courseType.sort == 课程类别.通识
                   and (course.courseType.identification == 认定类别.创新创业类
                        or course.courseType.identification == 认定类别.美育类
                        or course.courseType.identification == 认定类别.心理健康类
                        or course.courseType.identification == 认定类别.劳育类)

).withPriority(1)

# selectClass(classTable, wishList)
#
# print(classTable.classes)

# todo: (feat) OneOf
# todo: (feat) 课程间约束，例如：要求A课程与B课程不在同一天。
# todo: (feat) assume not selected
