"""
:Date        : 2025-07-22 16:49:07
:LastEditTime: 2025-08-27 07:26:48
:Description : 
"""
import sys
from PyQt5.QtWidgets import QApplication
from ui import MainWindow
from action import MainController

def main():
    """
    程序入口
    """
    app = QApplication(sys.argv)
    # 创建视图
    view = MainWindow()
    # 创建工作模块
    # 创建控制器，这个必须强引用避免内存回收导致控件功能失效
    controller = MainController(view) # pylint: disable=unused-variable

    # 显示界面
    view.show()
    # 启动应用
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
