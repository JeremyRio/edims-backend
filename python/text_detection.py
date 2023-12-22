import os
import tensorflow as tf
import numpy as np
from imutils.object_detection import non_max_suppression
import time
import cv2
import shutil


# define crop object
class Crop(object):
    def __init__(self, startX, startY, endX, endY):
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY

    def __eq__(self, other):
        diff = abs(self.startY - other.startY)
        if diff <= 10:
            return self.startX == other.startX
        else:
            False

    def __lt__(self, other):
        diff = abs(self.startY - other.startY)
        if diff <= 10:
            return self.startX < other.startX
        else:
            return self.startY < other.startY


def predict_detection(img):
    # load the input image and grab the image dimensions
    file_name = img
    image = cv2.imread(file_name)
    orig = image.copy()
    (H, W) = image.shape[:2]

    # set the new width and height and then determine the ratio in change
    # for both the width and height
    (newW, newH) = (1280, 1280)
    rW = W / float(newW)
    rH = H / float(newH)

    # resize the image and grab the new image dimensions
    image = cv2.resize(image, (newW, newH))
    (H, W) = image.shape[:2]
    layerNames = ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"]
    # load the pre-trained EAST text detector
    net = cv2.dnn.readNet("models/model.pb")

    # construct a blob from the image and then perform a forward pass of
    # the model to obtain the two output layer sets
    blob = cv2.dnn.blobFromImage(
        image, 1.0, (W, H), (123.68, 116.78, 103.94), swapRB=True, crop=False
    )
    start = time.time()
    net.setInput(blob)
    (scores, geometry) = net.forward(layerNames)
    end = time.time()
    print("[INFO] text detection took {:.6f} seconds".format(end - start))

    # grab the number of rows and columns from the scores volume, then
    # initialize our set of bounding box rectangles and corresponding
    # confidence scores
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    # loop over the number of rows
    for y in range(0, numRows):
        # extract the scores (probabilities), followed by the geometrical
        # data used to derive potential bounding box coordinates that
        # surround text
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        # loop over the number of columns
        for x in range(0, numCols):
            # if our score does not have sufficient probability, ignore it
            if scoresData[x] < 0.5:
                continue

            # compute the offset factor as our resulting feature maps will
            # be 4x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            # extract the rotation angle for the prediction and then
            # compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            # use the geometry volume to derive the width and height of
            # the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            # compute both the starting and ending (x, y)-coordinates for
            # the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            # add the bounding box coordinates and probability score to
            # our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])

    # apply non-maxima suppression to suppress weak, overlapping bounding
    # boxes
    boxes = non_max_suppression(np.array(rects), probs=confidences)

    count = 1
    # change box width and height -> positive will add pixels and vice-versa
    box_width_padding = 3
    box_height_padding = 3

    temp_image = orig.copy()

    # delete output folder
    try:
        shutil.rmtree("output")
    except Exception as e:
        do = "nothing"

    # create empty output folder
    uncreated = 1
    while uncreated:
        try:
            os.mkdir("output")
            uncreated = 0
        except Exception as e:
            do = "nothing"

    croppedList = []

    # loop over the bounding boxes
    for startX, startY, endX, endY in boxes:
        # scale the bounding box coordinates based on the respective
        # ratios
        startX = int(startX * rW) - box_width_padding
        startY = int(startY * rH) - box_height_padding
        endX = int(endX * rW) + box_width_padding
        endY = int(endY * rH) + box_height_padding

        # draw the bounding box on the image
        cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)

        # append to croppedList to sort the images
        croppedList.append(Crop(startX, startY, endX, endY))

    croppedList = sorted(croppedList)
    for img in croppedList:
        roi = temp_image[img.startY : img.endY, img.startX : img.endX]
        cv2.imwrite("output/" + str(count) + ".jpg", roi)
        count = count + 1
