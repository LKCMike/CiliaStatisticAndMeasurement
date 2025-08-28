"""
:Date        : 2025-07-20 16:47:32
:LastEditTime: 2025-08-28 08:39:17
:Description : 
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QApplication,
                            QPushButton, QListWidget, QTextEdit, QLineEdit,
                            QFileSystemModel, QTreeView, QSplitter, QLabel, QComboBox)
from PyQt5.QtCore import QDir
from PyQt5.QtGui import QTextCursor

class MainWindow(QMainWindow):
    """
    主界面定义
    """
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """
        初始化界面元素
        """
        self.setWindowTitle('Cilia Statistic and Measurement')
        self.setGeometry(300, 300, 1000, 600)

        # 主布局 - 水平三栏
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 左侧 - 文件浏览器
        self.left_panel = self.create_file_browser()

        # 中间 - 操作按钮
        self.center_panel = self.create_center_buttons()

        # 右侧 - 上下两部分
        self.right_panel = self.create_right_panel()

        # 使用QSplitter实现可调整的分隔布局
        splitter = QSplitter()
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.center_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([300, 100, 500])

        main_layout.addWidget(splitter)

    def create_file_browser(self):
        """
        创建左侧文件浏览器（带驱动器选择
        """
        panel = QWidget()
        layout = QVBoxLayout()

        # 添加驱动器选择栏
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("Current Partition:"))

        # 创建驱动器下拉框
        self.drive_combo = QComboBox()
        self.populate_drives()  # 填充驱动器列表

        # 刷新按钮
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.populate_drives)

        drive_layout.addWidget(self.drive_combo)
        drive_layout.addWidget(refresh_btn)
        drive_layout.addStretch()

        # 文件系统模型和树视图
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.rootPath())
        self.file_model.setNameFilters(['*.jpg', '*.png', '*.tif'])
        self.file_model.setNameFilterDisables(False)  # 隐藏不匹配的文件(True则显示但禁用)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setSelectionMode(QTreeView.ExtendedSelection)

        # 初始设置第一个驱动器为根目录
        if self.drive_combo.count() > 0:
            self.change_drive(0)

        # 连接信号
        self.drive_combo.currentIndexChanged.connect(self.change_drive)

        # 添加到布局
        layout.addLayout(drive_layout)
        layout.addWidget(self.tree_view)
        panel.setLayout(layout)
        return panel

    def populate_drives(self):
        """
        填充可用驱动器列表
        """
        self.drive_combo.clear()
        drives = QDir.drives()

        for drive in drives:
            self.drive_combo.addItem(drive.absolutePath(), drive.absolutePath())

    def change_drive(self, index):
        """
        切换当前驱动器
        """
        if index >= 0:
            drive_path = self.drive_combo.itemData(index)
            self.tree_view.setRootIndex(self.file_model.index(drive_path))

    def create_center_buttons(self):
        """
        创建中间按钮栏
        """
        panel = QWidget()
        layout = QVBoxLayout()

        # 添加按钮
        self.add_btn = QPushButton("Add >>")
        self.add_btn.setMinimumHeight(40)

        # 移除按钮
        self.remove_btn = QPushButton("<< Remove")
        self.remove_btn.setMinimumHeight(40)

        # 开始按钮
        self.start_btn = QPushButton("Start")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white;")

        # 添加间隔
        layout.addStretch()
        layout.addWidget(self.add_btn)
        layout.addWidget(self.remove_btn)
        layout.addWidget(self.start_btn)
        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def create_right_panel(self):
        """
        创建右侧面板
        """
        panel = QWidget()
        layout = QVBoxLayout()

        # 上部 - 已选文件列表
        self.selected_files_list = QListWidget()
        self.selected_files_list.setSelectionMode(QListWidget.ExtendedSelection)

        # 中部 - 输出目录选择
        output_panel = QWidget()
        output_layout = QHBoxLayout()

        self.output_dir_btn = QPushButton("Output To")
        self.open_dir_btn = QPushButton("Open")  # 新增按钮
        self.open_dir_btn.setToolTip("Open Output Directory")
        self.open_dir_btn.setFixedWidth(60)  # 设置固定宽度
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText("Output Directory")

        output_layout.addWidget(self.output_dir_btn)
        output_layout.addWidget(self.output_dir_input)
        output_layout.addWidget(self.open_dir_btn)  # 添加打开按钮
        output_panel.setLayout(output_layout)

        # 下部 - 日志显示
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # 添加各部分到右侧面板
        layout.addWidget(QLabel("Files to Process:"))
        layout.addWidget(self.selected_files_list)
        layout.addWidget(QLabel("Output Config:"))
        layout.addWidget(output_panel)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log_output)

        panel.setLayout(layout)
        return panel

    def append_log(self, message):
        """
        向日志框追加消息
        """
        self.log_output.append(message)
        self.log_output.moveCursor(QTextCursor.End)
        # 强制立即处理界面事件
        QApplication.processEvents()
