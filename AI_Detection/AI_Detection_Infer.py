import os
import numpy as np
import onnxruntime as ort
from torchvision import transforms
import torch
import cv2
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

# 默认转换
default_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def detection_init(model_path):
    """
    模型初始化
    :param model_path: ONNX 模型路径
    :return: ONNX Runtime 会话、输入张量名称和输入尺寸
    """
    # 创建 ONNX Runtime 会话
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    ort_session = ort.InferenceSession(model_path, providers=providers)
    input_name = ort_session.get_inputs()[0].name
    input_shape = ort_session.get_inputs()[0].shape
    input_size = input_shape[2]  # 假设输入是 HxWxC 格式
    return ort_session, input_name, input_size

def detection(image, ort_session, input_name, input_size):
    """
    单张图片推理接口
    :param image_path: 输入图像文件路径
    :param ort_session: ONNX Runtime 会话
    :param input_name: 输入名称
    :param input_size: 输入尺寸
    :return: 热力图矩阵和最大得分
    """
    # 前处理

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    orig_height, orig_width, _ = image.shape

    # 调整图像大小以匹配模型的输入尺寸
    image = cv2.resize(image, (input_size, input_size))
    image = default_transform(image)
    image = image[None]
    img_numpy = image.cpu().numpy()

    # 推理
    with torch.no_grad():
        map_combined = ort_session.run(None, {input_name: img_numpy})[0]

    # 后处理
    map_combined = torch.tensor(map_combined).clone().detach()
    map_combined = torch.nn.functional.interpolate(map_combined, (orig_height, orig_width), mode='bilinear')
    heatmap_matrix = map_combined[0, 0].cpu().numpy()

    # 获取前5%的得分
    top_5_percent_value = np.percentile(heatmap_matrix, 95)  # 计算前5%的阈值
    y_score_image = top_5_percent_value  # 取前5%的得分

    return heatmap_matrix, y_score_image * 255

# 将热力图矩阵转换为 QImage
def matrix_to_qimage(heatmap_matrix):
    """
    将热力图矩阵转换为 QImage
    :param heatmap_matrix: 热力图矩阵（二维 NumPy 数组）
    :return: QImage 对象
    """
    # 使用 OpenCV 将热力图矩阵映射到颜色图上
    heatmap_colored = cv2.applyColorMap((heatmap_matrix * 255).astype(np.uint8), cv2.COLORMAP_JET)

    # 将 BGR 图像转换为 RGB（PyQt 使用 RGB 格式）
    heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

    # 将 NumPy 数组转换为 QImage
    height, width, channel = heatmap_colored.shape
    bytes_per_line = 3 * width
    q_image = QImage(heatmap_colored.data, width, height, bytes_per_line, QImage.Format_RGB888)

    return q_image

# 创建 PyQt 主窗口
class MainWindow(QMainWindow):
    def __init__(self, heatmap_matrix):
        super().__init__()

        self.setWindowTitle("热力图显示")
        self.setGeometry(100, 100, 800, 600)

        # 创建一个 QLabel 来显示热力图
        self.label = QLabel(self)

        # 转换热力图矩阵为 QImage
        q_image = matrix_to_qimage(heatmap_matrix)

        # 设置 QLabel 显示的图片
        self.label.setPixmap(QPixmap.fromImage(q_image))

        # 布局设置
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

if __name__ == '__main__':
    # 获取热力图矩阵和最大得分
    # 初始化模型
    ort_session, input_name, input_size = detection_init(model_path='./ea.onnx')
    image_path = './1.jpg'
    image = cv2.imread(image_path)
    heatmap_matrix, y_score_image = detection(image, ort_session, input_name, input_size)

    # 运行 PyQt 应用
    app = QApplication([])
    window = MainWindow(heatmap_matrix)
    window.show()
    app.exec_()
