from datetime import datetime

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
import logging
import os

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

        self.save_folder = "../Algorithm_Platform_System/AI_Detection/data/de/train/good"  # 默认保存文件夹
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
        """
        保存图片，加上按时间分文件夹的操作
        1. 查看当前时间
        2. 检查当前时间的文件夹是否存在，不存在就新建一个文件夹 (在 self.save_folder 下新建一个名称为当前时间：年月日_小时分钟秒)
        3. 保存图片到时间文件夹
        :return:
        """
        if self.roi_selected and self.frame_for_roi is not None:
            # 获取当前时间并格式化为文件夹名
            current_time = datetime.now().strftime("%Y%m%d_%H%M")
            time_folder = os.path.join(self.save_folder, current_time)

            # 如果时间文件夹不存在，则创建
            if not os.path.exists(time_folder):
                os.makedirs(time_folder)

            # 截取ROI并生成文件名
            roi_image = self.frame_for_roi[self.roi[1]:self.roi[3], self.roi[0]:self.roi[2]]
            filename = os.path.join(time_folder, f"roi_{len(os.listdir(time_folder)) + 1}.jpg")

            # 保存图片
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

                    # 如果ROI选择完成，进行模板匹配
                    if self.roi_selected and  self.template is not None:
                        result = cv2.matchTemplate(frame, self.template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, max_loc = cv2.minMaxLoc(result)
                        h, w = self.template.shape[:2]
                        top_left = max_loc
                        bottom_right = (top_left[0] + w, top_left[1] + h)
                        cv2.rectangle(frame, top_left, bottom_right, (255, 0, 0), 2)

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
        ttk.Button(left_frame, text="服务IP", command=self.start_camera).pack(pady=5)
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
