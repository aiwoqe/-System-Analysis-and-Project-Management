import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import logging
import os
from S_Object_Classify.Classify_Infer import s_classify,classify_init
from AI_Detection.AI_Detection_Infer import detection,detection_init
from M_Object_Classify.object_Classify_Infer import yolo,yolo_init

# 设置日志记录
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ObjectLocatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Object Locator with Template Matching")
        self.root.configure(bg="#f0f0f0")  # Set background color

        # 摄像头捕获
        self.cap = None
        self.paused = False
        self.drawing = False
        self.roi_selected = False
        self.roi = (0, 0, 0, 0)
        self.template = None
        self.frame_for_roi = None  # 用于存储暂停时的帧
        self.canvases = []  # 用于存储所有窗口的canvas

        self.save_folder = "AI_Detection/data"  # 默认保存文件夹
        os.makedirs(self.save_folder, exist_ok=True)  # 创建文件夹

        # 创建界面布局
        self.create_main_window()

        # 更新视频帧
        self.update_frame()

    def create_main_window(self):
        # 中间视频显示区域
        self.canvas = tk.Canvas(self.root, width=640, height=480, bg="black")
        self.canvas.grid(row=1, column=1, padx=10, pady=10)
        self.canvases.append(self.canvas)  # 将主窗口的canvas加入列表
        # 顶部按钮区域
        top_frame = ttk.Frame(self.root, padding="5")
        top_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        self.start_button = ttk.Button(top_frame, text="开始相机", command=self.start_camera)
        self.start_button.pack(side=tk.LEFT, padx=10, pady=5)
        self.pause_button = ttk.Button(top_frame, text="暂停相机", command=self.pause_camera)
        self.pause_button.pack(side=tk.LEFT, padx=10, pady=5)

        # 左侧工具区域
        left_frame = ttk.Frame(self.root, padding="10")
        left_frame.grid(row=1, column=0, sticky="ns")
        ttk.Label(left_frame, text="工具列表", font=("Helvetica", 12)).pack(pady=5)
        ttk.Button(left_frame, text="缺陷检测", command=lambda: self.open_new_window("缺陷检测")).pack(pady=5)
        ttk.Button(left_frame, text="单目标分类", command=lambda: self.open_new_window("单目标分类")).pack(pady=5)
        ttk.Button(left_frame, text="多目标分类", command=lambda: self.open_new_window("多目标分类")).pack(pady=5)
        ttk.Button(left_frame, text="OCR", command=lambda: self.open_new_window("OCR")).pack(pady=5)

        # 右侧输出区域
        right_frame = ttk.Frame(self.root, padding="10")
        right_frame.grid(row=1, column=2, sticky="ns")
        ttk.Label(right_frame, text="输出结果....", font=("Helvetica", 12)).pack()

    def start_camera(self):
        try:
            if self.cap is None:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    raise Exception("无法打开摄像头")
            self.paused = False  # 恢复视频流
            self.drawing = False
            logging.info("摄像头已启动")
        except Exception as e:
            logging.error(f"启动摄像头时出错: {e}")

    def pause_camera(self):
        self.paused = True
        logging.info("摄像头已暂停")

    def upload_train(self):
        # 上传训练
        print()

    def save_roi(self):
        if self.roi_selected and self.frame_for_roi is not None:
            roi_image = self.frame_for_roi[self.roi[1]:self.roi[3], self.roi[0]:self.roi[2]]
            filename = os.path.join(self.save_folder, f"roi_{len(os.listdir(self.save_folder)) + 1}.jpg")
            cv2.imwrite(filename, roi_image)
            logging.info(f"ROI已保存到 {filename}")
        else:
            logging.warning("未选择ROI，无法保存")

    def update_frame(self):
        if self.cap is not None and not self.paused:
            try:
                ret, frame = self.cap.read()
                if ret:
                    # 保存当前帧，用于暂停后绘制ROI
                    self.frame_for_roi = frame.copy()

                    # # 如果ROI选择完成，进行模板匹配
                    # if self.roi_selected and self.template is not None:
                    #     result = cv2.matchTemplate(frame, self.template, cv2.TM_CCOEFF_NORMED)
                    #     _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    #     h, w = self.template.shape[:2]
                    #     top_left = max_loc
                    #     bottom_right = (top_left[0] + w, top_left[1] + h)
                    #     cv2.rectangle(frame, top_left, bottom_right, (255, 0, 0), 2)

                    if self.roi_selected and self.frame_for_roi is not None:
                        x1, y1, x2, y2 = self.roi
                        # 绘制ROI框
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        # 更新显示画布
                        self.show_frame_on_canvas(frame)

                    # 如果已经加载了模型，进行推理
                    if hasattr(self, "ort_session"):
                        # 执行视频流推理
                        #____________________________________________
                        # yolo(frame, session, model_inputs, input_width, input_height)
                        self.run_inference_on_video_stream(frame)

                    # 将OpenCV图像转为PIL格式
                    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(cv2image)
                    imgtk = ImageTk.PhotoImage(image=img)

                    # 更新画布
                    for canvas in self.canvases:
                        canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                        canvas.imgtk = imgtk  # 防止图像被垃圾回收
                else:
                    logging.warning("未能读取帧")
            except Exception as e:
                logging.error(f"更新帧时出错: {e}")

        # 每10ms更新一次画布
        self.root.after(10, self.update_frame)

    def run_inference_on_video_stream(self, frame):
        if not (self.roi_selected and self.frame_for_roi is not None):
            logging.warning("请先绘制ROI并暂停相机")
            return

        try:
            # 截取ROI区域
            x1, y1, x2, y2 = self.roi
            roi_image = frame[y1:y2, x1:x2]

            # 调用模型推理接口
            heatmap_matrix, y_score_image = detection(roi_image, self.ort_session, self.input_name, self.input_size)

            # 使用 OpenCV 将热力图矩阵映射到颜色图上
            heatmap_colored = cv2.applyColorMap((heatmap_matrix * 255).astype(np.uint8), cv2.COLORMAP_JET)

            # 将 BGR 图像转换为 RGB（PyQt 使用 RGB 格式）
            heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)

            # 调整热力图大小以匹配ROI尺寸
            heatmap_resized = cv2.resize(heatmap_colored, (roi_image.shape[1], roi_image.shape[0]))

            # 将热力图与原始ROI图像叠加
            alpha = 0.5  # 透明度
            overlay = cv2.addWeighted(roi_image, 1 - alpha, heatmap_resized, alpha, 0)

            # 将叠加后的图像更新到帧中
            frame[y1:y2, x1:x2] = overlay

            # # 绘制ROI框
            # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # 更新显示画布
            self.show_frame_on_canvas(frame)

            # 显示得分
            logging.info(f"推理得分：{y_score_image}")

        except Exception as e:
            logging.error(f"模型推理时出错：{e}")

    def draw_roi(self):
        """在 Tkinter 的 Canvas 上直接绘制 ROI."""
        if self.paused and self.frame_for_roi is not None:  # 只有在暂停并且有帧时才能绘制ROI
            self.drawing = True
            self.roi_selected = False
            logging.info("进入ROI绘制模式")

    def start_drawing(self, event):
        """开始绘制 ROI."""
        if self.paused and self.drawing:  # 确保在暂停时绘制
            self.drawing = True
            self.roi = (event.x, event.y, event.x, event.y)

    def update_drawing(self, event):
        """更新绘制中的 ROI."""
        if self.drawing:
            # 更新 ROI 坐标
            self.roi = (self.roi[0], self.roi[1], event.x, event.y)
            for canvas in self.canvases:
                canvas.delete("roi")  # 清除之前绘制的 ROI
                canvas.create_rectangle(self.roi[0], self.roi[1], self.roi[2], self.roi[3], outline="green", width=2,
                                        tag="roi")

    def finish_drawing(self, event):
        """完成绘制 ROI."""
        if self.drawing:
            # self.drawing = False
            self.roi_selected = True
            logging.info(f"ROI 绘制完成，坐标: {self.roi}")
            # 提取模板
            if self.frame_for_roi is not None:
                x1, y1, x2, y2 = self.roi
                self.template = self.frame_for_roi[y1:y2, x1:x2]
                logging.info("模板已提取")

    def open_new_window(self, title):
        # 隐藏当前窗口
        self.root.withdraw()

        # 创建新窗口
        new_window = tk.Toplevel(self.root)
        new_window.title(title)
        new_window.configure(bg="#f0f0f0")

        # 顶部菜单栏显示功能名称
        top_frame = ttk.Frame(new_window, padding="5")
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        ttk.Button(top_frame, text="开始相机", command=self.start_camera).pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Button(top_frame, text="暂停相机", command=self.pause_camera).pack(side=tk.LEFT, padx=10, pady=5)

        # 左侧功能按钮
        left_frame = ttk.Frame(new_window, padding="10")
        left_frame.grid(row=1, column=0, sticky="ns")

        ttk.Button(left_frame, text="模型推理", command=self.load_model).pack(pady=5)  # 新功能1：加载模型
        ttk.Button(left_frame, text="绘制ROI", command=self.draw_roi).pack(pady=5)
        ttk.Button(left_frame, text="保存图片", command=self.save_roi).pack(pady=5)
        ttk.Button(left_frame, text="上传训练", command=self.upload_train).pack(pady=5)

        # 中间视频显示区域
        canvas = tk.Canvas(new_window, width=640, height=480, bg="black")
        canvas.grid(row=1, column=1, padx=10, pady=10)
        self.canvases.append(canvas)  # 将新窗口的canvas加入列表

        # 设置绘制ROI的鼠标事件
        canvas.bind("<ButtonPress-1>", self.start_drawing)
        canvas.bind("<B1-Motion>", self.update_drawing)
        canvas.bind("<ButtonRelease-1>", self.finish_drawing)

        # 当新窗口关闭时恢复主窗口显示
        def on_new_window_close():
            self.canvases.remove(canvas)  # 从画布列表中移除该窗口的画布
            self.root.deiconify()  # 恢复主窗口显示
            new_window.destroy()  # 销毁新窗口

        new_window.protocol("WM_DELETE_WINDOW", on_new_window_close)

    # 新增功能：加载模型
    def load_model(self):
        model_path = filedialog.askopenfilename(
            title="选择模型文件",
            filetypes=(("ONNX 模型", "*.onnx"), ("所有文件", "*.*")),
        )
        if model_path:
            try:
                # 调用初始化接口加载模型
                self.ort_session, self.input_name, self.input_size = detection_init(model_path)
                logging.info(f"模型已加载成功：{model_path}")
            except Exception as e:
                logging.error(f"加载模型时出错：{e}")


    def show_frame_on_canvas(self, frame):
        # 将 OpenCV 图像转换为 RGB 格式
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        imgtk = ImageTk.PhotoImage(image=img)

        # 在所有 Canvas 上更新显示
        for canvas in self.canvases:
            canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            canvas.imgtk = imgtk  # 防止图像被垃圾回收

    def on_closing(self):
        if self.cap is not None:
            self.cap.release()
            logging.info("摄像头已释放")
        self.root.destroy()
        logging.info("应用已关闭")


# 创建主窗口
root = tk.Tk()
app = ObjectLocatorApp(root)

# 处理窗口关闭事件
root.protocol("WM_DELETE_WINDOW", app.on_closing)

# 启动主循环
root.mainloop()
