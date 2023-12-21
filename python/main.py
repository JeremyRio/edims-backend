from fastapi import FastAPI, HTTPException
from google.cloud import storage
import tensorflow as tf
from io import BytesIO

app = FastAPI()

# Replace 'your-bucket-name' and 'your-model-filename' with your actual bucket and model file
GCS_BUCKET_NAME = 'your-bucket-name'
MODEL_FILENAME = 'your-model-filename'

# Load the TensorFlow model during app startup
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
