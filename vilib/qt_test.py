import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
from picamera import PiCamera
from picamera.array import PiRGBArray

class CameraViewer(QWidget):
    def __init__(self):
        super().__init__()

        # 创建摄像头对象
        self.camera = PiCamera()
        self.camera.resolution = (640, 480)

        # 创建用于捕获图像的缓冲区
        self.raw_capture = PiRGBArray(self.camera)

        # 创建标签对象
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        # 创建定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)  # 每30毫秒更新一次画面

    def update_frame(self):
        # 捕获摄像头图像
        self.camera.capture(self.raw_capture, format='rgb')
        image = self.raw_capture.array

        # 转换图像格式
        height, width, channel = image.shape
        bytes_per_line = channel * width
        q_image = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)

        # 创建缩放后的图像
        scaled_image = q_image.scaled(640, 480, Qt.KeepAspectRatio)

        # 在标签中显示图像
        self.label.setPixmap(QPixmap.fromImage(scaled_image))

        # 清空缓冲区
        self.raw_capture.truncate(0)

if __name__ == '__main__':
    # 创建应用程序对象
    # app = QApplication(sys.argv)
    app = QApplication([])


    # 创建窗口对象
    window = CameraViewer()
    window.setWindowTitle('Camera Viewer')
    window.resize(640, 480)

    # 将标签添加到窗口中心
    window.label.setGeometry(0, 0, window.width(), window.height())

    # 显示窗口
    window.show()

    # 运行应用程序
    # sys.exit(app.exec_())
    app.exec_()


'''
import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtGui import QPixmap

if __name__ == '__main__':
    # 创建应用程序对象
    app = QApplication(sys.argv)

    # 创建窗口对象
    window = QWidget()
    window.setWindowTitle('Image Viewer')
    window.resize(800, 600)

    # 创建标签对象
    label = QLabel(window)

    # 加载图像文件
    image = QPixmap('path/to/your/image.jpg')

    # 设置图像为标签的内容
    label.setPixmap(image)
    label.adjustSize()

    # 将标签添加到窗口中心
    label.move((window.width() - label.width()) / 2, (window.height() - label.height()) / 2)

    # 显示窗口
    window.show()

    # 运行应用程序
    sys.exit(app.exec_())

'''