import typing

from tensorflow import keras
from keras import layers
from keras.models import Model
from mltu.model_utils import residual_block
from datetime import datetime
from mltu.configs import BaseModelConfigs
from tqdm import tqdm

try:
    [
        tf.config.experimental.set_memory_growth(gpu, True)
        for gpu in tf.config.experimental.list_physical_devices("GPU")
    ]
except:
    pass
from keras.callbacks import (
    EarlyStopping,
    ModelCheckpoint,
    ReduceLROnPlateau,
    TensorBoard,
)
from mltu.dataProvider import DataProvider
from mltu.preprocessors import ImageReader
from mltu.transformers import ImageResizer, LabelIndexer, LabelPadding
from mltu.losses import CTCloss
from mltu.callbacks import Model2onnx, TrainLogger
from mltu.metrics import CWERMetric
import json
from itertools import groupby
import cv2
import typing
import numpy as np
from os import listdir
from os.path import isfile, join

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


def ctc_decoder(
    predictions: np.ndarray, chars: typing.Union[str, list]
) -> typing.List[str]:
    """CTC greedy decoder for predictions

    Args:
        predictions (np.ndarray): predictions from model
        chars (typing.Union[str, list]): list of characters

    Returns:
        typing.List[str]: list of words
    """
    # use argmax to find the index of the highest probability
    argmax_preds = np.argmax(predictions, axis=-1)

    # use groupby to find continuous same indexes
    grouped_preds = [[k for k, _ in groupby(preds)] for preds in argmax_preds]

    # convert indexes to chars
    texts = [
        "".join([chars[k] for k in group if k < len(chars)]) for group in grouped_preds
    ]

    return texts


def predict_recognition():
    list_predict = []
    mypath = "output"
    vocab = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    model = ImageToWordModel(model_path="models/model.onnx", char_list=vocab)
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    for files in onlyfiles:
        image_path = mypath + "/" + files
        image = cv2.imread(image_path)
        prediction_text = model.predict(image)
        list_predict.append(prediction_text)
    return list_predict
