# 工地安全帽检测系统

基于 YOLOv8 的工地安全帽实时检测系统，用于自动化监测和管理工地人员安全帽佩戴情况。系统支持多种检测方式，并提供完整的数据管理功能。

## 功能特点

- 🎯 多模式检测：支持图片、视频文件和实时摄像头检测
- 📊 数据管理：工地信息和检测记录的完整管理功能
- 📈 统计分析：安全帽佩戴率统计和预警功能
- 🖥️ 友好界面：基于 PyQt5 的直观操作界面
- 💾 数据存储：使用 SQLite 实现高效数据管理

## 系统要求

### 环境要求
- Python 3.7+
- CUDA 11.0+ (推荐，用于GPU加速)
- 摄像头 (用于实时检测)

### 依赖包
```bash
torch>=2.0.0
ultralytics>=8.0.0
opencv-python>=4.5.0
PyQt5>=5.15.0
numpy>=1.21.0
```

## 安装说明

1. 克隆项目
```
git clone https://github.com/baoxu1/hardhat-detection-system.git
cd hardhat-detection-system
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 下载预训练模型
```bash
# 将预训练模型放在 models 目录下
mkdir models
# 下载模型文件到 models 目录
```

## 使用说明

### 启动系统
```bash
python main.py
```

### 基本操作流程

1. 工地管理
   - 点击"添加新工地"添加工地信息
   - 填写工地名称、负责人等信息

2. 检测操作
   - 选择检测模式（图片/视频/摄像头）
   - 选择目标工地
   - 开始检测
   - 保存检测记录

3. 记录查询
   - 设置查询条件（工地名称/时间范围）
   - 点击查询按钮
   - 查看检测记录

4. 数据统计
   - 查看安全帽佩戴率统计
   - 检查预警信息

## 项目结构

```
hardhat-detection-system/
├── main.py              # 主程序入口
├── detector.py          # 检测模型实现
├── database.py          # 数据库操作
├── config.py           # 配置文件
├── models/             # 模型文件目录
├── data/              # 数据存储目录
│   ├── images/        # 检测图片存储
│   └── database.db    # SQLite数据库文件
└── requirements.txt    # 项目依赖
```

## 模型训练

### 训练配置
- 模型：YOLOv8-nano
- 输入尺寸：256×256
- 训练轮次：30 epochs
- 批次大小：16
- 数据增强：Mosaic、RandAugment等

### 训练命令
```bash
python train.py --data dataset.yaml --cfg yolov8n.yaml --epochs 30 --batch-size 16
```

## 常见问题

1. 检测不准确
   - 确保光线充足
   - 避免过度拥挤的场景
   - 保持摄像头稳定

2. 系统运行缓慢
   - 检查GPU是否正常工作
   - 降低视频分辨率
   - 关闭不必要的后台程序

3. 数据库错误
   - 检查数据库文件权限
   - 确保磁盘空间充足
   - 定期备份数据库

## 维护说明

1. 数据库维护
   - 定期备份数据库文件
   - 清理过期的检测记录
   - 优化数据库索引

2. 系统更新
   - 定期更新依赖包
   - 检查模型更新
   - 维护系统日志



## 联系方式

- 作者：[Xu Bao]
- 邮箱：[2528628005@qq.com]
- 项目地址：[https://github.com/xubao123/hardhat-detection-system]

## 致谢

- YOLOv8 开发团队
- PyQt5 社区
- 所有项目贡献者
=======


## 致谢

- YOLOv8 开发团队
- PyQt5 社区
- 所有项目贡献者
