import traceback
from tkinter import *
from tkinter.ttk import Button, Entry
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import showinfo, showerror
import idlelib.colorizer as idc
import idlelib.percolator as idp
from Entities.ClassTable import ClassTable
from Entities.Constants import ClassStatus, CourseStatus
from interface import *
import network
import threading
from time import sleep
from data import loadCourseData, loadClassData, initClassTable


def CodeConfirmBox(code: str):
    class _CodeConfirmWindow(Tk):
        def __init__(self):
            super().__init__()
            self.title("请确认要执行的代码")
            self.geometry('800x600')
            self.iconbitmap("icon.ico")
            textPad = ScrolledText(self, bg='white', fg='white', font=('Consolas', 16))
            # textPad.pack(fill=BOTH, expand=1)
            textPad.focus_set()
            idc.color_config(textPad)
            textPad.focus_set()
            textPad.config(bg='#002240', fg='white')
            textPad.insert(INSERT, code)
            p = idp.Percolator(textPad)
            d = idc.ColorDelegator()
            p.insertfilter(d)
            buttonConfirm = Button(self, text="确认", command=self.confirm, font=('Consolas', 16), anchor=CENTER)
            buttonCancel = Button(self, text="取消", command=self.cancel, font=('Consolas', 16), anchor=CENTER)
            textPad.place(x=0, y=0, width=800, height=560, anchor=NW)
            buttonConfirm.place(x=250, y=560, width=80, height=40, anchor=NE)
            buttonCancel.place(x=550, y=560, width=80, height=40, anchor=NW)
            textPad.config(state=DISABLED)

            self.confirmStatus = None

        def confirm(self):
            self.confirmStatus = True
            self.destroy()

        def cancel(self):
            self.confirmStatus = False
            self.destroy()

        def destroy(self):
            if self.confirmStatus is None:
                self.confirmStatus = False
            super().destroy()

    window = _CodeConfirmWindow()
    while True:
        window.update()
        if window.confirmStatus is not None:
            break
    return window.confirmStatus


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
            last_course_name = ''
            start_time = 0
            last_class = None
            for time in range(1, 15):
                if self.half == 0:
                    class_time = ClassTime([(weekday, time)], [])
                else:
                    class_time = ClassTime([], [(weekday, time)])
                course_name = ''
                class_now = None
                for class_ in self.classTable.classes:
                    if class_.classTime.isOverlapped(class_time):
                        course_name = class_.course.courseName
                        class_now = class_
                        break

                if last_course_name != course_name or course_name == '':
                    # 画上上一个课程的名字
                    self.create_line(
                        80 + 100*weekday - 100, 40*start_time, 80 + 100*weekday, 40*start_time,
                        fill='black', tags="fill"
                    )
                    # self.create_text(80 + 100*weekday - 50, (start_time+time)*10, text=last_course_name)
                    if last_course_name:
                        pixel_length = 0
                        font = 12
                        for ch in last_course_name:
                            if ord(ch) < 128:
                                pixel_length += font
                            else:
                                pixel_length += font * 2
                        if pixel_length > 90*(time-start_time)*2:
                            font = int(90*(time-start_time)*2/pixel_length*font)
                        if last_course_name is not None and last_class.course.status == CourseStatus.SELECTED:
                            fg = "black"
                        else:
                            fg = "blue"
                        self.create_window(80 + 100*weekday - 50, (start_time+time)*20,
                                           window=Label(self.master, text=last_course_name, fg=fg, bg="#F1F1F1", font=('simHei', font), wraplength=90),
                                           anchor=CENTER, width=90, height=40*(time-start_time)-2,
                                           tags="fill")
                    last_course_name = course_name
                    last_class = class_now
                    start_time = time


class CandidateTable(Canvas):
    def __init__(self, master, classTable: ClassTable):
        """
        展示选课结果中各个课程的候选教学班
        :param master:
        :param classTable:
        """
        super().__init__(master, width=800, height=800, bg='#F1F1F1')
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
                # self.create_text(x+100, y+80+i*60+30,
                #                  text="已选上" if class_.course.status==1 else "待筛选",
                #                  font=('simHei', 16),
                #                  fill="blue" if class_.course.status==1 else "red",
                #                  anchor=CENTER)
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
        self.max_y = y
        self.now_y_delta = 0
        self.bind("<MouseWheel>", self.onMouseWheel)

    def onMouseWheel(self, *args):
        delta = args[0].delta/2
        if self.now_y_delta+delta > 0:
            delta = 0
        if self.now_y_delta+delta < 800-self.max_y:
            delta = 0
        self.now_y_delta += delta
        self.move("all", 0, delta)


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
            else:
                self.loginStatusLabel.config(text="登录失败", fg="red")
                self.loginStatus = False
                self.loginButton.config(state=NORMAL)
        except Exception as e:
            self.loginStatusLabel.config(text="登录失败", fg="red")
            self.loginStatus = False
            showerror("登录异常", str(e)+'\n'+traceback.format_exc())
            self.loginButton.config(state=NORMAL)
        # todo: 登录成功后，自动填充课程表

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
            network.updateClassJson(wish_list)
            loadClassData()
            initClassTable(class_table)
            selectClass(class_table, wish_list)
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
        root0 = Tk()
        root0.iconbitmap("icon.ico")
        root0.title("课程表")
        Label(root0, text="春学期", font=('simHei', 20)).pack()
        st0 = ScheduleTable(root0, class_table, 0)
        st0.pack()

        root1 = Tk()
        root1.iconbitmap("icon.ico")
        root1.title("课程表")
        Label(root1, text="夏学期", font=('simHei', 20)).pack()
        st1 = ScheduleTable(root1, class_table, 1)
        st1.pack()

        root2 = Tk()
        root2.iconbitmap("icon.ico")
        root2.title("志愿清单")
        ct = CandidateTable(root2, class_table)
        ct.pack()
        self.showButton.config(state=NORMAL)

    def showAuthor(self):
        showinfo("关于MOTIS", """作者：xi2p
版本：1.0.0
""")

    def destroy(self):
        super().destroy()
        quit(0)




if __name__ == '__main__':
    loadCourseData()
    wish_list = WishList()
    class_table = ClassTable()

    window = Application()
    mainloop()
    # from interface import *
    # init()
    # wish_list = WishList()
    # class_table = ClassTable()
    #
    # wish_list.append("MATH1136G").withPriority(10).avoidTeacher("薛儒英")  # 微积分
    # wish_list.append("PHY1001G").withPriority(9)                    # 大学物理
    # wish_list.append("MATH1138F").withPriority(9).withStatus(0)     # 常微分方程
    # wish_list.append("ME1103F").withPriority(9).withStatus(0)       # 机械制图及CAD基础
    # wish_list.append("MARX1002G").withPriority(8)                   # 史纲
    # wish_list.append("ME1002F").withPriority(7)                     # 工程训练
    # wish_list.append("CS1241G").withPriority(7)                     # 人工智能基础
    # wish_list.append("EDU2001G").withPriority(6).withStatus(0)      # 军事理论
    # wish_list.append("PHIL0902G").withPriority(6).withStatus(0)     # 希腊罗马哲学
    # wish_list.append("PPAE1100G").withPriority(5).withStatus(0)     # 体素
    # wish_list.append("PPAE0065G").withPriority(4).withStatus(0)     # 体育
    # wish_list.append("BEFS0402G").withPriority(3).withStatus(0)     # 微电子技术与纳米制造
    # wish_list.append("HIST0200G").withPriority(2).withStatus(0)     # 近代中日关系史
    #
    #
    # selectClass(class_table, wish_list)
    #
    # root = Tk()
    # root.title("课程表")
    # Label(root, text="春学期", font=('simHei', 20)).pack()
    # st0 = ScheduleTable(root, class_table, 0)
    # st0.pack()
    #
    # root1 = Tk()
    # root1.title("课程表")
    # Label(root1, text="夏学期", font=('simHei', 20)).pack()
    # st1 = ScheduleTable(root1, class_table, 1)
    # st1.pack()
    #
    # root2 = Tk()
    # root2.title("志愿清单")
    # ct = CandidateTable(root2, class_table)
    # ct.pack()
    #
    # mainloop()