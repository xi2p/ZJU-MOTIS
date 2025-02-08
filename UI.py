import traceback
from tkinter import *
from tkinter.ttk import Button, Entry
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import showinfo, showerror
from lib import colorizer as idc
import idlelib.percolator as idp
from Entities.Constants import ClassStatus, CourseStatus
from interface import *
import network
import threading
from data import loadCourseData, loadClassData, initClassTable, courseData, filterClassSetByCondition


# def CodeConfirmBox(code: str):
#     class _CodeConfirmWindow(Tk):
#         def __init__(self):
#             super().__init__()
#             self.title("请确认要执行的代码")
#             self.geometry('800x600')
#             self.iconbitmap("icon.ico")
#             textPad = ScrolledText(self, bg='white', fg='white', font=('Consolas', 16))
#             # textPad.pack(fill=BOTH, expand=1)
#             textPad.focus_set()
#             idc.color_config(textPad)
#             textPad.focus_set()
#             textPad.config(bg='#002240', fg='white')
#             textPad.insert(INSERT, code)
#             p = idp.Percolator(textPad)
#             d = idc.ColorDelegator()
#             p.insertfilter(d)
#             buttonConfirm = Button(self, text="确认", command=self.confirm, font=('Consolas', 16), anchor=CENTER)
#             buttonCancel = Button(self, text="取消", command=self.cancel, font=('Consolas', 16), anchor=CENTER)
#             textPad.place(x=0, y=0, width=800, height=560, anchor=NW)
#             buttonConfirm.place(x=250, y=560, width=80, height=40, anchor=NE)
#             buttonCancel.place(x=550, y=560, width=80, height=40, anchor=NW)
#             textPad.config(state=DISABLED)
#
#             self.confirmStatus = None
#
#         def confirm(self):
#             self.confirmStatus = True
#             self.destroy()
#
#         def cancel(self):
#             self.confirmStatus = False
#             self.destroy()
#
#         def destroy(self):
#             if self.confirmStatus is None:
#                 self.confirmStatus = False
#             super().destroy()
#
#     window = _CodeConfirmWindow()
#     while True:
#         window.update()
#         if window.confirmStatus is not None:
#             break
#     return window.confirmStatus


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
            lastClass = None
            lastDuality = False
            # 这里有两种情况，一种是这个课程的志愿里只有选上或者没选上的班，另一种是这个课程的志愿里两者都有
            # 如果是第二种情况，这一个单元格里既要显示蓝色的字，又要显示黑色的字
            for time in range(1, 15):
                if self.half == 0:
                    classTime = ClassTime([(weekday, time)], [])
                else:
                    classTime = ClassTime([], [(weekday, time)])
                courseName = ''
                class_now = None

                for class_ in self.classTable.classes:
                    if class_.classTime.isOverlapped(classTime):
                        courseName = class_.course.courseName
                        class_now = class_
                        break

                # 判断双重性
                confirmedClasses = filterClassSetByCondition(
                    lambda x: x.status == ClassStatus.CONFIRMED
                              and x.course.courseName == courseName
                              and x.classTime.isOverlapped(classTime)
                )
                unfilteredClasses = filterClassSetByCondition(
                    lambda x: x.course.courseName == courseName
                              and x.status != ClassStatus.CONFIRMED
                              and x.classTime.isOverlapped(classTime)
                )
                if confirmedClasses and unfilteredClasses:
                    duality = True
                else:
                    duality = False

                if lastCourseName != courseName or courseName == '' or duality != lastDuality:
                    # 画上上一个课程的名字
                    self.create_line(
                        80 + 100*weekday - 100, 40*startTime, 80 + 100*weekday, 40*startTime,
                        fill='black', tags="fill"
                    )
                    # self.create_text(80 + 100*weekday - 50, (startTime+time)*10, text=lastCourseName)
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
                            if lastCourseName is not None and lastClass.status == ClassStatus.CONFIRMED:
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
                    lastClass = class_now
                    lastDuality = duality
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
        self.maxY = y
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
        self.nameLabel.place(x=780, y=0, height=40, anchor=NE)
        self.button1.place(x=0, y=0, width=80, height=40, anchor=NW)
        self.button2.place(x=85, y=0, width=80, height=40, anchor=NW)
        self.button3.place(x=170, y=0, width=80, height=40, anchor=NW)
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

        Label(self, text="选课要求描述区(Python代码):", font=('Consolas', 16)).place(x=0, y=10, height=20, anchor=W)
        self.codePad = ScrolledText(self, bg='white', fg='white', font=('Consolas', 12))
        self.codePad.focus_set()
        idc.color_config(self.codePad)
        self.codePad.focus_set()
        self.codePad.config(bg='#002240', fg='white')
        p = idp.Percolator(self.codePad)
        d = idc.ColorDelegator()
        p.insertfilter(d)
        self.codePad.place(x=0, y=20, width=600, height=580, anchor=NW)

        self.accountLabel = Label(self, text="学号:", font=('Consolas', 16))
        self.passwordLabel = Label(self, text="密码:", font=('Consolas', 16))
        self.accountEntry = Entry(self, show="*")
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
            network.updateCoursesJson()
            loadCourseData()
            showinfo("更新成功", "课程数据更新成功")
        except Exception as e:
            showerror("更新失败", str(e)+'\n'+traceback.format_exc())

        self.updateButton.config(state=NORMAL)
        self.selectButton.config(state=NORMAL)
        self.updateButton.config(text="更新课程数据")

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
            exec(self.codePad.get(1.0, END))
            network.updateClassJson(wishList)
            loadClassData()
            initClassTable(classTable)
            selectClass(classTable, wishList)
            showinfo("选课完毕", "选课完毕")
            self.selectButton.config(text="自动选课完毕")

        except Exception as e:
            showerror("选课失败", str(e)+'\n'+traceback.format_exc())
            self.updateButton.config(state=NORMAL)
            self.selectButton.config(state=NORMAL)
            self.selectButton.config(text="开始自动选课")
        self.showButton.config(state=NORMAL)
        self.selectStatus = False


    def selectCourse(self):
        self.selectStatus = True
        thread = threading.Thread(target=self._selectCourse)
        thread.daemon = True
        thread.start()

        # # root0 = Tk()
        # # root0.title("课程表")
        # # Label(root0, text="春学期", font=('simHei', 20)).pack()
        # # st0 = ScheduleTable(root0, class_table, 0)
        # # st0.pack()
        # #
        # # root1 = Tk()
        # # root1.title("课程表")
        # # Label(root1, text="夏学期", font=('simHei', 20)).pack()
        # # st1 = ScheduleTable(root1, class_table, 1)
        # # st1.pack()
        #
        # while self.selectStatus:
        #     # st0.fill()
        #     # st1.fill()
        #     # st0.update()
        #     # st1.update()
        #     # root0.update()
        #     # root1.update()
        #     self.update()
        #
        # # st0.fill()
        # # st1.fill()
        # # root2 = Tk()
        # # root2.title("志愿清单")
        # # ct = CandidateTable(root2, class_table)
        # # ct.pack()
        # self.showResult()


    def showResult(self):
        self.showButton.config(state=DISABLED)
        ResultWindow(self)
        # root0 = Tk()
        # root0.iconbitmap("icon.ico")
        # root0.title("课程表")
        # Label(root0, text="春学期", font=('simHei', 20)).pack()
        # st0 = ScheduleTable(root0, class_table, 0)
        # st0.pack()
        #
        # root1 = Tk()
        # root1.iconbitmap("icon.ico")
        # root1.title("课程表")
        # Label(root1, text="夏学期", font=('simHei', 20)).pack()
        # st1 = ScheduleTable(root1, class_table, 1)
        # st1.pack()
        #
        # root2 = Tk()
        # root2.iconbitmap("icon.ico")
        # root2.title("志愿清单")
        # ct = CandidateTable(root2, class_table)
        # ct.pack()
        self.showButton.config(state=NORMAL)

    def showAuthor(self):
        showinfo("关于MOTIS", """作者：xi2p
版本：1.0.0
Fork me on Github:
https://github.com/xi2p/ZJU-MOTIS
""")

    def destroy(self):
        super().destroy()
        quit(0)




if __name__ == '__main__':
    loadCourseData()
    wishList = WishList()
    classTable = ClassTable()

    window = Application()
    mainloop()
