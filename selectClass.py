"""
这个模块负责执行选课算法
"""
import sys
from typing import *
import data
import Entities.WishList as WishList
import Entities.Course as Course
import Entities.ClassTable as ClassTable
import Entities.Class as Class
import Entities.Time as Time
import Entities.Constants as Constants
from Entities.Strategy import Strategy
from network import updateClassJson
from time import time




def calculateClassRate(course: Course.Course):
    """
    为一个课程内的所有班级计算评分，并填充到class.rate里面
    :param course: 课程对象
    """
    all_class_of_course = data.filterClassSetByCondition(
        lambda x: Course.Course.isEqualCourseCode(course.courseCode, x.course.courseCode)
    )
    # 给所有班级根据教师评分
    # 评分方法：
    # 1.    获取classSet内所有教师的査老师评分。如果某个教师查不到，就先跳过他。产生一个{教师-分数}的字典
    # 2.    给每个班级评分。班级教师的分数就直接作为班级的分数。如果一个班有多个教师，取最高分。
    # 3.    把这些班级按照分数从高到低排序。其(1-索引/长度)就是班级的分数。同一个老师的班级分数相同。
    # 4.    第2步中有的班级因为其教师查不到分数而导致班级没有分数。这些班级的分数就是0.5
    # 5.    产生一个{班级-分数}的字典，存储所有班级的分数
    # 6.    检查course的teacherGroup。遍历每个班级，如果班级的教师在teacherGroup里面，就给他加对应的分
    #       如果一个班里有多个教师在teacherGroup里面，就取最高分加上
    #       preferredTeacher    +2分;    goodTeacher +1分;
    #       normalTeacher       +0分;    badTeacher  -1分;
    # 注：不在任何teacherGroup的教师视作normalTeacher。这是因为teacherGroup是用户给的特殊标记，反映其主观意愿。程序不会自动给教师分组，只会按照排名给班级计分。
    # step 1
    teacher_to_rate = {}
    for class_ in all_class_of_course:
        for teacher in class_.teacherNames:
            if teacher not in teacher_to_rate:
                teacher_to_rate[teacher] = data.getTeacherRate(teacher)
    class_and_rate_by_teacher: List[
        List[Tuple[Class.Class, float]]] = []  # [[(class1, 9.9), (class2, 9.9), ...], [(class3, 9.8), ...], ...]
    class_not_included = []
    # step 2
    for class_ in all_class_of_course:
        rate = data.NULL_TEACHER_SCORE
        for teacher in class_.teacherNames:
            rate = max(rate, teacher_to_rate.get(teacher, data.NULL_TEACHER_SCORE))
        if rate != data.NULL_TEACHER_SCORE:
            inserted = False
            for class_and_rate_list in class_and_rate_by_teacher:
                if class_and_rate_list[0][1] == rate:
                    class_and_rate_list.append((class_, rate))
                    inserted = True
                    break
            if not inserted:
                class_and_rate_by_teacher.append([(class_, rate)])
        else:
            class_not_included.append(class_)
    # step 3/4/5
    class_and_rate_by_teacher.sort(key=lambda x: x[0][1], reverse=True)
    class_to_rate_by_teacher = {}
    for class_and_rate_list in class_and_rate_by_teacher:
        for class_, rate in class_and_rate_list:
            class_to_rate_by_teacher[class_] = (1 - class_and_rate_by_teacher.index(class_and_rate_list)
                                                / len(class_and_rate_by_teacher))
    for class_ in class_not_included:
        class_to_rate_by_teacher[class_] = 0.5
    # step 6
    for class_ in all_class_of_course:
        max_addition = -2
        for teacher in class_.teacherNames:
            if teacher in course.teacherGroup[0]:
                max_addition = max(max_addition, 2)
            elif teacher in course.teacherGroup[1]:
                max_addition = max(max_addition, 1)
            elif teacher in course.teacherGroup[2]:
                max_addition = max(max_addition, 0)
            elif teacher in course.teacherGroup[3]:
                max_addition = max(max_addition, -1)
        if max_addition != -2:
            class_to_rate_by_teacher[class_] += max_addition

    # 给所有班级根据时间评分
    # 评分方法：
    # 1.    遍历所有班级，查询这个班级的ClassTime。
    #       如果这个时间在course.expectedTimeList里面，这个班级评分为1分
    #       如果这个时间在course.avoidTimeList里面，这个班级评分为-1分
    #       如果这个时间不在course.expectedTimeList和course.avoidTimeList里面，这个班级评分为0分
    # 2.    产生一个{班级-分数}的字典，存储所有班级的分数
    class_to_rate_by_time = {}
    for class_ in all_class_of_course:
        rate = 0
        for class_time in course.expectedTimeList:
            if class_.classTime.isOverlapped(class_time):
                rate = 1
                break
        for class_time in course.avoidTimeList:
            if class_.classTime.isOverlapped(class_time):
                rate = -1
                break
        class_to_rate_by_time[class_] = rate

    # 给所有班级根据选上的概率评分
    # 1.    按照class内部的数据，算出选上的概率P。P=余量/待选人数。
    # 2.    将所有的P映射到[-1, 1]区间，得到一个P'。P'即为这个班级的概率评分。
    # 3.    产生一个{班级-分数}的字典，存储所有班级的分数，并
    class_to_rate_by_possibility = {}
    min_possibility = 1
    max_possibility = -1
    for class_ in all_class_of_course:
        if class_.available <= 0:
            possibility = 0
        elif class_.unfiltered <= class_.available:
            possibility = 1
        else:
            possibility = class_.available / class_.unfiltered
        min_possibility = min(min_possibility, possibility)
        max_possibility = max(max_possibility, possibility)
        class_to_rate_by_possibility[class_] = possibility
    # 映射到[-1, 1]区间

    for class_ in all_class_of_course:
        if max_possibility == min_possibility:
            rate = 0
        else:
            rate = (
                    (class_to_rate_by_possibility[class_] - min_possibility)
                    / (max_possibility - min_possibility) * 2
            )
        class_to_rate_by_possibility[class_] = rate
        class_.possibility = rate

    # 合并评分
    # 合并方法： 遍历所有班级，取出各个评分。将各个评分加权相加，得到最终评分。权值可由用户设定。
    for class_ in all_class_of_course:
        rate = (class_to_rate_by_teacher[class_] * course.teacherFactor
                + class_to_rate_by_time[class_] * course.timeFactor
                + class_to_rate_by_possibility[class_] * course.possibilityFactor)
        class_.rate = rate

    # 至此，所有班级已经按照评分规则由分数高到低排序。
    # 对应关系存储在class_and_rate_list里面
    # 格式：[(class1, 9.9), (class2, 9.8), ...]
    # hot_classes, normal_classes, cold_classes里面存储了热门班级，普通班级，冷门班级


def getOptimalCandidatesWithinClassSet(classSet: List[Class.Class]) -> List[Class.Class]:
    """
    找出一个班级集合内的最优志愿组合。本方法应由getCourseCandidateCombination调用。
    :param classSet: 班级集合。里面的班级应该是同一门课程的。
    :return: 按照用户设定的条件解除的最优的三个班级（如果有的话）
    """
    # 先获取是哪门课
    course = classSet[0].course

    # 教师的选择有三种情况：
    if course.requiredTeachers:
        # 情况一：用户指定一定选择的教师
        classSet = data.filterClassSetByCondition(
            lambda x: all([teacherName in x.course.requiredTeachers for teacherName in x.teacherNames]),
            classSet
        )
    classSet = data.filterClassSetByCondition(
        lambda x: not any([teacherName in x.course.avoidedTeachers for teacherName in x.teacherNames]),
        classSet
    )
    if not classSet:
        raise ValueError("No class in classSet has required teachers")

    # 接下来开始从classSet里面选出最优的三个班级
    # 选班的策略：

    # 1.    将课程按照possibility进行分类，分为hot, normal, cold三个列表。列表内按照评分从高到低排序。
    #       将P'[-1, -1/3)划为hot，(1/3, 1]划为cold，(-1/3, 1/3)划为normal
    # 2.    按照course.strategy的设定，从hot, normal, cold里面选出相应数量的评分前n的班级。
    #       如果某个类别的班级数量不够，就从更冷门类别里面选。如果班级总数小于3，就不选那么多。
    hot_classes = []
    normal_classes = []
    cold_classes = []
    for class_ in classSet:
        if class_.possibility >= 1 / 3:
            cold_classes.append(class_)
        elif class_.possibility <= -1 / 3:
            hot_classes.append(class_)
        else:
            normal_classes.append(class_)

    hot_classes.sort(key=lambda x: x.rate, reverse=True)
    normal_classes.sort(key=lambda x: x.rate, reverse=True)
    cold_classes.sort(key=lambda x: x.rate, reverse=True)
    hot_number = min(course.strategy.hot, len(hot_classes))
    normal_number = min(course.strategy.normal + course.strategy.hot - hot_number, len(normal_classes))
    cold_number = min(course.strategy.cold + course.strategy.normal + course.strategy.hot - hot_number - normal_number,
                      len(cold_classes))
    result = []
    for i in range(hot_number):
        result.append(hot_classes[i])
    for i in range(normal_number):
        result.append(normal_classes[i])
    for i in range(cold_number):
        result.append(cold_classes[i])
    return result


# 例如， CAD设计有周三班和周五班。由于志愿可以选三个，所以可以有三种情况：
# 时间占据情况1：周三
# 时间占据情况2：周五
# 时间占据情况3：周三和周五（两个班的志愿都先报上）
# 然后再对每个课程进行深搜，找到这个优先级的课表最优解
def getCourseCandidateCombination(course: Course.Course, classTable: ClassTable.ClassTable) -> List[List[Class.Class]]:
    """
    获取某门课程的不同时间占据情况下的最优的志愿组合。返回的时间组合是能插入ClassTable的。
    :param course: 课程对象
    :param classTable: 课表对象
    :return: [[一号志愿, 二号志愿, ...], ...] 内部各列表总体占据的时间互异
    "时间占据"说明如下：
    例如， CAD设计有周三班和周五班。由于志愿可以选三个，所以可以有三种情况：
    时间占据情况1：周三
    时间占据情况2：周五
    时间占据情况3：周三和周五（两个班的志愿都先报上）
    """
    # 先获取这门课程的所有班级有哪些时间
    class_time_set: List[List[Time.ClassTime | int]] = []
    # class_time_set 用于存储所有班级的时间占据情况
    # 每一个元素是一个列表，列表内的第一个元素是ClassTime
    # 第二个元素是一个数字，表示有几个班是这个时间

    for class_ in data.filterClassSetByCondition(
            lambda x: Course.Course.isEqualCourseCode(course.courseCode, x.course.courseCode)):
        if class_.classTime not in [i[0] for i in class_time_set]:
            class_time_set.append([class_.classTime, 0])
        index = 0
        for i in range(len(class_time_set)):
            if class_.classTime == class_time_set[i][0]:
                index = i
                break
        class_time_set[index][1] += 1

    # 递归找出所有可能的时间组合。每个组合内最多含有三个班，至少含有一个班
    def _getTimeCombination(_result, _current, _index):
        """
        递归函数找出所有可能的时间组合
        :param _result: 存储结果的列表
        :param _current: 当前的时间组合是怎么样的
        :param _index: 现在在处理class_time_set的第几个元素
        """
        # print(_current)
        if _index == len(class_time_set):
            # 达到递归终点。检查当前_current是否是一个时间不同于_result内所有元素的组合
            _current_time_set = []
            for i in _current:
                if i[1] != 0:
                    _current_time_set.append(i[0])
            if _current_time_set not in _result:
                _result.append(_current_time_set)
            # 出栈
            index = 0
            for i in range(len(_current)):
                if _current[i][0] == class_time_set[_index - 1][0]:
                    index = i
                    break
            _current.pop(index)
            return

        # 先看看已经选了几个志愿
        selected_num = 0
        for i in _current:
            selected_num += i[1]
        if selected_num >= 3:
            # 达到递归终点。检查当前_current是否是一个时间不同于_result内所有元素的组合
            _current_time_set = []
            for i in _current:
                if i[1] != 0:
                    _current_time_set.append(i[0])
            if _current_time_set not in _result:
                _result.append(_current_time_set)
            # 出栈
            index = 0
            for i in range(len(_current)):
                if _current[i][0] == class_time_set[_index - 1][0]:
                    index = i
                    break
            _current.pop(index)

        for i in range(0, min(class_time_set[_index][1], 3 - selected_num) + 1):
            # 首先找到_current里是否已经有这个时间段的班，如果有，就改变其数量
            found = False
            for j in range(len(_current)):
                if _current[j][0] == class_time_set[_index][0]:
                    _current[j][1] = i
                    found = True
                    break
            if not found:
                _current.append([class_time_set[_index][0], i])
            _getTimeCombination(_result, _current, _index + 1)

    _time_domain_set: List[List[Time.ClassTime]] = []  # 存储所有可能的时间组合
    current: List[List[Time.ClassTime | int]] = []
    _getTimeCombination(_time_domain_set, current, 0)
    _time_domain_set = [i for i in _time_domain_set if i != []]  # 去除空列表

    # _time_domain_set 内的元素是一个列表，列表内的元素是ClassTime对象
    # 现在把每个列表的多个元素合并成一个元素
    time_domain_set: List[Time.ClassTime] = []
    for i in _time_domain_set:
        _time_domain = i[0]
        for j in i[1:]:
            _time_domain = _time_domain + j
        time_domain_set.append(_time_domain)

    # 删去与现有课表冲突的时间
    time_domain_set = [i for i in time_domain_set if not classTable.isConflict(
        Class.Class("", course, [], "",
                    i, [],
                    0, 0, "", "", "", ""
                    )
    )]
    # 现在time_domain_set内存储了所有可能的时间组合
    # 现在要找出每个时间组合内的最优志愿组合
    optimal_candidate_combination = []
    for time_domain in time_domain_set:
        time_domain: Time.ClassTime
        # 这里不需要递归。根据Course内部的策略，找出当前时间下的最优志愿组合
        # 首先先找出所有符合当前时间要求的班级
        class_set = data.filterClassSetByCondition(
            lambda x: x.classTime in time_domain
                      and Course.Course.isEqualCourseCode(course.courseCode, x.course.courseCode)
        )
        # 然后按照策略找出class_set里面最好的三个班级（如果有的话）
        optimal_class_set = getOptimalCandidatesWithinClassSet(class_set)  # 存储最优的三个班级
        optimal_candidate_combination.append(optimal_class_set)

    # 去重
    result = []
    for i in optimal_candidate_combination:
        if i not in result:
            result.append(i)
    return result


def getClassTableRateList(classTable: ClassTable.ClassTable, wishList: WishList.WishList) -> List[float | None]:
    """
    获取一个课表的评分列表。这个列表是评价一个课表的好坏的指标。
    列表内的元素是各优先级的得分。例如：[优先级3所有课程得分和，优先级2所有课程得分和，优先级1所有课程得分和， ...]
    一个课程可能有多个班级被选上。此时，这个课程的得分是所有班级得分的最大值。
    列表元素中None是最小值，表示这个优先级没有课程被选上。None比所有数字都小。
    :param classTable: 课表对象
    :param wishList: 愿望清单对象。用于确定result的长度
    :return: 评分列表
    """
    # 找出最大优先级
    max_priority = wishList.max_priority
    result: List[float | None] = [None for _ in range(max_priority + 1)]

    course_to_rate = {}
    for class_ in classTable.classes:  # classTable内的班级必然是愿望清单上的
        if class_.course.status == Constants.CourseStatus.SELECTED:
            continue # 已经选上了，不再参与运算
        priority = class_.course.priority
        if class_.course in course_to_rate:
            if class_.rate > course_to_rate[class_.course.courseCode]:
                result[max_priority - priority] -= course_to_rate[class_.course.courseCode]
                result[max_priority - priority] += class_.rate
                course_to_rate[class_.course.courseCode] = class_.rate
        else:
            course_to_rate[class_.course.courseCode] = class_.rate
            if result[max_priority - priority] is None:
                result[max_priority - priority] = 0
            result[max_priority - priority] += class_.rate

    return result


def rateListCmp(a: List[float | None], b: List[float | None]) -> int:
    """
    评分列表比较函数
    :param a: 评分列表1
    :param b: 评分列表2
    :return: a > b: 1; a = b: 0; a < b: -1
    """
    for i in range(len(a)):
        if a[i] is None and b[i] is None:
            continue
        if a[i] is None:
            return -1
        if b[i] is None:
            return 1
        if a[i] > b[i]:
            return 1
        if a[i] < b[i]:
            return -1
    return 0


def selectClass(classTable: ClassTable.ClassTable, wishList: WishList) -> ClassTable.ClassTable:
    """
    选课算法。调用这个函数的时候，所有数据应该都已经加载好了。
    :param classTable: 课程表对象
    :param wishList: 愿望列表对象
    :return: 选课结果。选课结果也会直接写入classTable对象。
    """

    # 原wishList中有一些课程的状态是已选上，那么这些课程就直接加入课表，也不参与后面的计算
    wishes_to_remove = []
    for wish in wishList.wishes:
        if wish.status == Constants.CourseStatus.SELECTED:  # 已经选上了，那就不用选了
            calculateClassRate(wish)
            classes = data.filterClassSetByCondition(
                lambda x: (
                    Course.Course.isEqualCourseCode(wish.courseCode, x.course.courseCode)
                    and x.status == Constants.ClassStatus.CONFIRMED
                )
            )
            for class_ in classes:
                classTable.append(class_)
            wishes_to_remove.append(wish)

    for wish in wishes_to_remove:
        wishList.wishes.remove(wish)

    if not wishList.wishes:     # 没有课程需要选
        return classTable

    wishList.wishes.sort(key=lambda x: x.priority, reverse=True)
    # 按照优先级分组
    priority_group : Dict[int, List[Course]] = {}       # 优先级-课程列表
    for wish in wishList.wishes:
        calculateClassRate(wish)  # 在这里计算好所有课程的评分，以便后续使用
        if wish.priority not in priority_group:
            priority_group[wish.priority] = []
        priority_group[wish.priority].append(wish)

    wishList.max_priority = max(priority_group.keys())
    best_class_table = ClassTable.ClassTable()
    classTable.copyTo(best_class_table)
    best_rate_list = getClassTableRateList(classTable, wishList)

    def _select(_priority: int, index: int):
        """
        选课算法的递归函数，负责选出当前这一个优先级的课程表。一次处理一个课程。
        :param _priority: 当前优先级
        :param index: 当前正在处理的课程在priority_group[priority]中的索引
        课程表对象classTable是外部变量
        """
        nonlocal best_rate_list
        if _priority not in priority_group:
            return
        if index == len(priority_group[_priority]):      # 当前优先级的课程已经全部处理完了，可以评估这个课表了
            rate_list = getClassTableRateList(classTable, wishList)
            if rateListCmp(rate_list, best_rate_list) > 0:
                best_rate_list.clear()
                best_rate_list.extend(rate_list)
                best_class_table.clear()
                best_class_table.extend(classTable)
            return
        # 现在处理的是priority_group[priority][index]这门课程
        course = priority_group[_priority][index]

        # 获取这门课程的志愿组合，依次尝试
        candidate_combinations = getCourseCandidateCombination(course, classTable)
        for candidate_combination in candidate_combinations:
            candidate_combination : List[Class.Class]
            # getCourseCandidateCombination已经保证各candidate_combination能插入classTable
            # 所以不用再检查ClassTable是否冲突，直接append即可（再说了，append内部也会检查冲突）
            for class_ in candidate_combination:
                classTable.append(class_)
            _select(_priority, index + 1)
            for class_ in candidate_combination:
                classTable.removeClass(class_)

        _select(_priority, index + 1)    # 不选这门课程也要尝试

    # 逐优先级开始递归调用_select，选出这个优先级下的最优课表
    for priority in range(wishList.max_priority, -1, -1):
        _select(priority, 0)
        best_class_table.copyTo(classTable)     # 保存这一个优先级的最优课表。下一个优先级的课程要在这个基硃上继续选课
    return classTable

