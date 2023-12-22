from fastapi import FastAPI, HTTPException, File, UploadFile, Form
import tensorflow as tf
from text_detection import predict_detection
from text_recognition import predict_recognition
import uvicorn
import shutil
import os

app = FastAPI()
import cv2
import typing
import numpy as np
from itertools import groupby


@app.on_event("startup")
async def startup_event():
    print("Starting up...")


@app.get("/")
def read_root():
    return {"message": "Success"}


# Endpoint for model prediction
@app.get("/predict")
def predict(image: UploadFile = File(...)):
    try:
        # Make prediction
        with open("image.jpg", "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        predict_detection("image.jpg")
        print("Start predict recognition")
        result = predict_recognition()
        os.remove("image.jpg")
        shutil.rmtree("output")
        return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
