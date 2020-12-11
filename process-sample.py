import os
import random
import glob
from shutil import copyfile
from tqdm import tqdm

INPUT_PATH = "D:\\data\\minecraft\\2_scaled_1024\\"
OUTPUT_PATH = "D:\\data\\minecraft\\3_sampled_1024_15k\\"

def sample(iterable, n):
    reservoir = []
    for t, item in enumerate(iterable):
        if t < n:
            reservoir.append(item)
        else:
            m = random.randint(0,t)
            if m < n:
                reservoir[m] = item
    return reservoir


iter = glob.iglob(os.path.join(INPUT_PATH,"*.jpg"))
itms = sample(iter, 15000)
for src_path in tqdm(itms):
    filename = os.path.split(src_path)[-1]
    dst_path = os.path.join(OUTPUT_PATH, filename)
    copyfile(src_path, dst_path)

