import os
import numpy as np
from PIL import Image
import onnxruntime as ort
import albumentations as A
from albumentations.pytorch import ToTensorV2


def preprocess_image(img_path, input_size):
    """
    Preprocess the input image for inference.
    Args:
        img_path: Path to the input image.
        input_size: The size to which the image will be resized.
    Returns:
        Preprocessed image as a numpy array.
    """
    data_transform = A.Compose([
        A.SmallestMaxSize(max_size=input_size + 32),
        A.CenterCrop(height=input_size, width=input_size),
        A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2()
    ])

    assert os.path.exists(img_path), f"file: '{img_path}' does not exist."
    img = Image.open(img_path).convert("RGB")
    img = data_transform(image=np.array(img))['image']
    img = np.expand_dims(img, axis=0)  # Add batch dimension
    return img


def classify_init(model_path):
    """
    Initialize the ONNX model for detection, loading it into memory once.
    Args:
        model_path: Path to the ONNX model file.
    Returns:
        ort_session, input_name, input_size
    """
    # Load the ONNX model
    ort_session = ort.InferenceSession(model_path)
    input_name = ort_session.get_inputs()[0].name
    input_size = ort_session.get_inputs()[0].shape[2]  # Assuming square input
    return ort_session, input_name, input_size


def s_classify(image_path, class_indict, ort_session, input_name, input_size):
    """
    Perform inference on an image using the initialized ONNX model.
    Args:
        image_path: Path to the input image.
        ort_session: Initialized ONNX model session.
        input_name: Name of the input tensor for the model.
        input_size: The input size of the model (default is 224).
    Returns:
        Tuple of (predicted class index, predicted probabilities for all classes).
    """

    # Preprocess the image
    img = preprocess_image(image_path, input_size)
    img_tensor = img.astype(np.float32)  # Ensure input is float32

    # Run inference
    outputs = ort_session.run(None, {input_name: img_tensor})
    predict = outputs[0][0]  # Extract predictions from batch
    predict = np.exp(predict) / np.sum(np.exp(predict))  # Apply softmax for probabilities

    # Get the predicted class index and probability
    max_class_index = np.argmax(predict)
    max_class_prob = predict[max_class_index]
    predicted_class = class_indict[str(max_class_index)]

    # Prepare the output
    result = {
        "class": predicted_class,
        "score": max_class_prob,
    }
    return result


if __name__ == '__main__':
    # Model path and image path
    image_path = './data/flower/test/daisy/008.jpg'  # Replace with your image path
    onnx_model_path = 'EfficientNet_Lite0.onnx'  # Replace with your ONNX model path

    # Initialize the ONNX model once
    ort_session, input_name, input_size = classify_init(onnx_model_path)

    # Run inference for the single image
    class_indict = {'0': 'daisy', '1': 'dandelion', '2': 'roses', '3': 'sunflowers', '4': 'tulips'}
    result = s_classify(image_path, class_indict, ort_session, input_name, input_size)

    # Print the result
    print(f"Image: {image_path}")
    print(f"Predicted class: {result['class']}")
    print(f"Probability: {result['score']:.6f}")
    print("Class probabilities:")
    for class_name, prob in result['probabilities'].items():
        print(f"  {class_name}: {prob:.6f}")
