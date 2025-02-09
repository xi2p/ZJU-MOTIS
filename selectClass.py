"""
这个模块负责执行选课算法
"""
from typing import *
import data
from Entities.WishList import WishList
from Entities.Course import Course
from Entities.ClassTable import ClassTable
from Entities.Class import Class
import Entities.Time as Time
import Entities.Constants as Constants


def calculateClassRate(course: Course):
    """
    为一个课程内的所有班级计算评分，并填充到class.rate里面
    :param course: 课程对象
    """
    allClassOfCourse = data.filterClassSetByCondition(
        lambda x: Course.isEqualCourseCode(course.courseCode, x.course.courseCode)
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
    #       preferredTeacher    +1.5分;    goodTeacher +1分;
    #       normalTeacher       +0.5分;    badTeacher  -0分;
    #       这里不作扣分。因为如果扣分，可能存在一门课选上反而总体评分更低的情况。
    # 注：不在任何teacherGroup的教师视作normalTeacher。这是因为teacherGroup是用户给的特殊标记，反映其主观意愿。程序不会自动给教师分组，只会按照排名给班级计分。
    # step 1
    teacherToRate = {}
    for class_ in allClassOfCourse:
        for teacher in class_.teacherNames:
            if teacher not in teacherToRate:
                teacherToRate[teacher] = data.getTeacherRate(teacher)
    classAndRateByTeacher: List[
        List[Tuple[Class, float]]] = []  # [[(class1, 9.9), (class2, 9.9), ...], [(class3, 9.8), ...], ...]
    classNotIncluded = []
    # step 2
    for class_ in allClassOfCourse:
        rate = data.NULL_TEACHER_SCORE
        for teacher in class_.teacherNames:
            rate = max(rate, teacherToRate.get(teacher, data.NULL_TEACHER_SCORE))
        if rate != data.NULL_TEACHER_SCORE:
            inserted = False
            for classAndRateList in classAndRateByTeacher:
                if classAndRateList[0][1] == rate:
                    classAndRateList.append((class_, rate))
                    inserted = True
                    break
            if not inserted:
                classAndRateByTeacher.append([(class_, rate)])
        else:
            classNotIncluded.append(class_)
    # step 3/4/5
    classAndRateByTeacher.sort(key=lambda x: x[0][1], reverse=True)
    classToRateByTeacher = {}
    for classAndRateList in classAndRateByTeacher:
        for class_, rate in classAndRateList:
            classToRateByTeacher[class_] = (1 - classAndRateByTeacher.index(classAndRateList)
                                                / len(classAndRateByTeacher))
    for class_ in classNotIncluded:
        classToRateByTeacher[class_] = 0.5
    # step 6
    for class_ in allClassOfCourse:
        maxAddition = 0
        for teacher in class_.teacherNames:
            if teacher in course.teacherGroup[0]:
                maxAddition = max(maxAddition, 1.5)
            elif teacher in course.teacherGroup[1]:
                maxAddition = max(maxAddition, 1)
            elif teacher in course.teacherGroup[2]:
                maxAddition = max(maxAddition, 0.5)
            elif teacher in course.teacherGroup[3]:
                maxAddition = max(maxAddition, 0)
            else:
                maxAddition = max(maxAddition, 0.5)
        classToRateByTeacher[class_] += maxAddition

    # 给所有班级根据时间评分
    # 评分方法：
    # 1.    遍历所有班级，查询这个班级的ClassTime。
    #       如果这个时间在course.expectedTimeList里面，这个班级评分为1分
    #       如果这个时间在course.avoidTimeList里面，这个班级评分为0分
    #       如果这个时间不在course.expectedTimeList和course.avoidTimeList里面，这个班级评分为0.5分
    # 2.    产生一个{班级-分数}的字典，存储所有班级的分数
    classToRateByTime = {}
    for class_ in allClassOfCourse:
        rate = 0.5
        for classTime in course.expectedTimeList:
            if class_.classTime.isOverlapped(classTime):
                rate = 1
                break
        for classTime in course.avoidTimeList:
            if class_.classTime.isOverlapped(classTime):
                rate = 0
                break
        classToRateByTime[class_] = rate

    # 给所有班级根据选上的概率评分
    # 1.    按照class内部的数据，算出选上的概率P。P=余量/待选人数。
    # 2.    将所有的P映射到[0, 1]区间，得到一个P'。P'即为这个班级的概率评分。
    # 3.    产生一个{班级-分数}的字典，存储所有班级的分数，并
    classToRateByPossibility = {}
    minPossibility = 1
    maxPossibility = -1
    for class_ in allClassOfCourse:
        if class_.available <= 0:
            possibility = 0
        elif class_.unfiltered <= class_.available:
            possibility = 1
        else:
            possibility = class_.available / class_.unfiltered
        minPossibility = min(minPossibility, possibility)
        maxPossibility = max(maxPossibility, possibility)
        classToRateByPossibility[class_] = possibility
    # 映射到[0, 1]区间

    for class_ in allClassOfCourse:
        if maxPossibility == minPossibility:
            rate = 0
        else:
            rate = (
                    (classToRateByPossibility[class_] - minPossibility)
                    / (maxPossibility - minPossibility)
            )
        classToRateByPossibility[class_] = rate
        class_.possibility = rate

    # 合并评分
    # 合并方法： 遍历所有班级，取出各个评分。将各个评分加权相加，得到最终评分。权值可由用户设定。
    for class_ in allClassOfCourse:
        rate = (classToRateByTeacher[class_] * course.teacherFactor
                + classToRateByTime[class_] * course.timeFactor
                + classToRateByPossibility[class_] * course.possibilityFactor)
        class_.rate = rate


def getOptimalCandidatesWithinClassSet(classSet: List[Class]) -> List[Class]:
    """
    找出一个班级集合内的最优志愿组合。本方法应由getCourseCandidateCombination调用。
    :param classSet: 班级集合。里面的班级应该是同一门课程的。
    :return: 按照用户设定的条件解除的最优的三个班级（如果有的话）
    """
    # 先获取是哪门课
    course = classSet[0].course

    # 先初步筛选，去掉不符合条件的班级
    # 如果用户有指定一定要选择的教师
    if course.requiredTeachers:
        classSet = data.filterClassSetByCondition(
            lambda x: all([teacherName in x.course.requiredTeachers for teacherName in x.teacherNames]),
            classSet
        )
    classSet = data.filterClassSetByCondition(
        lambda x: not any([teacherName in x.course.avoidedTeachers for teacherName in x.teacherNames]),
        classSet
    )
    if not classSet:
        raise ValueError("No class in classSet fits teacher requirement")

    # 接下来开始从classSet里面选出最优的三个班级
    # 选班的策略：

    # 1.    将课程按照possibility进行分类，分为hot, normal, cold三个列表。列表内按照评分从高到低排序。
    #       将P'[-1, -1/3)划为hot，(1/3, 1]划为cold，(-1/3, 1/3)划为normal
    # 2.    按照course.strategy的设定，从hot, normal, cold里面选出相应数量的评分前n的班级。
    #       如果某个类别的班级数量不够，就从更冷门类别里面选。如果班级总数小于3，就不选那么多。
    hotClasses = []
    normalClasses = []
    coldClasses = []
    for class_ in classSet:
        if class_.possibility >= 1 / 3:
            coldClasses.append(class_)
        elif class_.possibility <= -1 / 3:
            hotClasses.append(class_)
        else:
            normalClasses.append(class_)

    hotClasses.sort(key=lambda x: x.rate, reverse=True)
    normalClasses.sort(key=lambda x: x.rate, reverse=True)
    coldClasses.sort(key=lambda x: x.rate, reverse=True)
    hotNumber = min(course.strategy.hot, len(hotClasses))
    normalNumber = min(course.strategy.normal + course.strategy.hot - hotNumber, len(normalClasses))
    coldNumber = min(course.strategy.cold + course.strategy.normal + course.strategy.hot - hotNumber - normalNumber,
                      len(coldClasses))
    result = []
    for i in range(hotNumber):
        result.append(hotClasses[i])
    for i in range(normalNumber):
        result.append(normalClasses[i])
    for i in range(coldNumber):
        result.append(coldClasses[i])
    return result


# 例如， CAD设计有周三班和周五班。由于志愿可以选三个，所以可以有三种情况：
# 时间占据情况1：周三
# 时间占据情况2：周五
# 时间占据情况3：周三和周五（两个班的志愿都先报上）
# 然后再对每个课程进行深搜，找到这个优先级的课表最优解
def getCourseCandidateCombination(course: Course, classTable: ClassTable) -> List[List[Class]]:
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
    classTimeSet: List[List[Time.ClassTime | int]] = []
    # classTimeSet 用于存储所有班级的时间占据情况
    # 每一个元素是一个列表，列表内的第一个元素是ClassTime
    # 第二个元素是一个数字，表示有几个班是这个时间

    for class_ in data.filterClassSetByCondition(
            lambda x: Course.isEqualCourseCode(course.courseCode, x.course.courseCode)):
        if class_.classTime not in [i[0] for i in classTimeSet]:
            classTimeSet.append([class_.classTime, 0])
        index = 0
        for i in range(len(classTimeSet)):
            if class_.classTime == classTimeSet[i][0]:
                index = i
                break
        classTimeSet[index][1] += 1

    # 递归找出所有可能的时间组合。每个组合内最多含有三个班，至少含有一个班
    def _getTimeCombination(_result, _current, _index):
        """
        递归函数找出所有可能的时间组合
        :param _result: 存储结果的列表
        :param _current: 当前的时间组合是怎么样的
        :param _index: 现在在处理class_time_set的第几个元素
        """
        # print(_current)
        if _index == len(classTimeSet):
            # 达到递归终点。检查当前_current是否是一个时间不同于_result内所有元素的组合
            _currentTimeSet = []
            for i in _current:
                if i[1] != 0:
                    _currentTimeSet.append(i[0])
            if _currentTimeSet not in _result:
                _result.append(_currentTimeSet)
            # 出栈
            index = 0
            for i in range(len(_current)):
                if _current[i][0] == classTimeSet[_index - 1][0]:
                    index = i
                    break
            _current.pop(index)
            return

        # 先看看已经选了几个志愿
        selectedNum = 0
        for i in _current:
            selectedNum += i[1]
        if selectedNum >= 3:
            # 达到递归终点。检查当前_current是否是一个时间不同于_result内所有元素的组合
            _currentTimeSet = []
            for i in _current:
                if i[1] != 0:
                    _currentTimeSet.append(i[0])
            if _currentTimeSet not in _result:
                _result.append(_currentTimeSet)
            # 出栈
            index = 0
            for i in range(len(_current)):
                if _current[i][0] == classTimeSet[_index - 1][0]:
                    index = i
                    break
            _current.pop(index)

        for i in range(0, min(classTimeSet[_index][1], 3 - selectedNum) + 1):
            # 首先找到_current里是否已经有这个时间段的班，如果有，就改变其数量
            found = False
            for j in range(len(_current)):
                if _current[j][0] == classTimeSet[_index][0]:
                    _current[j][1] = i
                    found = True
                    break
            if not found:
                _current.append([classTimeSet[_index][0], i])
            _getTimeCombination(_result, _current, _index + 1)

    _timeDomainSet: List[List[Time.ClassTime]] = []  # 存储所有可能的时间组合
    current: List[List[Time.ClassTime | int]] = []
    _getTimeCombination(_timeDomainSet, current, 0)
    _timeDomainSet = [i for i in _timeDomainSet if i != []]  # 去除空列表

    # _timeDomainSet 内的元素是一个列表，列表内的元素是ClassTime对象
    # 现在把每个列表的多个元素合并成一个元素
    timeDomainSet: List[Time.ClassTime] = []
    for i in _timeDomainSet:
        _timeDomain = i[0]
        for j in i[1:]:
            _timeDomain = _timeDomain + j
        timeDomainSet.append(_timeDomain)

    # 删去与现有课表冲突的时间
    timeDomainSet = [i for i in timeDomainSet if not classTable.isConflict(
        Class("", course, [], "",
              i, [],
              0, 0, "", "", "", ""
              )
    )]
    # 现在time_domain_set内存储了所有可能的时间组合
    # 现在要找出每个时间组合内的最优志愿组合
    optimalCandidateCombination = []
    for timeDomain in timeDomainSet:
        timeDomain: Time.ClassTime
        # 这里不需要递归。根据Course内部的策略，找出当前时间下的最优志愿组合
        # 首先先找出所有符合当前时间要求的班级
        classSet = data.filterClassSetByCondition(
            lambda x: x.classTime in timeDomain
                      and Course.isEqualCourseCode(course.courseCode, x.course.courseCode)
        )
        # 然后按照策略找出class_set里面最好的三个班级（如果有的话）
        optimalClassSet = getOptimalCandidatesWithinClassSet(classSet)  # 存储最优的三个班级
        optimalCandidateCombination.append(optimalClassSet)

    # 去重
    result = []
    for i in optimalCandidateCombination:
        if i not in result:
            result.append(i)
    return result


def getClassTableRateList(classTable: ClassTable, wishList: WishList) -> List[float | None]:
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
    maxPriority = wishList.maxPriority
    result: List[float | None] = [None for _ in range(maxPriority + 1)]

    courseToRate = {}
    for class_ in classTable.classes:
        if class_.course.status == Constants.CourseStatus.SELECTED and class_.course not in wishList.wishes:
            continue  # 已经选上了并且没有要求优化，不再参与运算
        priority = class_.course.priority
        if class_.course in courseToRate:
            if class_.rate > courseToRate[class_.course.courseCode]:
                result[maxPriority - priority] -= courseToRate[class_.course.courseCode]
                result[maxPriority - priority] += class_.rate
                courseToRate[class_.course.courseCode] = class_.rate
        else:
            courseToRate[class_.course.courseCode] = class_.rate
            if result[maxPriority - priority] is None:
                result[maxPriority - priority] = 0
            result[maxPriority - priority] += class_.rate

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


def selectClass(classTable: ClassTable, wishList: WishList, doubleVar) -> ClassTable:
    """
    选课算法。调用这个函数的时候，所有数据应该都已经加载好了。
    :param classTable: 课程表对象
    :param wishList: 愿望列表对象
    :param doubleVar: 用于显示进度条
    :return: 选课结果。选课结果也会直接写入classTable对象。
    """

    if not wishList.wishes:  # 没有课程需要选
        return classTable

    wishList.wishes.sort(key=lambda x: x.priority, reverse=True)
    # 按照优先级分组
    priorityGroup: Dict[int, List[Course]] = {}  # 优先级-课程列表
    for wish in wishList.wishes:
        calculateClassRate(wish)  # 在这里计算好所有课程的评分，以便后续使用
        if wish.priority not in priorityGroup:
            priorityGroup[wish.priority] = []
        priorityGroup[wish.priority].append(wish)

    # for class_ in classTable.classes:
    #     calculateClassRate(class_.course)

    wishList.maxPriority = max(priorityGroup.keys())
    bestClassTable = ClassTable()
    classTable.copyTo(bestClassTable)
    bestRateList = getClassTableRateList(classTable, wishList)

    def _select(_priority: int, index: int):
        """
        选课算法的递归函数，负责选出当前这一个优先级的课程表。一次处理一个课程。
        :param _priority: 当前优先级
        :param index: 当前正在处理的课程在priority_group[priority]中的索引

        课程表对象classTable是外部变量
        """
        if _priority not in priorityGroup:
            return
        if index == len(priorityGroup[_priority]):  # 当前优先级的课程已经全部处理完了，可以评估这个课表了
            rateList = getClassTableRateList(classTable, wishList)
            if rateListCmp(rateList, bestRateList) > 0:
                bestRateList.clear()
                bestRateList.extend(rateList)
                bestClassTable.clear()
                bestClassTable.extend(classTable)
            return
        # 现在处理的是priority_group[priority][index]这门课程
        course = priorityGroup[_priority][index]

        # 如果这门课程是已选上的，那么就尝试找出比当前已选上的教学班更好的教学班。并把它放到已选上的教学班的前面。
        # 为了保证修改最少的代码，这里将已选上的课程从classTable里面删除，模拟他是一个未选上的课程
        # 之后再加回去
        confirmedClass = None
        if course.status == Constants.CourseStatus.SELECTED:
            confirmedClass = data.filterClassSetByCondition(
                lambda x: x.course.courseCode == course.courseCode and x.status == Constants.ClassStatus.CONFIRMED
            )[0]
            classTable.removeClass(confirmedClass)     # 删除已选上的教学班

        # 获取这门课程的志愿组合，依次尝试
        candidateCombinations = getCourseCandidateCombination(course, classTable)
        for candidateCombination in candidateCombinations:
            candidateCombination: List[Class]
            # getCourseCandidateCombination已经保证各candidate_combination能插入classTable且按照评分从高到低排序
            # 对于已经选上的课程，getCourseCandidateCombination返回的candidate_combination里面可能包含已选上的教学班
            # 所以不用再检查ClassTable是否冲突，直接append即可（再说了，append内部也会检查冲突，真冲突就报错了）

            # 这个地方要分两种情况：
            # 1.    这门课程是未选上的课程。这种情况下，直接将candidate_combination里面的班级加入classTable即可。
            # 2.    这门课程是已选上的课程。这种情况下，candidate_combination里面的班级可能有已选上的班级。
            #       如果candidate_combination里没有已经选上的班级，由于本程序不会退选已选上的课程，所以取candidate_combination里面的前两个班级即可，再加入已选上的班级。
            #       接着按顺序把班级添加进classTable，添加到那个已选上的课程时，就可以停止了。
            if course.status == Constants.CourseStatus.NOT_SELECTED:
                for class_ in candidateCombination:
                    classTable.append(class_)
            else:
                # 最极端的情况下，系统可以在已选课程前再插入两个更好的教学班
                candidateCombination = candidateCombination[:2]
                candidateCombination.append(confirmedClass)
                # 再依次加入candidate_combination里面的班级，直到加入已选上的班级
                for class_ in candidateCombination:
                    classTable.append(class_)
                    if class_ == confirmedClass:
                        break
            # 递归调用_select，处理下一个课程
            _select(_priority, index + 1)
            # 撤销本次尝试，也要分两种情况
            # 1.    这门课程是未选上的课程。这种情况下，直接将candidate_combination里面的班级从classTable里面删除即可。
            # 2.    这门课程是已选上的课程。按照次序，将candidate_combination里面的班级从classTable里面删除。
            #       直到删除已选上的班级为止。
            if course.status == Constants.CourseStatus.NOT_SELECTED:
                for class_ in candidateCombination:
                    classTable.removeClass(class_)
            else:
                for class_ in candidateCombination:
                    classTable.removeClass(class_)
                    if class_ == confirmedClass:
                        break
        # 恢复已选上的课程
        if course.status == Constants.CourseStatus.SELECTED:
            classTable.append(confirmedClass)

        _select(_priority, index + 1)  # 不选这门课程也要尝试/不做更改也要尝试

    # 逐优先级开始递归调用_select，选出这个优先级下的最优课表
    for i, priority in enumerate(sorted(list(priorityGroup.keys()), reverse=True)):
        _select(priority, 0)
        bestClassTable.copyTo(classTable)  # 保存这一个优先级的最优课表。下一个优先级的课程要在这个基硃上继续选课
        doubleVar.set(i / len(priorityGroup.keys()))
    doubleVar.set(1)
    return classTable
