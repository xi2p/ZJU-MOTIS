from interface import *

init()

wishList = WishList()
classTable = ClassTable()

wishList.append("MATH1136G").withPriority(10)  # 微积分
wishList.append("PHY1001G").withPriority(9)  # 大学物理
wishList.append("MATH1138F").withPriority(9)  # 常微分方程
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

wishList.append("ISEE0401G").withPriority(2)

# selectClass(classTable, wishList)
#
# print(classTable.classes)

# todo: 增加课程需求：这一门课的所有志愿必须是同一时间段。
# todo: (feat) OneOf
# todo: (feat) 显示未满足的心愿
