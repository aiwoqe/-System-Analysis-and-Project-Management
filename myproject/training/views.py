# training/views.py

from django.shortcuts import render
from django.utils import timezone  # 导入 timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
import threading
import time
import os

from .models import TrainingRecord
from .serializers import TrainingRecordSerializer
# training/views.py


class ManualTrainingView(APIView):
    def post(self, request):
        model_type = request.data.get('model_type')
        dataset_path = request.data.get('dataset_path')

        if not model_type or not dataset_path:
            return Response({'message': '模型类型和数据集路径不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        if not os.path.exists(dataset_path):
            return Response({'message': '数据集路径不存在'}, status=status.HTTP_400_BAD_REQUEST)
        if not os.path.isdir(dataset_path):
            return Response({'message': '数据集路径不是目录'}, status=status.HTTP_400_BAD_REQUEST)

        # 启动后台线程进行训练
        training_thread = threading.Thread(target=self.run_training, args=(model_type, dataset_path))
        training_thread.start()

        return Response({'message': '训练已开始'}, status=status.HTTP_200_OK)

    def run_training(self, model_type, dataset_path):
        # 记录训练开始时间
        training_record = TrainingRecord(
            camera=None,  # 手动训练，无特定相机
            model_type=model_type,
            image_count=self.count_images_in_dataset(dataset_path),
            image_path=dataset_path,
            is_successful=False  # 训练完成后再更新
        )
        training_record.save()

        try:
            # 调用实际的训练逻辑
            model_path = self.train_model(model_type, dataset_path)

            # 更新训练记录
            training_record.training_end_time = timezone.now()
            training_record.model_path = model_path
            training_record.is_successful = True
            training_record.save()
        except Exception as e:
            print(f"训练过程中发生错误: {e}")
            training_record.training_end_time = timezone.now()
            training_record.is_successful = False
            training_record.save()

    def count_images_in_dataset(self, dataset_path):
        # 统计数据集中图片的数量
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        count = 0
        for root, dirs, files in os.walk(dataset_path):
            count += len([f for f in files if f.lower().endswith(image_extensions)])
        return count

    def train_model(self, model_type, dataset_path):
        # 在这里调用您的模型训练逻辑
        # 返回模型保存的路径
        # 例如：
        time.sleep(5)  # 模拟训练时间
        model_path = f'/models/{model_type}_model_{int(time.time())}.h5'
        # 假设模型已经保存到指定路径
        return model_path

class TrainingRecordListView(ListAPIView):
    queryset = TrainingRecord.objects.all().order_by('-training_start_time')
    serializer_class = TrainingRecordSerializer

def manual_training_page(request):
    return render(request, 'training/manual_training.html')

def training_records_page(request):
    return render(request, 'training/training_records.html')