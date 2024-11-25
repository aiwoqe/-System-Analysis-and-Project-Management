from django.urls import path
from .views import (
    ManualTrainingView,
    TrainingRecordListView,
    manual_training_page,
    training_records_page
)

urlpatterns = [
    path('manual_training/', manual_training_page, name='manual_training_page'),
    path('manual_train/', ManualTrainingView.as_view(), name='manual_train_api'),
    path('training_records_page/', training_records_page, name='training_records_page'),
    path('training_records/', TrainingRecordListView.as_view(), name='training_records_api'),
]