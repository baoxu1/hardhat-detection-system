from ultralytics import YOLO
import matplotlib.pyplot as plt


def main():
    # 初始化模型
    model = YOLO('yolov8n.pt')  # 创建一个新的YOLOv8n模型

    # 开始训练
    model.train(
        data='hardhat_dataset/dataset.yaml',
        epochs=10,
        imgsz=256,
        batch=16,
        workers=8,
        device='0',  # 使用第一个GPU
        patience=5,  # 早停策略
        project='hardhat_results',  # 结果保存目录
        name='exp1',  # 实验名称
        save=True,  # 保存模型
        plots=True,  # 保存训练图
        val=True,  # 启用验证
        split=0.8  # 训练集占比0.8，验证集占比0.2
    )

    print("Training completed! Check the training metrics plot at 'training_metrics.png'")


if __name__ == '__main__':
    main()