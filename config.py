# config.py
import os

# 使用SQLite数据库
DB_PATH = 'helmet_detection.db'

# 使用训练好的自定义模型
YOLO_MODEL = 'exp12/weights/best.pt'

# 图片保存路径
CAPTURE_DIR = 'captured_images'
if not os.path.exists(CAPTURE_DIR):
    os.makedirs(CAPTURE_DIR)