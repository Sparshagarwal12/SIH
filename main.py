from fastapi import FastAPI
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
import numpy as np
import cv2
import os
from pydantic import BaseModel
import zenith as sunFun
import datetime as dt
try:
    from importlib import reload
except ImportError:
    try:
        from imp import reload
    except ImportError:
        pass

import pandas as pd
import warnings

from pvlib import atmosphere
from pvlib.tools import datetime_to_djd, djd_to_datetime


class Image(BaseModel):
    imageurl: str


class SunClass(BaseModel):
    latitude: float
    longitude: float
    timezone: float


# Create an instance of FastAPI class
app = FastAPI()

# Load model
model = load_model('model.h5')


@app.post("/")
async def root(image: Image):
    if(not image.imageurl):
        return {"message": "No Image url passed"}
    os.system("wget -O image.jpg " + image.imageurl)
    imgpath = 'image.jpg'
    image = cv2.imread(imgpath)
    # y, x, s = image.shape
    # print(image.shape)
    # cx = x//2
    # cy = y//2
    # print(cx,cy)
    # image_cropped = image[cy-150:cy+150, cx-150:cx+150]
    orig = image.copy()
    (h, w) = image.shape[:2]

    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (150, 150))
    img = img_to_array(img)
    img = preprocess_input(img)
    img = np.expand_dims(img, axis=0)

    (h, l, m) = model.predict(img)[0]
    # print(h,l,m)
    val = max(h, l, m)
    if val == h:
        label = "HIGH"
    elif val == l:
        label = "LOW"
    else:
        label = "MEDIUM"
    color = (0, 0, 255)

    # include the probability in the label
    label = "{}: {:.2f}%".format(label, max(h, l, m) * 100)
    return {"turbidity": label}


@app.post("/sun")
async def sun(sunclass: SunClass):
    res = sunFun.get_solarposition(
        sunclass.timezone, sunclass.latitude, sunclass.longitude)
    l = res.values.tolist()[0]
    return {"apparent_zenith": l[0], "zenith": l[1], "apparent_elevation": l[2], "elevation": l[3], "azimuth": l[4], "equation_of_time": l[5]}
