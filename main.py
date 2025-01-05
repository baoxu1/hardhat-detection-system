# main.py
import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QGroupBox, QFormLayout, QLineEdit,
                            QComboBox, QMessageBox, QFileDialog, QApplication,
                            QTableWidget, QTableWidgetItem, QDateEdit, QDialog,
                            QSpinBox, QScrollArea, QHeaderView)
from PyQt5.QtCore import QTimer, QDate, Qt
from PyQt5.QtGui import QImage, QPixmap
import cv2
from database import Database
from detector import HelmetDetector
from config import CAPTURE_DIR, DB_PATH
import warnings
warnings.filterwarnings("ignore")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.detector = HelmetDetector()
        self.video_capture = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.current_frame = None
        # 存储最后一次的检测结果
        self.last_detection_results = None
        self.setupUI()

    def setupUI(self):
        """初始化UI"""
        self.setWindowTitle('工地安全帽检测系统')
        self.setGeometry(100, 100, 1200, 800)

        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        # 左侧面板
        left_panel = QVBoxLayout()

        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("border: 2px solid gray;")
        left_panel.addWidget(self.video_label)

        # 媒体控制按钮
        media_control = QHBoxLayout()

        self.image_btn = QPushButton('打开图片')
        self.image_btn.clicked.connect(self.open_image)

        self.video_btn = QPushButton('打开视频')
        self.video_btn.clicked.connect(self.open_video)

        self.camera_btn = QPushButton('打开摄像头')
        self.camera_btn.clicked.connect(self.toggle_camera)

        self.pause_btn = QPushButton('暂停')
        self.pause_btn.clicked.connect(self.toggle_pause)
        self.pause_btn.setEnabled(False)

        self.capture_btn = QPushButton('保存记录')
        self.capture_btn.clicked.connect(self.save_record)
        self.capture_btn.setEnabled(False)

        media_control.addWidget(self.image_btn)
        media_control.addWidget(self.video_btn)
        media_control.addWidget(self.camera_btn)
        media_control.addWidget(self.pause_btn)
        media_control.addWidget(self.capture_btn)
        left_panel.addLayout(media_control)

        # 工地信息面板
        site_group = QGroupBox('工地信息')
        site_layout = QVBoxLayout()

        # 工地选择/添加切换
        self.site_mode = QComboBox()
        self.site_mode.addItems(['选择已有工地', '添加新工地'])
        self.site_mode.currentTextChanged.connect(self.toggle_site_input)
        site_layout.addWidget(self.site_mode)

        # 选择已有工地
        self.site_select = QComboBox()
        self.update_site_combo()
        site_layout.addWidget(self.site_select)

        # 添加新工地
        self.site_input = QWidget()
        site_form = QFormLayout(self.site_input)
        self.site_name_edit = QLineEdit()
        self.manager_name_edit = QLineEdit()
        self.manager_phone_edit = QLineEdit()
        site_form.addRow('工地名称:', self.site_name_edit)
        site_form.addRow('项目经理:', self.manager_name_edit)
        site_form.addRow('联系电话:', self.manager_phone_edit)

        add_site_btn = QPushButton('添加工地')
        add_site_btn.clicked.connect(self.add_site)
        site_form.addRow(add_site_btn)

        site_layout.addWidget(self.site_input)
        self.site_input.hide()  # 默认隐藏添加新工地界面

        site_group.setLayout(site_layout)
        left_panel.addWidget(site_group)

        layout.addLayout(left_panel)

        # 右侧数据管理面板
        right_panel = QVBoxLayout()

        # 数据查询部分
        query_group = QGroupBox('检测记录管理')
        query_layout = QVBoxLayout()

        # 搜索区域
        search_layout = QHBoxLayout()

        # 工地名称搜索
        self.site_search = QLineEdit()
        self.site_search.setPlaceholderText('输入工地名称进行搜索')
        search_layout.addWidget(QLabel('工地名称:'))
        search_layout.addWidget(self.site_search)

        # 日期选择
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate())
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        search_layout.addWidget(QLabel('起始日期:'))
        search_layout.addWidget(self.start_date)
        search_layout.addWidget(QLabel('结束日期:'))
        search_layout.addWidget(self.end_date)

        # 查询按钮
        search_btn = QPushButton('查询')
        search_btn.clicked.connect(self.query_records)
        search_layout.addWidget(search_btn)

        query_layout.addLayout(search_layout)

        # 记录表格
        self.record_table = QTableWidget()
        self.record_table.setColumnCount(8)
        self.record_table.setHorizontalHeaderLabels([
            '工地名称', '检测时间', '总人数', '戴帽人数',
            '未戴帽人数', '佩戴率', '负责人', '操作'
        ])
        self.record_table.setEditTriggers(QTableWidget.NoEditTriggers)
        query_layout.addWidget(self.record_table)

        query_group.setLayout(query_layout)
        right_panel.addWidget(query_group)

        # 预警信息
        warning_group = QGroupBox('预警信息')
        warning_layout = QVBoxLayout()

        self.warning_text = QLineEdit()
        self.warning_text.setReadOnly(True)
        warning_layout.addWidget(self.warning_text)

        check_warning_btn = QPushButton('检查预警')
        check_warning_btn.clicked.connect(self.check_warnings)
        warning_layout.addWidget(check_warning_btn)

        warning_group.setLayout(warning_layout)
        right_panel.addWidget(warning_group)

        layout.addLayout(right_panel)

        # 添加退出按钮
        exit_btn = QPushButton('退出系统')
        exit_btn.clicked.connect(self.close)
        exit_btn.setStyleSheet("background-color: #ff4d4d; color: white; padding: 5px;")
        right_panel.addWidget(exit_btn)

        # 初始化状态变量
        self.is_paused = False
        self.current_media_type = None

    def toggle_site_input(self, mode):
        """切换工地信息输入模式"""
        if mode == '选择已有工地':
            self.site_select.show()
            self.site_input.hide()
        else:
            self.site_select.hide()
            self.site_input.show()

    def update_site_combo(self):
        """更新工地选择下拉框"""
        self.site_select.clear()
        sites = self.db.get_sites()
        for site in sites:
            self.site_select.addItem(site[1], site[0])  # 显示名称，存储ID

    def add_site(self):
        """添加新工地"""
        site_name = self.site_name_edit.text()
        manager_name = self.manager_name_edit.text()
        manager_phone = self.manager_phone_edit.text()

        if not all([site_name, manager_name, manager_phone]):
            QMessageBox.warning(self, '警告', '请填写完整信息')
            return

        try:
            self.db.add_site(site_name, manager_name, manager_phone)
            self.update_site_combo()

            # 清空输入框
            self.site_name_edit.clear()
            self.manager_name_edit.clear()
            self.manager_phone_edit.clear()

            # 切换回选择模式
            self.site_mode.setCurrentText('选择已有工地')
            QMessageBox.information(self, '提示', '工地信息添加成功')
        except Exception as e:
            QMessageBox.warning(self, '错误', f'添加工地失败: {str(e)}')

    def open_image(self):
        """打开图片文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, '选择图片', '', 'Image Files (*.jpg *.png *.jpeg)'
        )

        if file_name:
            # 关闭之前的视频捕获
            if self.video_capture is not None:
                self.video_capture.release()
                self.video_capture = None
                self.timer.stop()

            self.current_media_type = 'image'
            frame = cv2.imread(file_name)
            if frame is not None:
                # 进行检测并保存结果
                processed_frame, total, with_helmet, without_helmet = self.detector.detect_frame(frame)
                self.current_frame = processed_frame.copy()
                # 更新检测结果
                self.last_detection_results = (total, with_helmet, without_helmet)
                self.display_frame(processed_frame)
                self.capture_btn.setEnabled(True)
                self.pause_btn.setEnabled(False)
            else:
                QMessageBox.warning(self, '警告', '无法加载图片')

    def open_video(self):
        """打开视频文件"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, '选择视频文件', '', 'Video Files (*.mp4 *.avi *.mkv)'
        )

        if file_name:
            if self.video_capture is not None:
                self.video_capture.release()

            self.video_capture = cv2.VideoCapture(file_name)
            if self.video_capture.isOpened():
                self.current_media_type = 'video'
                self.pause_btn.setEnabled(True)
                self.capture_btn.setEnabled(True)
                self.is_paused = False
                self.pause_btn.setText('暂停')
                self.timer.start(30)
            else:
                QMessageBox.warning(self, '警告', '无法打开视频文件')

    def toggle_camera(self):
        """切换摄像头状态"""
        if self.video_capture is None:
            self.video_capture = cv2.VideoCapture(0)
            if self.video_capture.isOpened():
                self.camera_btn.setText('关闭摄像头')
                self.current_media_type = 'camera'
                self.pause_btn.setEnabled(True)
                self.capture_btn.setEnabled(True)
                self.is_paused = False
                self.pause_btn.setText('暂停')
                self.timer.start(30)
            else:
                QMessageBox.warning(self, '警告', '无法打开摄像头')
                self.video_capture = None
        else:
            self.timer.stop()
            self.video_capture.release()
            self.video_capture = None
            self.camera_btn.setText('打开摄像头')
            self.pause_btn.setEnabled(False)
            self.capture_btn.setEnabled(False)
            self.video_label.clear()

    def toggle_pause(self):
        """切换视频播放状态"""
        if self.current_media_type in ['video', 'camera']:
            self.is_paused = not self.is_paused
            self.pause_btn.setText('继续' if self.is_paused else '暂停')

    def update_frame(self):
        """更新视频帧"""
        if self.video_capture is not None and not self.is_paused:
            ret, frame = self.video_capture.read()
            if ret:
                # 存储检测结果
                processed_frame, total, with_helmet, without_helmet = self.detector.detect_frame(frame)
                self.current_frame = processed_frame.copy()
                # 更新检测结果
                self.last_detection_results = (total, with_helmet, without_helmet)
                self.display_frame(processed_frame)
            else:
                self.timer.stop()
                self.video_capture.release()
                self.video_capture = None
                self.pause_btn.setEnabled(False)

    def display_frame(self, frame):
        """显示图像帧"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_image = qt_image.scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.KeepAspectRatio
        )
        self.video_label.setPixmap(QPixmap.fromImage(scaled_image))

    def save_record(self):
        """保存检测记录"""
        if self.site_mode.currentText() == '选择已有工地':
            site_id = self.site_select.currentData()
            if site_id is None:
                QMessageBox.warning(self, '警告', '请先选择工地')
                return
        else:
            QMessageBox.warning(self, '警告', '请先选择工地')
            return

        if self.current_frame is None:
            QMessageBox.warning(self, '警告', '没有可用的检测结果')
            return

        try:
            # 检查是否有有效的检测结果
            if self.last_detection_results is None:
                # 如果没有存储的结果，重新进行一次检测
                processed_frame, total, with_helmet, without_helmet = self.detector.detect_frame(self.current_frame)
                self.last_detection_results = (total, with_helmet, without_helmet)
                self.current_frame = processed_frame.copy()

            total, with_helmet, without_helmet = self.last_detection_results

            # 验证检测结果的有效性
            if total == 0 and with_helmet == 0 and without_helmet == 0:
                QMessageBox.warning(self, '警告', '没有有效的检测结果')
                return

            # 保存图像
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_path = os.path.join(CAPTURE_DIR, f'capture_{timestamp}.jpg')
            cv2.imwrite(image_path, self.current_frame)

            # 保存记录到数据库
            record_id = self.db.add_detection_record(
                site_id, total, with_helmet, without_helmet, image_path
            )

            print(f"Saving detection results - Total: {total}, With: {with_helmet}, Without: {without_helmet}")

            QMessageBox.information(self, '提示',
                                    f'记录保存成功\n'
                                    f'总人数: {total}\n'
                                    f'戴帽人数: {with_helmet}\n'
                                    f'未戴帽人数: {without_helmet}\n'
                                    f'保存ID: {record_id}'
                                    )

            self.query_records()
        except Exception as e:
            print(f"Error in save_record: {str(e)}")
            QMessageBox.warning(self, '错误', f'保存记录失败: {str(e)}')

    def query_records(self):
        """查询检测记录"""
        site_name = self.site_search.text().strip()
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()

        try:
            records = self.db.get_records_with_site_name(site_name, start_date, end_date)

            self.record_table.setRowCount(len(records))
            for i, record in enumerate(records):
                record_id, site_id, detection_time, total_people, with_helmet, without_helmet, \
                    image_path, site_name, manager_name, manager_phone = record

                # 计算佩戴率
                wear_rate = (with_helmet / total_people * 100) if total_people > 0 else 0

                # 添加记录到表格
                self.record_table.setItem(i, 0, QTableWidgetItem(site_name))
                self.record_table.setItem(i, 1, QTableWidgetItem(str(detection_time)))
                self.record_table.setItem(i, 2, QTableWidgetItem(str(total_people)))
                self.record_table.setItem(i, 3, QTableWidgetItem(str(with_helmet)))
                self.record_table.setItem(i, 4, QTableWidgetItem(str(without_helmet)))
                self.record_table.setItem(i, 5, QTableWidgetItem(f"{wear_rate:.1f}%"))
                self.record_table.setItem(i, 6, QTableWidgetItem(f"{manager_name}\n{manager_phone}"))

                # 操作按钮
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(0, 0, 0, 0)

                # 查看按钮
                view_btn = QPushButton('查看')
                view_btn.setStyleSheet("padding: 3px;")
                view_btn.clicked.connect(lambda _, path=image_path: self.view_image(path))

                # 编辑按钮
                edit_btn = QPushButton('编辑')
                edit_btn.setStyleSheet("padding: 3px;")
                edit_btn.clicked.connect(lambda _, r=record: self.edit_record(r))

                # 删除按钮
                delete_btn = QPushButton('删除')
                delete_btn.setStyleSheet("padding: 3px;")
                delete_btn.clicked.connect(lambda _, rid=record_id, row=i: self.delete_record(rid, row))

                btn_layout.addWidget(view_btn)
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                btn_layout.setSpacing(5)

                self.record_table.setCellWidget(i, 7, btn_widget)

            self.record_table.resizeColumnsToContents()
            self.record_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        except Exception as e:
            QMessageBox.warning(self, '错误', f'查询记录失败: {str(e)}')

    def edit_record(self, record):
        """编辑记录对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle('编辑检测记录')
        dialog.setModal(True)

        layout = QVBoxLayout()

        # 表单布局
        form_layout = QFormLayout()

        # 工地选择
        site_combo = QComboBox()
        sites = self.db.get_sites()
        for site in sites:
            site_combo.addItem(site[1], site[0])  # 显示名称，存储ID
        # 设置当前工地
        current_index = site_combo.findData(record[1])
        site_combo.setCurrentIndex(current_index)

        # 数据输入框
        total_edit = QSpinBox()
        total_edit.setRange(0, 1000)
        total_edit.setValue(record[3])

        with_helmet_edit = QSpinBox()
        with_helmet_edit.setRange(0, 1000)
        with_helmet_edit.setValue(record[4])

        without_helmet_edit = QSpinBox()
        without_helmet_edit.setRange(0, 1000)
        without_helmet_edit.setValue(record[5])

        # 添加到表单
        form_layout.addRow('工地:', site_combo)
        form_layout.addRow('总人数:', total_edit)
        form_layout.addRow('戴帽人数:', with_helmet_edit)
        form_layout.addRow('未戴帽人数:', without_helmet_edit)

        layout.addLayout(form_layout)

        # 按钮区域
        btn_layout = QHBoxLayout()
        save_btn = QPushButton('保存')
        cancel_btn = QPushButton('取消')

        save_btn.clicked.connect(lambda: self.save_record_edit(
            dialog,
            record[0],  # record_id
            site_combo.currentData(),
            total_edit.value(),
            with_helmet_edit.value(),
            without_helmet_edit.value()
        ))
        cancel_btn.clicked.connect(dialog.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def save_record_edit(self, dialog, record_id, site_id, total, with_helmet, without_helmet):
        """保存编辑后的记录"""
        try:
            self.db.update_record(record_id, site_id, total, with_helmet, without_helmet)
            QMessageBox.information(self, '成功', '记录更新成功')
            dialog.accept()
            self.query_records()  # 刷新表格
        except Exception as e:
            QMessageBox.warning(self, '错误', f'更新记录失败: {str(e)}')

    def delete_record(self, record_id, row):
        """删除记录"""
        reply = QMessageBox.question(
            self, '确认删除',
            '确定要删除这条记录吗？此操作不可撤销。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # 获取图片路径并删除记录
                image_path = self.db.delete_record(record_id)

                # 如果有对应的图片文件，也删除它
                if image_path and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception as e:
                        print(f"删除图片文件失败: {str(e)}")

                # 从表格中删除该行并刷新记录
                self.record_table.removeRow(row)
                self.query_records()

                QMessageBox.information(self, '成功', '记录已删除')
            except Exception as e:
                QMessageBox.warning(self, '错误', f'删除记录失败: {str(e)}')

    def view_image(self, image_path):
        """查看检测图片"""
        if os.path.exists(image_path):
            image = QImage(image_path)
            if not image.isNull():
                dialog = QDialog(self)
                dialog.setWindowTitle('检测图片')
                dialog.setModal(True)

                layout = QVBoxLayout()

                # 创建图片标签并设置图片
                label = QLabel()
                pixmap = QPixmap.fromImage(image)
                # 缩放图片以适应屏幕
                screen_size = QApplication.primaryScreen().size()
                max_size = min(screen_size.width() * 0.8, screen_size.height() * 0.8)
                scaled_pixmap = pixmap.scaled(
                    max_size, max_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                label.setPixmap(scaled_pixmap)

                # 添加滚动区域
                scroll = QScrollArea()
                scroll.setWidget(label)
                scroll.setWidgetResizable(True)
                layout.addWidget(scroll)

                # 添加关闭按钮
                close_btn = QPushButton('关闭')
                close_btn.clicked.connect(dialog.close)
                layout.addWidget(close_btn)

                dialog.setLayout(layout)
                # 设置对话框大小
                dialog.resize(min(pixmap.width() + 50, int(screen_size.width() * 0.9)),
                              min(pixmap.height() + 100, int(screen_size.height() * 0.9)))
                dialog.exec_()
            else:
                QMessageBox.warning(self, '警告', '无法加载图片')
        else:
            QMessageBox.warning(self, '警告', '图片文件不存在')

    def check_warnings(self):
        """检查安全帽佩戴率预警"""
        try:
            low_compliance_sites = self.db.get_low_compliance_sites(0.8)  # 低于80%预警

            warning_text = ""
            for site in low_compliance_sites:
                site_name, manager_name, manager_phone, total_records, compliance_rate = site
                warning_text += f"警告：工地'{site_name}'的安全帽佩戴率为{compliance_rate * 100:.1f}%\n"
                warning_text += f"项目经理：{manager_name}，联系电话：{manager_phone}\n\n"

            if warning_text:
                self.warning_text.setText(warning_text)
            else:
                self.warning_text.setText("目前所有工地的安全帽佩戴率均在正常水平。")
        except Exception as e:
            self.warning_text.setText(f"检查预警失败: {str(e)}")

    def closeEvent(self, event):
        """程序关闭事件"""
        if self.video_capture is not None:
            self.video_capture.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())