from PyQt5.QtGui import *  # QtGui：包含了窗口系统、事件处理、2D图像、基本绘画、字体和文字类
from PyQt5.QtWidgets import * # QtWidgets：包含了一些列创建桌面应用的UI元素
from PyQt5.QtCore import *  # QtCore：包含了核心的非GU的功能。主要和时间、文件与文件夹、各种数据、流、URLs、mime类文件、进程与线程一起使用
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent,QSound
import sys
import random
import time
#雷、flag、时钟图标
IMG_BOMB = QImage("./images/bug.png")
IMG_FLAG = QImage("./images/flag.png")
IMG_CLOCK = QImage("./images/clock-select.png")

#显示雷数量的数字的颜色
NUM_COLORS = {
    1: QColor('#f44336'),
    2: QColor('#9C27B0'),
    3: QColor('#3F51B5'),
    4: QColor('#03A9F4'),
    5: QColor('#00BCD4'),
    6: QColor('#4CAF50'),
    7: QColor('#E91E63'),
    8: QColor('#FF9800'),
    9: QColor('#FF0000'),
}

#游戏状态
STATUS_READY = 0
STATUS_PLAYING = 1
STATUS_FAILED = 2
STATUS_SUCCESS = 3

#游戏正中间的状态图标
STATUS_ICONS = {
    STATUS_READY: "./images/plus.png",
    STATUS_PLAYING: "./images/smiley.png",
    STATUS_FAILED: "./images/cross.png",
    STATUS_SUCCESS: "./images/smiley-lol.png",
}

class Demo(QWidget):
    def __init__(self):
        super(Demo, self).__init__()
        self.sound=QSound("./music/EXPLO.mp3")
    def plays(self):
        self.sound.play()


#该类定义了棋盘上每个格子的属性和方法
class Pos(QWidget):
    #声明带特定数据类型参数的信号函数
    #可以查看Tutorial中的相关介绍(Step 4)
    expandable = pyqtSignal(int, int)
    clicked = pyqtSignal()
    ohno = pyqtSignal(int, int)
    postips=pyqtSignal(int,int)
    # 初始化
    def __init__(self, x, y, *args, **kwargs):
        super(Pos, self).__init__(*args, **kwargs)
        #设置格子的大小
        self.setFixedSize(QSize(20, 20))
        # 保存格子在grip上的位置
        self.x = x
        self.y = y

    def reset(self):
        #是否是游戏开始时自动点击的第一个格子
        self.is_start = False
        #是否是雷
        self.is_mine = False
        # 该格子附近8格的地雷数
        self.adjacent_n = 0
        #是否已经点开
        self.is_revealed = False
        #是否标记为棋子
        self.is_flagged = False
        #是否是触发爆炸的雷
        self.is_boomed = False

        self.update()
    #重写虚函数，该虚函数在每次update()时会被调用
    def paintEvent(self, event):
        #QPainter为PyQt的一个绘图类
        #可以查看Tutorial中的相关介绍(Step 2)
        p = QPainter(self)
        #与抗锯齿等相关
        p.setRenderHint(QPainter.Antialiasing)
        #获得该格子在面板中的位置矩形坐标
        r = event.rect()
        #设置揭开和没揭开两种颜色格式
        if self.is_revealed:
            color = self.palette().color(QPalette.Background) # 调色板QPalette类
            outer, inner = color, color
        else:
            outer, inner = Qt.gray, Qt.lightGray
        #QBrush为PyQt的一个基本图形对象，常用于填充矩形等
        brush = QBrush(inner)
        #填充矩形
        p.fillRect(r, brush)
        #外轮廓
        pen = QPen(outer)
        #设置笔的粗细，绘制外轮廓
        pen.setWidth(2)
        p.setPen(pen)
        #绘制外轮廓
        p.drawRect(r)
        #如果被揭开了
        if self.is_revealed:
            # 如果是开始格子
            if self.is_start:
                ch=Qt.yellow
                peny=QPen(ch)
                peny.setWidth(8)
                p.setPen(peny)
                p.drawRect(r)
                # p.drawRect()

                # p.fillRect(r,QBrush(ch))
                # pass
            #如果是雷
            if self.is_mine:
                #如果是爆炸的雷
                #注意，QPainter有类似图层的概念，注意绘制的先后顺序
                # ch = Qt.red
                # p.fillRect(r, QBrush(ch))
                if self.is_boomed:
                    ch = Qt.red
                    p.fillRect(r, QBrush(ch))
                    # pass
                #绘制图案
                p.drawPixmap(r, QPixmap(IMG_BOMB))
            #如果周围有雷，那么这个格子应该显示雷的数量
            elif self.adjacent_n > 0:
                #根据不同的颜色设置QPen
                pen = QPen(NUM_COLORS[self.adjacent_n])
                p.setPen(pen)
                #设置字体
                f = p.font()
                f.setBold(True)
                p.setFont(f)
                #绘制文本
                p.drawText(r, Qt.AlignHCenter | Qt.AlignVCenter, str(self.adjacent_n))
        #如果被标记为flag
        elif self.is_flagged:
            p.drawPixmap(r, QPixmap(IMG_FLAG))

    def flag(self):
        #标记为雷
        self.is_flagged = True
        self.update()
        #触发信号
        self.clicked.emit()
    def unflag(self):
        self.is_flagged=False
        self.update()
        self.clicked.emit()

    def reveal(self):
        #标记为已揭开
        self.is_revealed = True
        self.update()

    def click(self):
        if not self.is_revealed:
            self.reveal()
            #如果雷的数目为零
            if self.adjacent_n == 0:
                #触发信号
                self.expandable.emit(self.x, self.y)
        self.clicked.emit()

    def showTips(self):
        print('showtips')
        self.update()
        #可以在此处添加代码实现Tips功能

    #重写虚函数，该虚函数在收到鼠标点击释放时被调用
    def mouseReleaseEvent(self, event): #判断点击后的逻辑
        if (event.button() == Qt.RightButton and not self.is_revealed):
            if(self.is_flagged):
                self.unflag()
            else:
                self.flag()
        elif (event.button() == Qt.LeftButton):
            if(self.is_flagged): return
            self.click()
            if self.is_mine:
                self.is_boomed=True
                self.ohno.emit(self.x, self.y)  #信号函数发射信号并传递数据
        elif (event.button()==Qt.MiddleButton):
            print(self.x,self.y)
            if(self.is_revealed and not self.is_mine):
                self.postips.emit(self.x,self.y)
                self.showTips()
        #         print('ok')
        #         x=self.x;y=self.y
                # tt=self.grid.itemAtPosition(y, x).widget()
                # print(tt)
            #     aa=0
            #     for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            #         for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
            #             w = self.grid.itemAtPosition(yi, xi).widget()
            #             if not w.is_flagged:
            #                 aa+=1
            #     print(tt,aa)
            #     if aa==tt:
            #         for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            #             for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
            #                 self.x=x
            #                 self.y=y
            #                 self.click()





class MainWindow(QMainWindow):
    #初始化类
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.demo = Demo()
        #设置扫雷行列大小与雷的数量
        self.b_size = 16
        self.n_mines = 40
        #对UI进行布局
        w = QWidget()
        hb = QHBoxLayout()
        vb = QVBoxLayout()
        #显示雷的个数的Label
        self.mines = QLabel()
        self.mines.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        #显示时钟的Label
        self.clock = QLabel()
        self.clock.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        #设置字体大小
        f = self.mines.font()
        f.setPointSize(24)
        f.setWeight(75)
        self.mines.setFont(f)
        self.clock.setFont(f)
        #创建定时器
        #该定时器每秒调用一次self.update_timer，并更新时间
        self._timer = QTimer()
            #信号与槽机制
            # 可以查看Tutorial中的相关介绍(Step 4)
        self._timer.timeout.connect(self.update_timer)
        self._timer.start(1000)
        #初始化，显示雷的数量和时间
        self.mines.setText("%03d" % self.n_mines)
        self.clock.setText("000")
        #状态按钮（用于新开游戏等）
        self.button = QPushButton()
        self.button.setFixedSize(QSize(32, 32))
        self.button.setIconSize(QSize(32, 32))
        self.button.setIcon(QIcon("./images/smiley.png"))
        self.button.setFlat(True)
            #信号与槽机制
            # 可以查看Tutorial中的相关介绍(Step 4)
        self.button.pressed.connect(self.button_pressed)
        self.many=QLineEdit()
        self.many.setText(str(self.n_mines))
        self.many.setFixedWidth(40)
        #将所有Label按顺序装入hb和vb两个布局中
            #雷的图标
        l = QLabel()
        l.setPixmap(QPixmap.fromImage(IMG_BOMB))
        l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            #按顺序添加雷的图标、炸弹数量、状态按钮、时间的图标
        hb.addWidget(self.many)
        hb.addWidget(l)
        hb.addWidget(self.mines)
        hb.addWidget(self.button)
        hb.addWidget(self.clock)
            #时钟显示
        l = QLabel()
        l.setPixmap(QPixmap.fromImage(IMG_CLOCK))
        l.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            #添加时间显示
        hb.addWidget(l)
        self.qok=QPushButton("确认")
        self.qok.setText("确认")
        self.qok.setFixedWidth(60)
        hb.addWidget(self.qok)
        # grid布局，用于创建扫雷每个格子
        self.grid = QGridLayout()
        # 设置每个格子的Spacing
        self.grid.setSpacing(5)
        #垂直布局
        vb.addLayout(hb)
        vb.addLayout(self.grid)
        w.setLayout(vb)
        self.setCentralWidget(w)
        #初始化棋盘
        self.init_map()
        #更新游戏状态
        self.update_status(STATUS_READY)
        #重制棋盘
        self.reset_map()
        #更新游戏状态
        self.update_status(STATUS_READY)
        self.qok.pressed.connect(lambda :self.reset_mine())
        # self.sound=QSound("./music/EXPLO.wav")

        self.show()


    def reset_mine(self):
        tmp=eval(self.many.text())
        print(tmp)
        self.n_mines=tmp
        self.mines.setText("%03d" % self.n_mines)
        self.update_status(STATUS_READY)
        self.reset_map()
        # self.button_pressed()
    # 添加扫雷棋盘的格子  self.b_size * self.b_size的大小
    def init_map(self):
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                #Pos类
                w = Pos(x, y)
                self.grid.addWidget(w, y, x)
                #槽和Pos类的信号连接到一起
                #例如，当w的clicked被emit时，将会调用self.trigger_start并传递数据
                w.clicked.connect(self.trigger_start)
                w.expandable.connect(self.expand_reveal)
                w.ohno.connect(self.game_over)
                w.postips.connect(self.show_tip)

    def reset_map(self):
        # 清除雷的标记
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                #获得( x, y )位置的Pos类（注意查找位置时候的顺序为( y, x )）
                w = self.grid.itemAtPosition(y, x).widget()
                #重置格子的状态
                w.reset()
        # 添加地雷
        positions = []
        while len(positions) < self.n_mines:
            x, y = random.randint(0, self.b_size - 1), random.randint(0, self.b_size - 1)
            if (x, y) not in positions:
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_mine = True
                positions.append((x, y))

        #获得该格子附件的雷的数量
        def get_adjacency_n(x, y):
            positions = self.get_surrounding(x, y)
            n_mines = sum(1 if w.is_mine else 0 for w in positions)
            return n_mines

        # 添加该格子附件的地雷数
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.adjacent_n = get_adjacency_n(x, y)

        #设置开始的格子
        while True:
            x, y = random.randint(0, self.b_size - 1), random.randint(0, self.b_size - 1)
            #避免最开始的格子是炸弹
            if (x, y) not in positions:
                w = self.grid.itemAtPosition(y, x).widget()
                w.is_start = True

                #揭开附近的格子
                for w in self.get_surrounding(x, y):
                    if not w.is_mine:
                        w.click()
                        if w.is_mine:
                            w.is_boomed = True
                            w.ohno.emit(self.x, self.y)
                break

    # 获得该格子附近格子的Pos对象
    def get_surrounding(self, x, y):
        positions = []
        for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                positions.append(self.grid.itemAtPosition(yi, xi).widget())
        return positions

    # 按下状态按钮后，执行重开
    def button_pressed(self):
        #没输但是重开
        if self.status == STATUS_PLAYING:
            self.update_status(STATUS_FAILED)
            self.reveal_map()
        #输了然后重开
        elif self.status == STATUS_FAILED:
            self.update_status(STATUS_READY)
            self.reset_map()

    # 揭开所有的格子
    def reveal_map(self):
        for x in range(0, self.b_size):
            for y in range(0, self.b_size):
                w = self.grid.itemAtPosition(y, x).widget()
                w.reveal()

    # 揭开格子
    def expand_reveal(self, x, y):
        #(x,y)附近的8格
        for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                w = self.grid.itemAtPosition(yi, xi).widget()
                if not w.is_mine:
                    w.click()

    # Tips翻开安全区域
    def show_tip(self, x, y):
        print('tip')
        tt=self.grid.itemAtPosition(y,x).widget()
        print(tt,tt.adjacent_n)
        aa=0
        for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
            for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                w = self.grid.itemAtPosition(yi, xi).widget()
                if w.is_flagged:
                    aa+=1
        print(aa)
        if aa== tt.adjacent_n:
            for xi in range(max(0, x - 1), min(x + 2, self.b_size)):
                for yi in range(max(0, y - 1), min(y + 2, self.b_size)):
                    w = self.grid.itemAtPosition(yi, xi).widget()
                    if not w.is_flagged and not w.is_revealed:
                        w.click()
                        if w.is_mine:
                            w.is_boomed = True
                            w.ohno.emit(self.x, self.y)
        # pass
        #可在此添加代码实现Tips功能

    # 记录开始时间
    def trigger_start(self, *args):
        #只有游戏开始后的第一次点击执行此函数，用于记录开始时间
        if self.status != STATUS_PLAYING:
            # 第一次点击
            self.update_status(STATUS_PLAYING)
            # 记录开始时间
            self._timer_start_nsecs = int(time.time())

    # 更新游戏状态并更新图标
    def update_status(self, status):
        self.status = status
        self.button.setIcon(QIcon(STATUS_ICONS[self.status]))

    # 计算时间
    def update_timer(self):
        if self.status == STATUS_PLAYING:
            n_secs = int(time.time()) - self._timer_start_nsecs
            self.clock.setText("%03d" % n_secs)

    # 游戏结束
    def game_over(self, x, y):
        #揭开所有的格子

        self.reveal_map()
        print("plays")
        self.demo.plays()
        self.update_status(STATUS_FAILED)



if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    #运行，程序进入循环等待状态
    app.exec_()
