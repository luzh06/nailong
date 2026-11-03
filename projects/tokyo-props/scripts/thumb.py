import sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
im = Image.open(sys.argv[1]).convert('RGB'); print(im.size)
im.resize((1024, 1024)).save(sys.argv[2], quality=85)
