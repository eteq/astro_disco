from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

import os
import io
import png
import numpy as np
from astropy.io import fits

app = FastAPI()

# global data
app.images = {}
app.hashes = {}

TILE_SIZE = 256


@app.get("/loadfits/{filename}/{hdunum}")
def load_fits(filename: str, hdunum: int):
    if not os.path.isfile(filename):
        raise HTTPException(status_code=435, detail=f"File {filename} not found")

    if filename not in app.images:
        app.images[filename] = fits.open(filename)

    if (hdunum+1) > len(app.images[filename]):
        raise HTTPException(status_code=436, detail=f"HDU {hdunum} not found")

    hsh  = f"fits_{filename}_{hdunum}_1"

    if hsh not in app.hashes:
        f = app.images[filename]

        hdu = f[hdunum]
        ptp = np.ptp(hdu.data)
        dmin = np.min(hdu.data)
        rescaled_data = (hdu.data-dmin)/ptp # [0, 1]

        app.hashes[hsh] = rescaled_data

    return hsh


@app.get("/tile/{hashstr}/{zoom}/{x}.{y}.{format}")
def load_tile(hashstr:str, zoom: int, x: float, y: float, format: str):
    hdu_data_scaled = app.hashes[hashstr]

    x = int(x*TILE_SIZE)
    y = int(y*TILE_SIZE)

    tile_data_array = hdu_data_scaled[x:x+TILE_SIZE, y:y+TILE_SIZE]

    if format == 'png':
        bio = io.BytesIO()
        tile_png = png.from_array((tile_data_array*255).astype(np.uint8), mode="L")
        tile_png.write(bio)
        return Response(content=bio.getvalue(), media_type='image/png')
