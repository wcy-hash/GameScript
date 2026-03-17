import sys
import os
import configparser
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QSpinBox, QFormLayout,
                             QLineEdit, QMessageBox, QFrame, QTextEdit, QPlainTextEdit)
from PyQt5.QtGui import QPixmap, QFont, QTextCursor, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread

from utils import jieping_save_filename, jietu_with_save, resource_path
import qiang_huan, zhuxian_main


class Stream(QObject):
    # 重定向输出的类
    """将标准输出重定向到信号的类"""
    new_text = pyqtSignal(str)

    def write(self, text):
        self.new_text.emit(str(text))

    def flush(self):
        # 通常可以什么都不做，但必须存在，供系统调用
        # 因为Python在输出后可能会调用flush()
        pass


class ScriptThread(QThread):
    # 定义一个信号，用于任务结束时通知主界面恢复按钮状态
    task_finished = pyqtSignal()

    def __init__(self, mode, params):
        super().__init__()
        self.mode = mode  # 'ring' 或 'elite'
        self.params = params  # 传入的参数字典

    def run(self):
        # 这个方法里的代码会在子线程中执行，不会卡死界面
        if self.mode == 'ring':
            qiang_huan.qianghuan_STOP = False
            qiang_huan.main(
                limit_hours=self.params['hours'],
                region=self.params['region'],
                limit_cishu=self.params['runs']
            )
        elif self.mode == 'elite':
            zhuxian_main.zhuxian_STOP = False
            zhuxian_main.main(
                limit_hours=self.params['hours'],
                region=self.params['region'],
                limit_cishu=self.params['runs'],
                maximum_time_one_round=self.params['mission_time']
            )

        # 任务执行完（或者中途停止跳出循环后）发送信号
        self.task_finished.emit()


class ImageDisplayApp(QWidget):
    def __init__(self):
        super().__init__()
        self.image_path = jieping_save_filename
        self.config_file = resource_path('config.ini')

        # 修改logo
        self.setWindowIcon(QIcon(resource_path('picture/logo.ico')))

        # 初始化界面
        self.initUI()

        # 加载配置
        self.load_config()

        # --- 标准输出重定向 ---
        sys.stdout = Stream()
        sys.stdout.new_text.connect(self.on_stdout_received)
        # 如果不想想捕获报错信息，可以注释下面这行
        sys.stderr = sys.stdout

    def on_stdout_received(self, text):
        """当 stdout 收到内容时，追加到文本框并在末尾"""
        self.log_console.moveCursor(QTextCursor.End)
        self.log_console.insertPlainText(text)
        self.log_console.ensureCursorVisible()

    def initUI(self):
        # 主布局：水平排列 (左中右)
        main_h_layout = QHBoxLayout()

        # ==================== 1. 左侧区域 (参数配置) ====================
        left_widget = QVBoxLayout()
        form_layout = QFormLayout()

        self.spin_runtime = QSpinBox()
        self.spin_runtime.setRange(0, 1000)
        self.spin_runtime.setSuffix(" 小时")
        form_layout.addRow("运行时间:", self.spin_runtime)

        self.spin_max_runs = QSpinBox()
        self.spin_max_runs.setRange(0, 1000000)
        self.spin_max_runs.setSuffix(" 次")
        form_layout.addRow("运行次数:", self.spin_max_runs)

        # 坐标区域
        region_layout = QHBoxLayout()
        self.reg_x = QSpinBox();
        self.reg_x.setRange(0, 9999)
        self.reg_y = QSpinBox();
        self.reg_y.setRange(0, 9999)
        self.reg_w = QSpinBox();
        self.reg_w.setRange(0, 9999)
        self.reg_h = QSpinBox();
        self.reg_h.setRange(0, 9999)
        region_layout.addWidget(self.reg_x);
        region_layout.addWidget(self.reg_y)
        region_layout.addWidget(self.reg_w);
        region_layout.addWidget(self.reg_h)
        form_layout.addRow("坐标(XYWH):", region_layout)

        self.spin_mission_time = QSpinBox()
        self.spin_mission_time.setRange(0, 10000)
        self.spin_mission_time.setSuffix(" 秒")
        form_layout.addRow("任务耗时:", self.spin_mission_time)

        left_widget.addLayout(form_layout)

        # 公告框 (自动填充中间)
        left_widget.addWidget(QLabel("公告信息:"))
        self.text_notice = QTextEdit()
        self.text_notice.setReadOnly(True)
        self.text_notice.setText("【公告】\n"
                                 "1. 启动前确保模拟器/游戏窗口未被遮挡。\n\n"
                                 "2. 所有的输出将实时显示在右侧日志框。\n\n"
                                 "3. 坐标设置建议：点击刷新图片确认截取区域是否正确。\n\n"
                                 "4. 遇到闪退请检查 config.ini 权限。\n\n"
                                 "5. 枪环是有一定概率存在抢到精英的情况，因为游戏页面刷新可能发生在点击的一瞬间。\n\n"
                                 "6. 每次启动尽量保持游戏窗口大小，否则，需要相应更换一下picture和zhuxian_picture文件夹中的图片。\n\n"
                                 "7. 运行时间，一次性最长让脚本的运行时间，时间到了会终止；\n   运行次数，一次性最长让脚本的运行次数，次数到了会终止；\n   坐标（XYWH），针对的识别区域，左上角x，左上角y，宽度w，高度h；\n   任务耗时，只针对精英模式，让单局时间不超过任务耗时。\n\n"
                                 "8. 针对识别到了、鼠标没有点击的情况，请用右键软件，用【管理员权限】运行，如在应用宝、腾讯游戏助手、腾讯管家等软件运行的小游戏。\n\n"
                                 "9. 抢环，针对的是抢环球救援；精英，针对的是消耗体力打精英模式。\n\n"
                                 "10. 相关版本更新，可以持续关注https://github.com/wcy-hash/GameScript。然后，多给我的项目点点star，感谢支持和关注。"
                                 )
        self.text_notice.setStyleSheet("background-color: #FFF9C4; border: 1px solid #FBC02D; border-radius: 4px;")
        left_widget.addWidget(self.text_notice)

        # 按钮样式
        style_base = "QPushButton { border-radius: 4px; color: white; }"
        style_save = style_base + "QPushButton { background-color: #2196F3; } QPushButton:disabled { background-color: #ccc; }"
        style_ring = style_base + "QPushButton { background-color: #4CAF50; font-weight: bold; } QPushButton:disabled { background-color: #ccc; }"
        style_elite = style_base + "QPushButton { background-color: #FF9800; font-weight: bold; } QPushButton:disabled { background-color: #ccc; }"
        style_pause = style_base + "QPushButton { background-color: #f44336; font-weight: bold; } QPushButton:disabled { background-color: #ccc; }"

        self.btn_save = QPushButton('保存参数')
        self.btn_save.setFixedHeight(35)
        self.btn_save.setStyleSheet(style_save)
        self.btn_save.clicked.connect(self.save_config)
        left_widget.addWidget(self.btn_save)

        control_layout = QHBoxLayout()
        self.btn_ring = QPushButton('抢环')
        self.btn_ring.setFixedHeight(45);
        self.btn_ring.setStyleSheet(style_ring)
        self.btn_ring.clicked.connect(self.start_ring)

        self.btn_elite = QPushButton('精英')
        self.btn_elite.setFixedHeight(45);
        self.btn_elite.setStyleSheet(style_elite)
        self.btn_elite.clicked.connect(self.start_elite)

        self.btn_pause = QPushButton('暂停')
        self.btn_pause.setFixedHeight(45);
        self.btn_pause.setStyleSheet(style_pause);
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.pause_script)

        control_layout.addWidget(self.btn_ring);
        control_layout.addWidget(self.btn_elite);
        control_layout.addWidget(self.btn_pause)
        left_widget.addLayout(control_layout)

        # ==================== 2. 中间区域 ====================
        middle_widget = QVBoxLayout()
        self.image_label = QLabel("预览图")
        self.image_label.setFixedSize(450, 600)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("border: 2px solid #555; background-color: #eee;")

        self.btn_load = QPushButton('刷新并加载截图')
        self.btn_load.setFixedHeight(35);
        self.btn_load.setStyleSheet(style_save)
        self.btn_load.clicked.connect(self.load_image)

        middle_widget.addWidget(self.image_label)
        middle_widget.addWidget(self.btn_load)

        # ==================== 3. 右侧区域 (终端日志) ====================
        right_widget = QVBoxLayout()
        right_widget.addWidget(QLabel("脚本运行日志:"))
        self.log_console = QPlainTextEdit()
        self.log_console.setMaximumBlockCount(1000)
        self.log_console.setReadOnly(True)
        # 设置黑底白字，像终端一样
        self.log_console.setStyleSheet("""
            background-color: #1e1e1e; 
            color: #dcdcdc; 
            font-family: 'Consolas', 'Monaco', monospace; 
            font-size: 10pt;
            border-radius: 4px;
        """)
        right_widget.addWidget(self.log_console)

        # 合并所有布局
        main_h_layout.addLayout(left_widget, stretch=2)  # 左侧占 2

        # 分割线 1
        line1 = QFrame();
        line1.setFrameShape(QFrame.VLine);
        line1.setFrameShadow(QFrame.Sunken)
        main_h_layout.addWidget(line1)

        main_h_layout.addLayout(middle_widget, stretch=0)  # 图片固定，不拉伸

        # 分割线 2
        line2 = QFrame();
        line2.setFrameShape(QFrame.VLine);
        line2.setFrameShadow(QFrame.Sunken)
        main_h_layout.addWidget(line2)

        main_h_layout.addLayout(right_widget, stretch=3)  # 日志占 3

        self.setLayout(main_h_layout)
        self.setWindowTitle('向僵尸开炮自动化脚本')
        self.resize(1400, 750)  # 调宽总窗口以容纳终端

    # --- 功能函数 ---
    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            try:
                config.read(self.config_file, encoding='utf-8')
                self.spin_runtime.setValue(config.getint('Settings', 'runtime', fallback=10))
                self.spin_max_runs.setValue(config.getint('Settings', 'max_runs', fallback=1000))
                self.spin_mission_time.setValue(config.getint('Settings', 'mission_time', fallback=300))
                self.reg_x.setValue(config.getint('Region', 'x', fallback=0))
                self.reg_y.setValue(config.getint('Region', 'y', fallback=0))
                self.reg_w.setValue(config.getint('Region', 'w', fallback=600))
                self.reg_h.setValue(config.getint('Region', 'h', fallback=1040))
            except:
                pass

    def save_config(self):
        config = configparser.ConfigParser()
        config['Settings'] = {'runtime': str(self.spin_runtime.value()), 'max_runs': str(self.spin_max_runs.value()),
                              'mission_time': str(self.spin_mission_time.value())}
        config['Region'] = {'x': str(self.reg_x.value()), 'y': str(self.reg_y.value()), 'w': str(self.reg_w.value()),
                            'h': str(self.reg_h.value())}
        with open(self.config_file, 'w', encoding='utf-8') as f:
            config.write(f)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 参数已保存到本地。")

    def set_running_state(self, is_running):
        self.btn_ring.setEnabled(not is_running)
        self.btn_elite.setEnabled(not is_running)
        self.btn_pause.setEnabled(is_running)
        self.btn_save.setEnabled(not is_running)
        self.btn_load.setEnabled(not is_running)

    def start_ring(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 任务启动：开始抢环...")
        self.set_running_state(True)

        params = {
            'hours': self.spin_runtime.value(),
            'region': (self.reg_x.value(), self.reg_y.value(), self.reg_w.value(), self.reg_h.value()),
            'runs': self.spin_max_runs.value()
        }

        self.script_thread = ScriptThread('ring', params)
        self.script_thread.task_finished.connect(self.on_script_done)  # 绑定结束回调
        self.script_thread.start()  # 启动线程

    def start_elite(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 任务启动：开始精英任务...")
        self.set_running_state(True)
        params = {
            'hours': self.spin_runtime.value(),
            'region': (self.reg_x.value(), self.reg_y.value(), self.reg_w.value(), self.reg_h.value()),
            'runs': self.spin_max_runs.value(),
            'mission_time': self.spin_mission_time.value()
        }
        self.script_thread = ScriptThread('elite', params)
        self.script_thread.task_finished.connect(self.on_script_done)
        self.script_thread.start()

    def on_script_done(self):
        """当脚本线程结束时调用"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 脚本已停止运行。")
        self.set_running_state(False)

    def pause_script(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 任务指令：下发暂停请求...")
        # 修改全局变量，子线程里的循环检测到该变量变化后会退出
        qiang_huan.qianghuan_STOP = True
        zhuxian_main.zhuxian_STOP = True
        # 注意：这里点击后，界面不会立刻变回“未运行”状态
        # 而是要等子线程里的循环真正结束后，触发 on_script_done 才会变

    def load_image(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在执行区域截图...")
        try:
            jietu_with_save(self.image_path,
                            region=(self.reg_x.value(), self.reg_y.value(), self.reg_w.value(), self.reg_h.value()))
            if os.path.exists(self.image_path):
                pixmap = QPixmap(self.image_path)
                scaled = pixmap.scaled(self.image_label.width() - 10, self.image_label.height() - 10,
                                       Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_label.setPixmap(scaled)
                print("截图加载成功。")
            else:
                print("截图文件未生成，请检查权限。")
        except Exception as e:
            print(f"截图出错: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    ex = ImageDisplayApp()
    ex.show()
    sys.exit(app.exec_())
