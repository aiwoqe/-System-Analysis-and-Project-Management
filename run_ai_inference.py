from S_Object_Classify.Classify_Infer import s_classify,classify_init
from AI_Detection.AI_Detection_Infer import detection,detection_init
from M_Object_Classify.object_Classify_Infer import yolo,yolo_init
import cv2
import time


# image_path = './S_Object_Classify/data/flower/test/daisy/008.jpg'
# model_path = './S_Object_Classify/EfficientNet_Lite0.onnx'
# class_indict = {'0': 'daisy', '1': 'dandelion', '2': 'roses', '3': 'sunflowers', '4': 'tulips'}
# # 初始化检测模型，一次初始化，多次运行
# ort_session, input_name, input_size = classify_init(model_path)
# # Run inference for the single image
# result = s_classify(image_path, class_indict, ort_session, input_name, input_size)
# print(result)  # {'class': 'daisy', 'score': 0.9999355}

# #heatmap_matrix是一个矩阵，y_score_image是得分
# image_path = './AI_Detection/data/roi_1.jpg'
# image = cv2.imread(image_path)
# if image is None:
#     raise ValueError(f"无法读取图片：{image_path}")
# model_path = './AI_Detection/de_10_ef.onnx'
# # 初始化检测模型，一次初始化，多次运行
# ort_session, input_name, input_size = detection_init = detection_init(model_path)
# time1 = time.time()
# heatmap_matrix, y_score_image = detection(image_path, ort_session, input_name, input_size)
# time2 = time.time()
# print(time2-time1)
# heatmap_matrix, y_score_image = detection(image_path, ort_session, input_name, input_size)
# heatmap_matrix, y_score_image = detection(image_path, ort_session, input_name, input_size)
# heatmap_matrix, y_score_image = detection(image_path, ort_session, input_name, input_size)
# time3 = time.time()
# print(time3-time2)



image_path = './M_Object_Classify/data/img.png'
model_path = './M_Object_Classify/yolov8n.onnx'
# 初始化检测模型，一次初始化，多次运行
session, model_inputs, input_width, input_height = yolo_init(model_path)
# 读取图像文件
image_data = cv2.imread(image_path)
# 使用检测模型对读入的图像进行对象检测，多次运行
result_image, class_dic = yolo(image_data, session, model_inputs, input_width, input_height)
print(class_dic)

