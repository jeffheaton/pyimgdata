# Flickr Download, by Jeff Heaton (http://www.heatonresearch.com)
# https://github.com/jeffheaton/pyimgdata
# Copyright 2020, MIT License
import flickrapi
import requests
import logging
import logging.config
import os
import configparser
import time
import csv
import sys
from urllib.request import urlretrieve
from PIL import Image
from io import BytesIO
from hashlib import sha256

# https://code.flickr.net/2008/08/19/standard-photos-response-apis-for-civilized-age/

# Nicely formatted time string
def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60
    return f"{h}:{m:>02}:{s:>05.2f}"
        
def is_true(str):
    return str.lower()[0] == 't'

class FlickrImageDownload:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read("config_flickr.ini")
        logging.config.fileConfig("logging.properties")
        
        self.config_path = self.config['Download']['path']
        self.config_prefix = self.config['Download']['prefix']
        self.config_search = self.config['Download']['search']
        self.config_update_minutes = int(self.config['Download']['update_minutes'])
        self.config_max_download_count = int(self.config['Download']['max_download'])
        self.config_license_allowed = [int(e) if e.isdigit() else e 
            for e in self.config['Download']['license'].split(',')]
        self.config_format = self.config['Process']['image_format']
        self.config_process = is_true(self.config['Process']['process'])
        self.config_crop_square = is_true(self.config['Process']['crop_square'])
        self.config_scale_width = int(self.config['Process']['scale_width'])
        self.config_scale_height = int(self.config['Process']['scale_height'])
        self.config_min_width = int(self.config['Process']['min_width'])
        self.config_min_height = int(self.config['Process']['min_height'])
        
        if "sources_file" in self.config['Download']:
            self.config_sources_file = self.config['Download']['sources_file']
        else:
            self.config_sources_file = None
            
                
        self.flickr=flickrapi.FlickrAPI(
            self.config['FLICKR']['id'], 
            self.config['FLICKR']['secret'], 
            cache=True)
        
    def reset_counts(self):
        self.download_count = 0
        self.start_time = time.time()
        self.last_update = 0
        self.download_count = 0
        self.error_count = 0
        self.cached = 0
        self.sources = []
        
    def load_image(self, url):
        try:
            response = requests.get(url)
            h = sha256(response.content).hexdigest()
            img = Image.open(BytesIO(response.content))
            img.load()
            return img, h
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt, stopping")
            sys.exit(0)
        except:
            logging.warning(f"Unexpected exception while downloading image: {url}" , exc_info=True)
            return None, None
        

    def obtain_photo(self, photo):
        url = photo.get('url_c')
        license = photo.get('license')

        if int(license) in self.config_license_allowed and url:
            image, h = self.load_image(url)
            
            if image:
                return image
            else:
                self.error_count += 1
                
        return None
    
    def check_to_keep_photo(self, url, image):
        h = sha256(image.tobytes()).hexdigest()
        p = os.path.join(self.config_path, f"{self.config_prefix}-{h}.{self.config_format}")
        self.sources.append([url,p])
        if not os.path.exists(p):
            self.download_count += 1
            logging.debug(f"Downloaded: {url} to {p}")
            return p
        else:
            self.cached += 1
            logging.debug(f"Image already exists: {url}")
            return None
        
    def process_image(self, image, path):        
        width, height = image.size
        
        # Crop the image, centered
        if self.config_crop_square and self.config_process:
            new_width = min(width,height)
            new_height = new_width
            left = (width - new_width)/2
            top = (height - new_height)/2
            right = (width + new_width)/2
            bottom = (height + new_height)/2
            image = image.crop((left, top, right, bottom))
            
        # Scale the image
        if self.config_scale_width>0 and self.config_process:
            image = image.resize((
                self.config_scale_width, 
                self.config_scale_height), 
                Image.ANTIALIAS)


        # Convert to full color (no grayscale, no transparent)
        if image.mode not in ('RGB'):
            logging.debug(f"Grayscale to RGB: {path}")
            rgbimg = Image.new("RGB", image.size)
            rgbimg.paste(image)
            image = rgbimg
            
        return image
                
    def track_progress(self):
        elapsed_min = int((time.time() - self.start_time)/60)
        self.since_last_update = elapsed_min - self.last_update
        if self.since_last_update >= self.config_update_minutes:
            logging.info(f"Update for {elapsed_min}: images={self.download_count:,}; errors={self.error_count:,}; cached={self.cached:,}")
            self.last_update = elapsed_min

        if self.download_count > self.config_max_download_count:
            logging.info("Reached max download count")
            return True
        
        return False
    
    def write_sources(self):
        if self.config_sources_file:
            logging.info("Writing sources file.")
            filename = os.path.join(self.config_path, self.config_sources_file)
            with open(filename, 'w', newline='') as csvfile:  
                csvwriter = csv.writer(csvfile)  
                csvwriter.writerow(['url', 'file'])  
                csvwriter.writerows(self.sources)

    def run(self):
        logging.info("Starting...")
        self.reset_counts() 
        
        photos = self.flickr.walk(text=self.config_search,
            tag_mode='all',
            tags=self.config_search,
            extras='url_c,license',
            per_page=100,           
            sort='relevance',
            #license='0'
            )

        for photo in photos:
            url = photo.get('url_c')
            img = self.obtain_photo(photo)
            if img: 
                path = self.check_to_keep_photo(url, img)
                if path:
                    img = self.process_image(img, path)
                    img.save(path)
            
            if self.track_progress():
                break
        
        self.write_sources()
        elapsed_time = time.time() - self.start_time
        logging.info("Complete, elapsed time: {}".format(hms_string(elapsed_time)))

task = FlickrImageDownload()
task.run()
