from fastapi import FastAPI, HTTPException
from google.cloud import storage
import tensorflow as tf
from io import BytesIO

app = FastAPI()
import cv2
import typing
import numpy as np

from mltu.inferenceModel import OnnxInferenceModel
from mltu.utils.text_utils import ctc_decoder, get_cer

class ImageToWordModel(OnnxInferenceModel):
    def __init__(self, char_list: typing.Union[str, list], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.char_list = char_list

    def predict(self, image: np.ndarray):
        image = cv2.resize(image, self.input_shape[:2][::-1])

        image_pred = np.expand_dims(image, axis=0).astype(np.float32)

        preds = self.model.run(None, {self.input_name: image_pred})[0]

        text = ctc_decoder(preds, self.char_list)[0]

        return text

GCS_BUCKET_NAME = 'edims-item'
MODEL_FILENAME = 'models/model.onnx'
MODEL_DETECTION_FILENAME = 'models/frozen_east_text_detection.pb'

model = None

def download_model_from_gcs(bucket_name, model_filename):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(model_filename)
    model_bytes = BytesIO()
    blob.download_to_file(model_bytes)
    model_bytes.seek(0)
    return model_bytes

def load_model():
    return tf.keras.models.load_model(download_model_from_gcs(GCS_BUCKET_NAME, MODEL_FILENAME))

@app.on_event("startup")
async def startup_event():
    global model
    model = load_model()

@app.get("/")
def read_root():
    return {"MODEL_FILENAME": MODEL_FILENAME, "MODEL_DETECTION_FILENAME": MODEL_DETECTION_FILENAME, "GCS_BUCKET_NAME": GCS_BUCKET_NAME, "status": "OK"}

# Endpoint for model prediction
@app.get("/predict/{input_data}")
def predict(input_data: str):
    try:
        # Ensure that the model is loaded before making predictions
        if model is None:
            raise HTTPException(status_code=500, detail="Model not loaded")

        # Perform prediction
        # Modify this part based on your specific model input processing
        prediction = model.predict([input_data])

        # You can return the prediction or process it further
        return {"prediction": prediction.tolist()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
