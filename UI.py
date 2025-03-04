import traceback
from tkinter import *
from tkinter.ttk import Button, Entry
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import showinfo, showerror, askokcancel
from lib import colorizer as idc
import idlelib.percolator as idp
from interface import *
import network
import threading
import time
from data import loadCourseData, loadClassData, initClassTable, courseData, filterClassSetByCondition


class ProgressBar(Canvas):
    def __init__(self, master, doubleVar: DoubleVar, stringVar: StringVar, width=600):
        super().__init__(master, width=width, height=40)
        self.progress = 0
        self.text = ''

        self.width = width
        self.height = 40

        self.doubleVar = doubleVar
        self.stringVar = stringVar

        self.frameNum = 60
        self.frames = [PhotoImage(file='./loading.gif', format='gif -index %i' % i) for i in range(self.frameNum)]

        self['bg'] = 'white'

        self.create_rectangle(8, 6, self.width - 8, 13, fill='white', outline='#14A8DD', tags='progress')
        self.create_text(30, 18, text=self.text + f'[{round(self.progress * 100)}%]', fill='#202020', anchor=NW,
                         tags='text')

        self.destroyed = False
        self.threadRunning = True
        thread = threading.Thread(target=self.updateImage)
        thread.daemon = True
        thread.start()

    def updateImage(self):
        index = 0
        while not self.destroyed:
            if index == 0:
                self.delete('gif')
            self.create_image(
                8, 18, image=self.frames[index], anchor=NW, tags='gif'
            )
            index = (index + 1) % self.frameNum

            if self.progress != self.doubleVar.get() or self.text != self.stringVar.get():
                self.create_rectangle(10, 8,
                                      10 + (self.width - 20) * self.doubleVar.get(), 11, fill='#14A8DD',
                                      outline='#14A8DD', tags='progress')
                self.progress = self.doubleVar.get()
                self.text = self.stringVar.get()
                self.itemconfigure('text', text=self.text+f'[{round(self.progress * 100)}%]')


                self.update()

            time.sleep(0.03)
        self.threadRunning = False

    def reset(self):
        self.delete(ALL)
        self.create_rectangle(8, 6, self.width - 8, 13, fill='white', outline='#14A8DD', tags='progress')
        self.create_text(30, 18, text=self.text + f'[{round(self.progress * 100)}%]', fill='#202020', anchor=NW,
                         tags='text')
        self.destroyed = True
        while self.threadRunning:
            time.sleep(0.01)
        self.destroyed = False
        self.threadRunning = True
        thread = threading.Thread(target=self.updateImage)
        thread.daemon = True
        thread.start()

    def destroy(self):
        self.destroyed = True
        super().destroy()


class ScheduleTable(Canvas):
    def __init__(self, master, classTable, half):
        """
        课程表Canvas
        :param master: 上级窗口
        :param classTable: 课程表对象
        :param half: half=0表示上半学期，half=1表示下半学期
        """
        super().__init__(master, bg='#F1F1F1', width=780, height=560)
        self.classTable = classTable
        self.half = half
        self.create_line(0, 0, 780, 0, fill='black')
        self.create_line(0, 40, 780, 40, fill='black')
        self.create_line(0, 0, 0, 40, fill='black')
        self.create_line(80, 0, 80, 560, fill='black')
        self.create_line(50, 40, 50, 560, fill='black')
        for i in range(1, 8):
            self.create_line(80+100*i, 0, 80+100*i, 560, fill='black')
        self.create_line(0, 240, 50, 240, fill='black')
        self.create_line(0, 440, 50, 440, fill='black')
        self.create_line(0, 560, 780, 560, fill='black')
        for i in range(2, 15):
            self.create_line(50, 40*i, 80, 40*i, fill='black')
            self.create_text(65, 40*i-20, text=str(i-1))
        self.create_text(25, 140, text="上午")
        self.create_text(25, 340, text="下午")
        self.create_text(25, 500, text="晚上")
        self.create_text(40, 20, text="时间")
        self.create_text(130, 20, text="周一")
        self.create_text(230, 20, text="周二")
        self.create_text(330, 20, text="周三")
        self.create_text(430, 20, text="周四")
        self.create_text(530, 20, text="周五")
        self.create_text(630, 20, text="周六")
        self.create_text(730, 20, text="周日")
        self.fill()

    def fill(self):
        self.delete("fill")
        for weekday in range(1, 8):
            lastCourseName = ''
            startTime = 0
            lastHasNotSelected = False
            lastHasSelected = False
            # 这里有两种情况，一种是这个课程的志愿里只有选上或者没选上的班，另一种是这个课程的志愿里两者都有
            # 如果是第二种情况，这一个单元格里既要显示蓝色的字，又要显示黑色的字
            for time in range(1, 15):
                if self.half == 0:
                    classTime = ClassTime([(weekday, time)], [])
                else:
                    classTime = ClassTime([], [(weekday, time)])
                courseName = ''

                for class_ in self.classTable.classes:
                    if class_.classTime.isOverlapped(classTime):
                        courseName = class_.course.courseName
                        break

                # 判断双重性
                confirmedClasses = filterClassSetByCondition(
                    lambda x: x.status == ClassStatus.CONFIRMED
                              and x.course.courseName == courseName
                              and x.classTime.isOverlapped(classTime),
                    self.classTable.classes
                )
                unfilteredClasses = filterClassSetByCondition(
                    lambda x: x.course.courseName == courseName
                              and x.status != ClassStatus.CONFIRMED
                              and x.classTime.isOverlapped(classTime),
                    self.classTable.classes
                )

                hasSelected = bool(confirmedClasses)
                hasNotSelected = bool(unfilteredClasses)



                if (lastCourseName != courseName or courseName == ''
                        or hasSelected != lastHasSelected
                        or hasNotSelected != lastHasNotSelected):
                    # 画上上一个课程的名字
                    self.create_line(
                        80 + 100*weekday - 100, 40*startTime, 80 + 100*weekday, 40*startTime,
                        fill='black', tags="fill"
                    )
                    # self.create_text(80 + 100*weekday - 50, (startTime+time)*10, text=lastCourseName)
                    lastDuality = lastHasSelected and lastHasNotSelected
                    if lastCourseName:
                        if not lastDuality:
                            pixelLength = 0
                            font = 12
                            for ch in lastCourseName:
                                if ord(ch) < 128:
                                    pixelLength += font
                                else:
                                    pixelLength += font * 2
                            if pixelLength > 90 * (time - startTime) * 1.414:
                                font = int(90 * (time - startTime) * 1.414 / pixelLength * font)
                            # 课程的志愿里只有选上或者没选上的班一种
                            if lastCourseName is not None and lastHasSelected:
                                fg = "black"
                            else:
                                fg = "blue"
                            self.create_window(80 + 100*weekday - 50, (startTime+time)*20,
                                               window=Label(self.master, text=lastCourseName, fg=fg, bg="#F1F1F1", font=('simHei', font), wraplength=90),
                                               anchor=CENTER, width=90, height=40*(time-startTime)-2,
                                               tags="fill")
                        else:
                            pixelLength = 0
                            font = 12
                            for ch in lastCourseName:
                                if ord(ch) < 128:
                                    pixelLength += font
                                else:
                                    pixelLength += font * 2
                            if pixelLength > 90 * (time - startTime):
                                font = int(90 * (time - startTime) / pixelLength * font * 1.414)
                            self.create_window(80 + 100 * weekday - 50, (startTime * 20 + time * 20) - 10*(time - startTime),
                                               window=Label(self.master, text=lastCourseName, fg="black",
                                                            bg="#F1F1F1",
                                                            font=('simHei', font), wraplength=90),
                                               anchor=CENTER, width=90, height=20 * (time - startTime) - 2,
                                               tags="fill")
                            self.create_window(80 + 100 * weekday - 50, (startTime * 20 + time * 20) + 10*(time - startTime),
                                               window=Label(self.master, text=lastCourseName, fg="blue",
                                                            bg="#F1F1F1",
                                                            font=('simHei', font), wraplength=90),
                                               anchor=CENTER, width=90, height=20 * (time - startTime) - 2,
                                               tags="fill")
                    lastCourseName = courseName
                    lastHasSelected = hasSelected
                    lastHasNotSelected = hasNotSelected
                    startTime = time



class CandidateTable(Canvas):
    def __init__(self, master, classTable: ClassTable):
        """
        展示选课结果中各个课程的候选教学班
        :param master:
        :param classTable:
        """
        super().__init__(master, width=800, height=720, bg='#F1F1F1')
        # 先获取有哪些课程
        courses = []
        for class_ in classTable.classes.copy():
            if class_.course not in courses:
                courses.append(class_.course)
        courses.sort(key=lambda x: x.courseCode)
        x = 10
        y = 10
        for course in courses:
            # 找出这门课选了哪些班
            classes = []
            for class_ in classTable.classes.copy():
                if class_.course == course:
                    classes.append(class_)
            self.create_rectangle(x, y, 800-x, y+80+len(classes)*60+20, fill='white', outline="white")
            self.create_text(x+10, y+20, text=course.courseCode + course.courseName + f'-{course.credit}学分'
                             , font=('simHei', 12), fill="blue", anchor=W)
            self.create_line(x+10, y+40, 800-x-10, y+40, fill='gray')
            self.create_text(x + 30, y + 60, text="志愿", font=('simHei', 12), fill="black", anchor=CENTER)
            self.create_text(x + 100, y + 60, text="选上否", font=('simHei', 12), fill="black", anchor=CENTER)
            self.create_text(x + 220, y + 60, text="教师", font=('simHei', 12), fill="black", anchor=CENTER)
            self.create_text(x + 340, y + 60, text="学期", font=('simHei', 12), fill="black", anchor=CENTER)
            self.create_text(x + 490, y + 60, text="上课时间", font=('simHei', 12), fill="black", anchor=CENTER)
            self.create_text(x + 690,  y + 60, text="上课地点", font=('simHei', 12), fill="black", anchor=CENTER)
            self.create_line(x+10, y+80, 800-x-10, y+80, fill='gray')
            for i in range(len(classes)):
                class_ = classes[i]
                # 志愿序号
                self.create_text(x+30, y+80+i*60+30, text=f"{i+1}", font=('simHei', 20, "italic"), fill="gray", anchor=CENTER)
                # 选上否
                self.create_text(x + 100, y + 80 + i * 60 + 30,
                                 text="已选上" if class_.status==ClassStatus.CONFIRMED else "待筛选",
                                 font=('simHei', 16),
                                 fill="blue" if class_.status==ClassStatus.CONFIRMED else "red",
                                 anchor=CENTER)
                # 教师姓名
                self.create_text(x+220, y+80+i*60+30, text="\n".join(class_.teacherNames), font=('simHei', 10), fill="black", anchor=CENTER)
                # 学期
                self.create_text(x+340, y+80+i*60+30, text=class_.originSemesterStr, font=('simHei', 10), fill="black", anchor=CENTER)
                # 上课时间
                self.create_text(x+490, y+80+i*60+30,
                                 text=class_.originClassTimeStr.replace("<br>", "\n").replace(";", "\n"),
                                 font=('simHei', 10), fill="black", anchor=CENTER)
                # 上课地点
                self.create_text(x+690, y+80+i*60+30,
                                 text=class_.location.replace("<br>", "\n").replace(";", "\n"),
                                 font=('simHei', 10), fill="black", anchor=CENTER)
                self.create_line(x+10, y+80+i*60+60, 800-x-10, y+80+i*60+60, fill='gray')

            y += 80+len(classes)*60+40

        # 通过滑动条滚动，展示所有内容
        self.maxY = y + 80
        self.nowYDelta = 0
        self.bind("<MouseWheel>", self.onMouseWheel)

    def onMouseWheel(self, *args):
        delta = args[0].delta/2
        if self.nowYDelta+delta > 0:
            delta = 0
        if self.nowYDelta+delta < 720-self.maxY:
            delta = 0
        self.nowYDelta += delta
        self.move("all", 0, delta)


class DifferenceTable(Canvas):
    def __init__(self, master):
        """
        展示选课算法对课表产生的差异
        依次展示以下内容：
        1. 成功选上的未选课程
        2. 成功优化的已选课程
        3. 未选上的课程
        4. 未优化的已选课程
        """
        super().__init__(master, width=800, height=720, bg='#F1F1F1')
        successSelected = []
        successOptimized = []
        failedSelected = []
        failedOptimized = []
        for wish in wishList.wishes:
            if wish.status == CourseStatus.NOT_SELECTED:
                if filterClassSetByCondition(lambda x: x.course == wish, classTable.classes):
                    successSelected.append(wish)
                else:
                    failedSelected.append(wish)
            else:
                if filterClassSetByCondition(lambda x: x.course == wish and x.status != ClassStatus.CONFIRMED,
                                             classTable.classes):
                    successOptimized.append(wish)
                else:
                    failedOptimized.append(wish)
        y = 10
        for course in successSelected + successOptimized + failedSelected + failedOptimized:
            self.drawCourse(y, course)
            y += 80
        # 通过滑动条滚动，展示所有内容
        self.maxY = y + 80
        self.nowYDelta = 0
        self.bind("<MouseWheel>", self.onMouseWheel)

    def drawCourse(self, y: int, course: Course):
        """
        画出一门课程的信息
        :param y: 这一课程块的y坐标
        :param course: 课程对象
        """
        x = 10
        self.create_rectangle(x, y, 800 - x, y + 60, fill='white', outline="white")
        self.create_text(x + 10, y + 20, text="课程代码：" + course.courseCode, font=('simHei', 12), fill="blue", anchor=W)
        self.create_text(x + 10, y + 40, text="课程名称：" + course.courseName, font=('simHei', 12), fill="blue", anchor=W)
        if course.status == CourseStatus.NOT_SELECTED:
            if filterClassSetByCondition(lambda x: x.course == course, classTable.classes):
                text = "成功选择"
                color = "green"
            else:
                text = "未能选择"
                color = "red"
        else:
            if filterClassSetByCondition(lambda x: x.course == course and x.status != ClassStatus.CONFIRMED, classTable.classes):
                text = "成功优化"
                color = "green"
            else:
                text = "未优化"
                color = "gray"
        self.create_text(800-x-10, y+30, text=text, font=('simHei', 24), fill=color, anchor=E)

    def onMouseWheel(self, *args):
        delta = args[0].delta/2
        if self.nowYDelta+delta > 0:
            delta = 0
        if self.nowYDelta+delta < 720-self.maxY:
            delta = 0
        self.nowYDelta += delta
        self.move("all", 0, delta)




class ResultWindow(Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("选课结果")
        self.iconbitmap("icon.ico")
        self.showWidget = ScheduleTable(self, classTable, 0)
        self.showWidget.place(x=0, y=40, anchor=NW)
        self.nameLabel = Label(self, text="春学期", font=('simHei', 20))
        self.button1 = Button(self, text="春学期", command=lambda: self.show(0))
        self.button2 = Button(self, text="夏学期", command=lambda: self.show(1))
        self.button3 = Button(self, text="志愿表", command=lambda: self.show(2))
        self.button4 = Button(self, text="细节表", command=lambda: self.show(3))
        self.nameLabel.place(x=780, y=0, height=40, anchor=NE)
        self.button1.place(x=0, y=0, width=80, height=40, anchor=NW)
        self.button2.place(x=85, y=0, width=80, height=40, anchor=NW)
        self.button3.place(x=170, y=0, width=80, height=40, anchor=NW)
        self.button4.place(x=255, y=0, width=80, height=40, anchor=NW)
        self.geometry("780x600")

    def show(self, code: int):
        self.showWidget.destroy()
        if code == 0:
            self.showWidget = ScheduleTable(self, classTable, 0)
            self.nameLabel.config(text="春学期")
            self.geometry("780x600")
            self.nameLabel.place(x=780, y=0, height=40, anchor=NE)
        elif code == 1:
            self.showWidget = ScheduleTable(self, classTable, 1)
            self.nameLabel.config(text="夏学期")
            self.geometry("780x600")
            self.nameLabel.place(x=780, y=0, height=40, anchor=NE)
        elif code == 2:
            self.showWidget = CandidateTable(self, classTable)
            self.nameLabel.config(text="志愿表")
            self.geometry("800x760")
            self.nameLabel.place(x=800, y=0, height=40, anchor=NE)
        elif code == 3:
            self.showWidget = DifferenceTable(self)
            self.nameLabel.config(text="细节表")
            self.geometry("800x760")
            self.nameLabel.place(x=800, y=0, height=40, anchor=NE)
        self.showWidget.place(x=0, y=40, anchor=NW)


class Application(Tk):
    def __init__(self):
        super().__init__()
        self.title("MOTIS")
        self.iconbitmap("icon.ico")
        self.geometry('800x600')

        # 保存用户是否登录的状态
        self.loginStatus = False
        # 保存选课算法的执行状态。True表示正在执行，False表示未执行
        self.selectStatus = False

        scrollX = Scrollbar(self, orient=HORIZONTAL)
        Label(self, text="选课要求描述区(Python代码):", font=('Consolas', 16)).place(x=0, y=10, height=20, anchor=W)
        self.codePad = ScrolledText(self, bg='white', fg='white', font=('Consolas', 12), xscrollcommand=scrollX.set, wrap=NONE)
        scrollX.config(command=self.codePad.xview)

        self.codePad.focus_set()
        idc.color_config(self.codePad)
        self.codePad.focus_set()
        self.codePad.config(bg='#002240', fg='white')
        p = idp.Percolator(self.codePad)
        d = idc.ColorDelegator()
        p.insertfilter(d)
        self.codePad.place(x=0, y=20, width=600, height=560, anchor=NW)
        scrollX.place(x=0, y=580, width=580, height=20, anchor=NW)

        self.accountLabel = Label(self, text="学号:", font=('Consolas', 16))
        self.passwordLabel = Label(self, text="密码:", font=('Consolas', 16))
        # self.accountEntry = Entry(self, show="*")
        # 通常而言，学号不应当隐藏，因为学号是公开的信息，没有隐藏的必要，而且隐藏学号会给用户带来视觉上的困难？
        self.accountEntry = Entry(self)
        self.passwordEntry = Entry(self, show="*")
        self.loginButton = Button(self, text="登录", command=self.login)
        self.loginStatusLabel = Label(self, text="未登录", fg="red")

        self.accountEntry.insert(INSERT, network.username)
        self.passwordEntry.insert(INSERT, network.password)
        self.accountLabel.place(x=600, y=0, height=40, anchor=NW)
        self.accountEntry.place(x=600, y=40, width=200, height=30, anchor=NW)
        self.passwordLabel.place(x=600, y=70, height=40, anchor=NW)
        self.passwordEntry.place(x=600, y=110, width=200, height=30, anchor=NW)
        self.loginButton.place(x=600, y=150, width=200, height=40, anchor=NW)
        self.loginStatusLabel.place(x=600, y=190, width=200, height=40, anchor=NW)

        self.updateButton = Button(self, text="更新课程数据", command=self.updateCourse, state=DISABLED)
        self.selectButton = Button(self, text="开始自动选课", command=self.selectCourse, state=DISABLED)
        self.showButton = Button(self, text="显示选课结果", command=self.showResult, state=DISABLED)
        self.authorButton = Button(self, text="关于", command=self.showAuthor)

        self.updateButton.place(x=600, y=440, width=200, height=40, anchor=NW)
        self.selectButton.place(x=600, y=480, width=200, height=40, anchor=NW)
        self.showButton.place(x=600, y=520, width=200, height=40, anchor=NW)
        self.authorButton.place(x=600, y=560, width=200, height=40, anchor=NW)

        self.progressBar = None
        self.doubleVar = DoubleVar()
        self.stringVar = StringVar()

    def _login(self):
        username = self.accountEntry.get()
        password = self.passwordEntry.get()
        self.loginStatusLabel.config(text="正在登录...", fg="blue")
        self.loginButton.config(state=DISABLED)
        network.username = username
        network.password = password
        try:
            if network.loginZDBK():
                self.loginStatusLabel.config(text="登录成功", fg="green")
                self.loginStatus = True
                self.loginButton.config(state=DISABLED)
                self.updateButton.config(state=NORMAL)
                self.selectButton.config(state=NORMAL)
                self.showButton.config(state=NORMAL)
                if not courseData:
                    showinfo("提示", "检测到课程数据为空，即将自动更新课程数据")
                    self.updateCourse()
            else:
                self.loginStatusLabel.config(text="登录失败", fg="red")
                self.loginStatus = False
                self.loginButton.config(state=NORMAL)
        except Exception as e:
            self.loginStatusLabel.config(text="登录失败", fg="red")
            self.loginStatus = False
            showerror("登录异常", str(e)+'\n'+traceback.format_exc())
            self.loginButton.config(state=NORMAL)

    def login(self):
        thread = threading.Thread(target=self._login)
        thread.daemon = True
        thread.start()

    def _updateCourse(self):
        self.updateButton.config(state=DISABLED)
        self.selectButton.config(state=DISABLED)
        self.updateButton.config(text="正在更新课程数据...")


        try:
            self.enableProgress()
            self.stringVar.set("下载课程档案...")
            network.updateCoursesJson(self.doubleVar)
            self.resetProgress()
            self.stringVar.set("载入课程档案...")
            loadCourseData()
            showinfo("更新成功", "课程数据更新成功")
        except Exception as e:
            showerror("更新失败", str(e)+'\n'+traceback.format_exc())

        self.updateButton.config(state=NORMAL)
        self.selectButton.config(state=NORMAL)
        self.updateButton.config(text="更新课程数据")
        self.disableProgress()

    def updateCourse(self):
        thread = threading.Thread(target=self._updateCourse)
        thread.daemon = True
        thread.start()

    def _selectCourse(self):
        self.updateButton.config(state=DISABLED)
        self.selectButton.config(state=DISABLED)
        self.showButton.config(state=DISABLED)
        self.selectButton.config(text="正在选课...")

        try:
            ok = askokcancel("警告", "请不要执行来源不可信任的代码\n否则您的计算机系统可能遭到攻击\n是否继续？")
            if not ok:
                self.updateButton.config(state=NORMAL)
                self.selectButton.config(state=NORMAL)
                self.selectButton.config(text="开始自动选课")
                self.showButton.config(state=NORMAL)
                self.selectStatus = False
                self.disableProgress()
                return

            self.enableProgress()

            # 危险方法，进行修改
            # exec(self.codePad.get(1.0, END))
            user_code = self.codePad.get(1.0, END).strip()
            safe_globals = {
                "__builtins__": None,  # 禁止使用内置危险函数
                "wishList": wishList,  # 允许访问 wishList 对象
                "classTable": classTable,  # 允许访问 classTable 对象
                # 常量
                "First": First,
                "Second": Second,
                "Third": Third,
                "Fourth": Fourth,
                "Fifth": Fifth,
                "Sixth": Sixth,
                "Seventh": Seventh,
                "Eighth": Eighth,
                "Ninth": Ninth,
                "Tenth": Tenth,
                "Eleventh": Eleventh,
                "Twelfth": Twelfth,
                "Thirteenth": Thirteenth,
                "MorningEight": MorningEight,
                "Morning": Morning,
                "Afternoon": Afternoon,
                "Night": Night,
                "Monday": Monday,
                "Tuesday": Tuesday,
                "Wednesday": Wednesday,
                "Thursday": Thursday,
                "Friday": Friday,
                "Saturday": Saturday,
                "Sunday": Sunday,
                "FirstHalfSemester": FirstHalfSemester,
                "SecondHalfSemester": SecondHalfSemester,
                "课程类别": 课程类别,
                "课程归属": 课程归属,
                "课程标记": 课程标记,
                "认定类别": 认定类别,
                # 类
                "ClassTime": ClassTime,
            }

            safe_locals = {}
            try:
                exec(user_code, safe_globals, safe_locals)
            except Exception as e:
                raise Exception(traceback.format_exc())

            ok = True
            if len(wishList.wishes) > 50:
                ok = askokcancel("提示", "愿望清单内课程数量较多，选课可能消耗大量时间，是否继续？")
            if not ok:
                self.updateButton.config(state=NORMAL)
                self.selectButton.config(state=NORMAL)
                self.selectButton.config(text="开始自动选课")
                self.showButton.config(state=NORMAL)
                self.selectStatus = False
                self.disableProgress()
                return

            self.stringVar.set("下载班级档案...")
            network.updateClassJson(wishList, self.doubleVar)
            self.resetProgress()

            self.stringVar.set("载入班级档案...")
            loadClassData(self.doubleVar)
            initClassTable(classTable)
            self.resetProgress()

            self.stringVar.set("自动选课中...")
            selectClass(classTable, wishList, doubleVar=self.doubleVar)

            time.sleep(0.1)
            showinfo("选课完毕", "选课完毕")
            self.selectButton.config(text="自动选课完毕")

        except Exception as e:
            detail = traceback.format_exc()
            showerror("选课失败", str(e)+'\n'+detail)
            self.updateButton.config(state=NORMAL)
            self.selectButton.config(state=NORMAL)
            self.selectButton.config(text="开始自动选课")
        self.showButton.config(state=NORMAL)
        self.selectStatus = False
        self.disableProgress()


    def selectCourse(self):
        self.selectStatus = True
        thread = threading.Thread(target=self._selectCourse)
        thread.daemon = True
        thread.start()


    def showResult(self):
        self.showButton.config(state=DISABLED)
        ResultWindow(self)
        self.showButton.config(state=NORMAL)

    def showAuthor(self):
        showinfo("关于MOTIS", """作者：xi2p
版本：1.0.2(2025/2/10)
Star me on Github:
https://github.com/xi2p/ZJU-MOTIS
软件交流QQ群：836702761
""")

    def enableProgress(self):
        self.progressBar = ProgressBar(self, self.doubleVar, self.stringVar, width=580)
        self.doubleVar.set(0)
        self.stringVar.set("")
        self.progressBar.place(x=0, y=560)

    def resetProgress(self):
        self.doubleVar.set(0)
        self.stringVar.set("")
        self.progressBar.reset()

    def disableProgress(self):
        self.progressBar.destroy()
        self.progressBar = None

    def destroy(self):
        super().destroy()
        quit(0)




if __name__ == '__main__':
    loadCourseData()
    wishList = WishList()
    classTable = ClassTable()

    window = Application()
    mainloop()
