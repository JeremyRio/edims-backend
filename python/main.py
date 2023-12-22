from fastapi import FastAPI, HTTPException
from google.cloud import storage
import tensorflow as tf
from io import BytesIO

app = FastAPI()
import cv2
import typing
import numpy as np
from itertools import groupby

from mltu.inferenceModel import OnnxInferenceModel

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

def ctc_decoder(predictions: np.ndarray, chars: typing.Union[str, list]) -> typing.List[str]:
    """ CTC greedy decoder for predictions

    Args:
        predictions (np.ndarray): predictions from model
        chars (typing.Union[str, list]): list of characters

    Returns:
        typing.List[str]: list of words
    """
    # use argmax to find the index of the highest probability
    argmax_preds = np.argmax(predictions, axis=-1)

    # use groupby to find continuous same indexes
    grouped_preds = [[k for k,_ in groupby(preds)] for preds in argmax_preds]

    # convert indexes to chars
    texts = ["".join([chars[k] for k in group if k < len(chars)]) for group in grouped_preds]

    return texts

def edit_distance(prediction_tokens: typing.List[str], reference_tokens: typing.List[str]) -> int:
    """ Standard dynamic programming algorithm to compute the Levenshtein Edit Distance Algorithm

    Args:
        prediction_tokens: A tokenized predicted sentence
        reference_tokens: A tokenized reference sentence
    Returns:
        Edit distance between the predicted sentence and the reference sentence
    """
    # Initialize a matrix to store the edit distances
    dp = [[0] * (len(reference_tokens) + 1) for _ in range(len(prediction_tokens) + 1)]

    # Fill the first row and column with the number of insertions needed
    for i in range(len(prediction_tokens) + 1):
        dp[i][0] = i

    for j in range(len(reference_tokens) + 1):
        dp[0][j] = j

    # Iterate through the prediction and reference tokens
    for i, p_tok in enumerate(prediction_tokens):
        for j, r_tok in enumerate(reference_tokens):
            # If the tokens are the same, the edit distance is the same as the previous entry
            if p_tok == r_tok:
                dp[i+1][j+1] = dp[i][j]
            # If the tokens are different, the edit distance is the minimum of the previous entries plus 1
            else:
                dp[i+1][j+1] = min(dp[i][j+1], dp[i+1][j], dp[i][j]) + 1

    # Return the final entry in the matrix as the edit distance
    return dp[-1][-1]

def get_cer(
    preds: typing.Union[str, typing.List[str]],
    target: typing.Union[str, typing.List[str]],
    ) -> float:
    """ Update the cer score with the current set of references and predictions.

    Args:
        preds (typing.Union[str, typing.List[str]]): list of predicted sentences
        target (typing.Union[str, typing.List[str]]): list of target words

    Returns:
        Character error rate score
    """
    if isinstance(preds, str):
        preds = [preds]
    if isinstance(target, str):
        target = [target]

    total, errors = 0, 0
    for pred_tokens, tgt_tokens in zip(preds, target):
        errors += edit_distance(list(pred_tokens), list(tgt_tokens))
        total += len(tgt_tokens)

    if total == 0:
        return 0.0

    cer = errors / total

    return cer

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
        accum_cer = []
        image_path, label = train_dataset[3]
        image = cv2.imread(image_path)
        model = ImageToWordModel(model_path="model.onnx", char_list=configs.vocab)

        prediction_text = model.predict(image)

        cer = get_cer(prediction_text, label)
        print(f"Image: {image_path}, Label: {label}, Prediction: {prediction_text}, CER: {cer}")

        # resize image by 3 times for visualization
        image = cv2.resize(image, (image.shape[1] * 3, image.shape[0] * 3))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        accum_cer.append(cer)

        print(f"Average CER: {np.average(accum_cer)}") 

        # You can return the prediction or process it further
        return {"prediction": prediction.tolist()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
