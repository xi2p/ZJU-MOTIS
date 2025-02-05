from interface import *

init()

wish_list = WishList()
class_table = ClassTable()

wish_list.append("MATH1136G").withPriority(10).avoidTeacher("薛儒英")  # 微积分
wish_list.append("PHY1001G").withPriority(9)  # 大学物理
wish_list.append("MATH1138F").withPriority(9).withStatus(0)  # 常微分方程
wish_list.append("ME1103F").withPriority(9).withStatus(0)  # 机械制图及CAD基础
wish_list.append("MARX1002G").withPriority(8)  # 史纲
wish_list.append("ME1002F").withPriority(7)  # 工程训练
wish_list.append("CS1241G").withPriority(7)  # 人工智能基础
wish_list.append("EDU2001G").withPriority(6).withStatus(0)  # 军事理论
wish_list.append("PHIL0902G").withPriority(6).withStatus(0)  # 希腊罗马哲学
wish_list.append("PPAE1100G").withPriority(5).withStatus(0)  # 体素
wish_list.append("PPAE0065G").withPriority(4).withStatus(0)  # 体育
wish_list.append("BEFS0402G").withPriority(3).withStatus(0)  # 微电子技术与纳米制造
wish_list.append("HIST0200G").withPriority(2).withStatus(0)  # 近代中日关系史

wish_list.append("ISEE0401G").withPriority(2)

selectClass(class_table, wish_list)

print(class_table.classes)