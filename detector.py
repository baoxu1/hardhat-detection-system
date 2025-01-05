# detector.py
from ultralytics import YOLO
import cv2
import numpy as np
from config import YOLO_MODEL

class HelmetDetector:
    def __init__(self):
        self.model = YOLO(YOLO_MODEL)
    def detect_frame(self, frame):
        if frame is None or frame.size == 0:
            print("Warning: Invalid input frame")
            return frame, 0, 0, 0
        # 保持原始图像尺寸较大，提高检测质量
        original_size = frame.shape[:2]
        min_size = 640  # 设置最小尺寸为640x640
        # 如果图像太小，进行放大
        if original_size[0] < min_size or original_size[1] < min_size:
            scale = min_size / min(original_size)
            new_size = (int(original_size[1] * scale), int(original_size[0] * scale))
            frame = cv2.resize(frame, new_size)
            print(f"Resized image from {original_size} to {new_size}")

        # 运行检测，使用conf参数降低置信度阈值
        results = self.model(frame, conf=0.25)[0]

        total_people = 0
        with_helmet = 0
        without_helmet = 0
        valid_detections = []

        # 收集所有有效的检测结果
        for r in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = r
            # 降低置信度阈值以捕获更多可能的目标
            if score > 0.25:  # 降低置信度阈值
                valid_detections.append((x1, y1, x2, y2, score, int(class_id)))
                if int(class_id) == 0:  # Hardhat
                    with_helmet += 1
                else:  # NO-Hardhat
                    without_helmet += 1

        total_people = with_helmet + without_helmet

        # 打印详细的检测信息
        print(f"Valid detections count: {len(valid_detections)}")
        print(f"Detection scores: {[f'{score:.2f}' for *_, score, _ in valid_detections]}")

        # 在图像上绘制检测结果
        for x1, y1, x2, y2, score, class_id in valid_detections:
            if class_id == 0:  # Hardhat
                color = (0, 255, 0)  # 绿色
                label = "Hardhat"
            else:  # NO-Hardhat
                color = (0, 0, 255)  # 红色
                label = "NO-Hardhat"

            # 绘制边界框
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(frame, f'{label} {score:.2f}',
                        (int(x1), int(y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, color, 2)

        # 添加统计信息到图像
        cv2.putText(frame, f'Total: {total_people}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f'With Helmet: {with_helmet}', (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f'Without Helmet: {without_helmet}', (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        print(
            f"Final detection results - Total: {total_people}, With Helmet: {with_helmet}, Without Helmet: {without_helmet}")
        return frame, total_people, with_helmet, without_helmet