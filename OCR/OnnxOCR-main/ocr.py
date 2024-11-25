import cv2
import time
from onnxocr.onnx_paddleocr import ONNXPaddleOcr,sav2Img



model = ONNXPaddleOcr(use_angle_cls=True, use_gpu=False)


img = cv2.imread('./onnxocr/test_images/11.jpg')
s = time.time()
result = model.ocr(img)
e = time.time()
print("total time: {:.3f}".format(e - s))
print("result:", result)
for box in result[0]:
    print(box[1])

sav2Img(img, result)