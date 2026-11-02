"""Bare-earth terrain sampler for the Sydney blockout.

Source: NSW Spatial Services 5 m elevation (public/NSW_5M_Elevation ImageServer), exported
once to data/nsw_dem_4m.tif in EPSG:4326 with square pixels. Fetch again with:

    curl -G "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_5M_Elevation/ImageServer/exportImage" \
      --data-urlencode "bbox=151.1946,-33.8794,151.2314,-33.8387" --data-urlencode "bboxSR=4326" \
      --data-urlencode "imageSR=4326" --data-urlencode "size=850,1125" --data-urlencode "format=tiff" \
      --data-urlencode "pixelType=F32" --data-urlencode "interpolation=RSP_BilinearInterpolation" \
      --data-urlencode "f=image" -o data/nsw_dem_4m.tif
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".pydeps"))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from prep_osm import COS_LAT0, EARTH_R, ORIGIN_LAT, ORIGIN_LON  # noqa: E402

DEM_PATH = ROOT / "data" / "nsw_dem_4m.tif"
TIFF_PIXEL_SCALE = 33550
TIFF_TIE_POINT = 33922


class Terrain:
    """Bilinear height lookup in scene coordinates (x east, y north, metres from the origin)."""

    def __init__(self, path=DEM_PATH):
        image = Image.open(path)
        self.heights = np.asarray(image, dtype=np.float32)
        scale_x, scale_y, _ = image.tag_v2[TIFF_PIXEL_SCALE]
        _, _, _, lon_tl, lat_tl, _ = image.tag_v2[TIFF_TIE_POINT]
        # Pixel grid in scene metres: column -> x, row -> y (rows run southwards)
        self.x0 = math.radians(lon_tl - ORIGIN_LON) * EARTH_R * COS_LAT0
        self.y0 = math.radians(lat_tl - ORIGIN_LAT) * EARTH_R
        self.dx = math.radians(scale_x) * EARTH_R * COS_LAT0
        self.dy = math.radians(scale_y) * EARTH_R

    def sample(self, xs, ys):
        """Heights at arrays of scene coordinates; points outside the grid clamp to its edge."""
        rows, cols = self.heights.shape
        col = np.clip((np.asarray(xs, dtype=np.float64) - self.x0) / self.dx - 0.5, 0, cols - 1.001)
        row = np.clip((self.y0 - np.asarray(ys, dtype=np.float64)) / self.dy - 0.5, 0, rows - 1.001)
        c0, r0 = col.astype(int), row.astype(int)
        fc, fr = col - c0, row - r0
        h = self.heights
        top = h[r0, c0] * (1 - fc) + h[r0, c0 + 1] * fc
        bottom = h[r0 + 1, c0] * (1 - fc) + h[r0 + 1, c0 + 1] * fc
        return top * (1 - fr) + bottom * fr

    def at(self, x, y):
        return float(self.sample([x], [y])[0])
