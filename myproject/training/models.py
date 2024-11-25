# training/models.py

from django.db import models

class Camera(models.Model):
    camera_ip = models.CharField(max_length=45, unique=True)

    def __str__(self):
        return self.camera_ip

class TrainingRecord(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.SET_NULL, null=True, blank=True)
    training_start_time = models.DateTimeField(auto_now_add=True)
    training_end_time = models.DateTimeField(null=True, blank=True)
    model_type = models.CharField(max_length=255)
    image_count = models.IntegerField()
    image_path = models.TextField()
    model_path = models.TextField()
    is_successful = models.BooleanField()

    def __str__(self):
        return f"TrainingRecord {self.id} - {self.model_type}"
