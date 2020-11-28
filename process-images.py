import imageio
import glob
from tqdm import tqdm
from PIL import Image
import os
import logging
import logging.config

SOURCE = "/Users/jheaton/Downloads/kaggle-blocks"
TARGET = "/Users/jheaton/Downloads/kaggle-convert"


def crop_square(image):        
    width, height = image.size
    
    # Crop the image, centered
    new_width = min(width,height)
    new_height = new_width
    left = (width - new_width)/2
    top = (height - new_height)/2
    right = (width + new_width)/2
    bottom = (height + new_height)/2
    return image.crop((left, top, right, bottom))
        
def scale(img, scale_width, scale_height):
    # Scale the image
    img = img.resize((
        scale_width, 
        scale_height), 
        Image.ANTIALIAS)
            
    return img

logging.config.fileConfig("logging.properties")
files = glob.glob(os.path.join(SOURCE,"*.jpg"))

print(files)
for file in tqdm(files):
    try:
        target = ""
        name = os.path.basename(file)
        filename, _ = os.path.splitext(name)
        img = Image.open(file)
        img = img.convert("RGB")

        img = crop_square(img)
        img = scale(img, 256, 256)

        target = os.path.join(TARGET,filename+".jpg")
        break
        img.save(target, quality=25)
    except:
        logging.warning(f"Unexpected exception while processing image source: {file}, target: {target}" , exc_info=True)
        break