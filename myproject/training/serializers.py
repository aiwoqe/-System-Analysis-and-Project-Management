# training/serializers.py

from rest_framework import serializers
from .models import TrainingRecord

class TrainingRecordSerializer(serializers.ModelSerializer):
    camera_ip = serializers.CharField(source='camera.camera_ip', allow_null=True)

    class Meta:
        model = TrainingRecord
        fields = [
            'id',
            'camera_ip',
            'model_type',
            'image_count',
            'training_start_time',
            'training_end_time',
            'image_path',
            'model_path',
            'is_successful',
        ]