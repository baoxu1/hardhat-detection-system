import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QComboBox, QGroupBox, QGridLayout,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPalette, QColor
from ultralytics import YOLO
import cv2
import numpy as np


class ObjectDetectionUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        # 加载模型
        self.model = YOLO('exp1/weights/best.pt')
        self.model.to('cuda')

        # 初始化变量
        self.current_image = None
        self.detection_result = None
        self.camera = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
        self.is_camera_on = False

    def initUI(self):
        # 设置主窗口
        self.setWindowTitle('基于YOLOv8的目标检测')
        self.setGeometry(100, 100, 1200, 800)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #E6F3FF;
            }
            QGroupBox {
                border: 2px solid #A0A0A0;
                border-radius: 5px;
                margin-top: 1em;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QPushButton {
                background-color: #D7EBF9;
                border: 1px solid #A0A0A0;
                border-radius: 4px;
                padding: 5px;
                min-width: 80px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #BDE0F7;
            }
            QPushButton:pressed {
                background-color: #A5D3F3;
            }
            QPushButton:disabled {
                background-color: #F0F0F0;
                color: #A0A0A0;
            }
            QComboBox {
                border: 1px solid #A0A0A0;
                border-radius: 3px;
                padding: 1px 18px 1px 3px;
                min-width: 6em;
                min-height: 25px;
            }
            QLabel {
                color: #333333;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #A0A0A0;
                gridline-color: #E0E0E0;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                padding: 5px;
                border: 1px solid #A0A0A0;
                font-weight: bold;
            }
        """)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 创建左侧布局
        left_panel = QVBoxLayout()

        # 图像显示区
        image_group = QGroupBox("图像显示")
        image_layout = QHBoxLayout()

        # 原始图像显示
        self.original_image_label = QLabel('原始图像')
        self.original_image_label.setAlignment(Qt.AlignCenter)
        self.original_image_label.setMinimumSize(400, 400)
        self.original_image_label.setStyleSheet(
            "border: 2px solid #A0A0A0; background-color: white;")

        # 检测结果图像显示
        self.result_image_label = QLabel('检测结果')
        self.result_image_label.setAlignment(Qt.AlignCenter)
        self.result_image_label.setMinimumSize(400, 400)
        self.result_image_label.setStyleSheet(
            "border: 2px solid #A0A0A0; background-color: white;")

        image_layout.addWidget(self.original_image_label)
        image_layout.addWidget(self.result_image_label)
        image_group.setLayout(image_layout)

        # 检测结果表格
        table_group = QGroupBox("检测结果与位置信息")
        table_layout = QVBoxLayout()

        # 创建表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(['序号', '类别', '置信度', '位置', '大小'])
        # 设置表格的列宽自适应
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        table_layout.addWidget(self.result_table)
        table_group.setLayout(table_layout)

        left_panel.addWidget(image_group, 7)
        left_panel.addWidget(table_group, 3)

        # 创建右侧控制面板
        right_panel = QVBoxLayout()

        # 文件导入组
        input_group = QGroupBox("文件导入")
        input_layout = QVBoxLayout()

        self.load_image_btn = QPushButton('选择图片文件')
        self.load_image_btn.clicked.connect(self.loadImage)
        self.load_video_btn = QPushButton('选择视频文件')
        self.load_video_btn.clicked.connect(self.loadVideo)
        self.camera_btn = QPushButton('打开摄像头')
        self.camera_btn.clicked.connect(self.toggleCamera)

        input_layout.addWidget(self.load_image_btn)
        input_layout.addWidget(self.load_video_btn)
        input_layout.addWidget(self.camera_btn)
        input_group.setLayout(input_layout)

        # 检测结果组
        result_group = QGroupBox("检测信息")
        result_layout = QGridLayout()

        result_layout.addWidget(QLabel("目标数目:"), 0, 0)
        self.target_count = QLabel("0")
        result_layout.addWidget(self.target_count, 0, 1)

        result_layout.addWidget(QLabel("选择类别:"), 1, 0)
        self.class_combo = QComboBox()
        self.class_combo.addItem("全部")
        result_layout.addWidget(self.class_combo, 1, 1)

        result_group.setLayout(result_layout)

        # 操作按钮组
        operation_group = QGroupBox("操作")
        operation_layout = QHBoxLayout()

        self.detect_button = QPushButton('开始检测')
        self.detect_button.clicked.connect(self.detectObjects)
        self.detect_button.setEnabled(False)

        self.save_button = QPushButton('保存结果')
        self.save_button.clicked.connect(self.saveResult)
        self.save_button.setEnabled(False)

        operation_layout.addWidget(self.detect_button)
        operation_layout.addWidget(self.save_button)
        operation_group.setLayout(operation_layout)

        # 添加所有组件到右侧面板
        right_panel.addWidget(input_group)
        right_panel.addWidget(result_group)
        right_panel.addWidget(operation_group)
        right_panel.addStretch()

        # 设置左右面板的比例
        main_layout.addLayout(left_panel, 7)
        main_layout.addLayout(right_panel, 3)

    def loadImage(self):
        """加载图片"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp)")

        if file_name:
            self.current_image = cv2.imread(file_name)
            if self.current_image is not None:
                rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
                scaled_pixmap = self.scaleImage(rgb_image,
                                                self.original_image_label.size())
                self.original_image_label.setPixmap(scaled_pixmap)
                self.detect_button.setEnabled(True)
                self.save_button.setEnabled(False)
                self.result_image_label.setText('检测结果')
                self.result_table.setRowCount(0)
                self.stopCamera()

    def loadVideo(self):
        """加载视频文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "", "视频文件 (*.mp4 *.avi *.mov)")

        if file_name:
            # 视频处理功能预留
            pass

    def toggleCamera(self):
        """切换摄像头状态"""
        if not self.is_camera_on:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.is_camera_on = True
                self.camera_btn.setText('关闭摄像头')
                self.timer.start(30)
                self.detect_button.setEnabled(True)
        else:
            self.stopCamera()

    def stopCamera(self):
        """停止摄像头"""
        if self.is_camera_on:
            self.timer.stop()
            self.camera.release()
            self.is_camera_on = False
            self.camera_btn.setText('打开摄像头')
            self.camera = None

    def update_camera(self):
        """更新摄像头画面"""
        if self.camera is not None:
            ret, frame = self.camera.read()
            if ret:
                self.current_image = frame
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                scaled_pixmap = self.scaleImage(rgb_frame,
                                                self.original_image_label.size())
                self.original_image_label.setPixmap(scaled_pixmap)

    def detectObjects(self):
        """执行目标检测"""
        if self.current_image is not None:
            # 使用模型进行检测
            results = self.model(self.current_image, device='cpu')[0]

            # 在图像上绘制检测结果
            result_image = self.current_image.copy()

            # 获取检测结果
            boxes = results.boxes.xyxy.numpy()
            classes = results.boxes.cls.numpy()
            confs = results.boxes.conf.numpy()

            # 更新目标数目
            self.target_count.setText(str(len(boxes)))

            # 清空表格
            self.result_table.setRowCount(0)

            # 获取类别名称
            names = results.names

            # 在图像上绘制检测框和标签
            for i, (box, cls, conf) in enumerate(zip(boxes, classes, confs)):
                x1, y1, x2, y2 = box.astype(int)
                cls_name = names[int(cls)]
                label = f'{cls_name} {conf:.2f}'
                width = x2 - x1
                height = y2 - y1

                # 绘制边界框
                cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # 绘制标签背景和文字
                (label_w, label_h), _ = cv2.getTextSize(label,
                                                        cv2.FONT_HERSHEY_SIMPLEX,
                                                        0.6, 1)
                cv2.rectangle(result_image, (x1, y1 - label_h - 10),
                              (x1 + label_w, y1), (0, 255, 0), -1)
                cv2.putText(result_image, label, (x1, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

                # 添加到表格
                row_position = self.result_table.rowCount()
                self.result_table.insertRow(row_position)

                self.result_table.setItem(row_position, 0,
                                          QTableWidgetItem(str(i + 1)))
                self.result_table.setItem(row_position, 1,
                                          QTableWidgetItem(cls_name))
                self.result_table.setItem(row_position, 2,
                                          QTableWidgetItem(f"{conf:.2f}"))
                self.result_table.setItem(row_position, 3,
                                          QTableWidgetItem(f"({x1},{y1})-({x2},{y2})"))
                self.result_table.setItem(row_position, 4,
                                          QTableWidgetItem(f"{width}×{height}"))

                # 设置单元格居中对齐
                for col in range(5):
                    item = self.result_table.item(row_position, col)
                    item.setTextAlignment(Qt.AlignCenter)

            # 保存检测结果
            self.detection_result = result_image

            # 显示检测结果
            rgb_result = cv2.cvtColor(result_image, cv2.COLOR_BGR2RGB)
            scaled_pixmap = self.scaleImage(rgb_result,
                                            self.result_image_label.size())
            self.result_image_label.setPixmap(scaled_pixmap)

            # 启用保存按钮
            self.save_button.setEnabled(True)

    def saveResult(self):
        """保存检测结果"""
        if self.detection_result is not None:
            file_name, _ = QFileDialog.getSaveFileName(
                self, "保存检测结果", "", "图片文件 (*.jpg *.jpeg *.png *.bmp)")

            if file_name:
                cv2.imwrite(file_name, self.detection_result)
                QMessageBox.information(self, "提示", "检测结果已保存！")

    def scaleImage(self, img_array, target_size):
        """等比例缩放图片"""
        h, w, ch = img_array.shape
        target_w, target_h = target_size.width(), target_size.height()

        # 计算缩放比例
        scale = min(target_w / w, target_h / h)
        new_w, new_h = int(w * scale), int(h * scale)
        # 缩放图片
        scaled_img = cv2.resize(img_array, (new_w, new_h))

        # 转换为QPixmap
        height, width, channel = scaled_img.shape
        bytes_per_line = 3 * width
        q_img = QImage(scaled_img.data, width, height, bytes_per_line,
                       QImage.Format_RGB888)
        return QPixmap.fromImage(q_img)

    def closeEvent(self, event):
        """关闭窗口时的处理"""
        self.stopCamera()
        event.accept()

def main():
    # 创建应用
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle('Fusion')

    # 创建并显示主窗口
    window = ObjectDetectionUI()
    window.show()

    # 运行应用
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()