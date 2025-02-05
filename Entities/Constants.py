# 默认Strategy对象的数据源
STRATEGY_DEFAULT = (1, 2, 0)


class CourseSort:
    GeneralCourse = "通识"
    ProfessionalBasicCourse = "专业基础课程"
    ProfessionalCourse = "专业课"


class CourseBelonging:
    PoliticalMilitary = "政治类\\军体类"
    ForeignLanguage = "外语类"
    Computer = "计算机类"
    NaturalScience = "自然科学通识类"
    ChineseTradition = "中华传统"
    WorldCivilization = "世界文明"
    ContemporarySociety = "当代社会"
    ScienceAndTechnologyInnovation = "科技创新"
    ArtisticAesthetics = "文艺审美"
    LifeExploration = "生命探索"
    CraftAndSkill = "博雅技艺"


class CourseMark:
    GeneralCore = "通识核心课程"


class CourseIdentification:
    ArtEducation = "美育类"
    LaborEducation = "劳育类"
    InnovationAndEntrepreneurship = "创新创业类"
    PsychologicalHealth = "心理健康类"


class Weekday:
    Monday = 1
    Tuesday = 2
    Wednesday = 3
    Thursday = 4
    Friday = 5
    Saturday = 6
    Sunday = 7


class CourseStatus:
    # 课程状态只有两种：已选和未选。待筛选也算未选。
    NOT_SELECTED = "未选"
    SELECTED = "已选"


class ClassStatus:
    NOT_SELECTED = "未选"
    TO_BE_FILTERED = "待筛选"
    CONFIRMED = "已选上"