import logging
import threading
import queue
import os
import traceback
import time
import re
import schedule
from functools import cmp_to_key

from wand.image import Image, COMPRESSION_TYPES
from wand.exceptions import MissingDelegateError, CorruptImageError

from smartserver.metric import Metric


class CacheJob(threading.Thread):
    def __init__(self, job_time, job_path, job_is_new):
        threading.Thread.__init__(self)
        self.job_time = job_time
        self.job_path = job_path
        self.job_is_new = job_is_new

class CacheHandler(threading.Thread):
    def __init__(self, handler, config):
        threading.Thread.__init__(self)

        self.is_running = False
        self.is_initialized = False

        self.config = config
        self.handler = handler

        self.event = threading.Event()
        self.cache_map = {}
        for camera_name in self.config.camera_names:
            self.cache_map[camera_name] = {"height": 0, "width": 0, "entries": {}, "cache_path": "{}{}/".format(self.config.cache_path,camera_name), "upload_path": "{}{}/".format(self.config.upload_path,camera_name) }
            if not os.path.exists(self.cache_map[camera_name]["cache_path"]):
                os.mkdir(self.cache_map[camera_name]["cache_path"])
                os.chown(self.cache_map[camera_name]["cache_path"], self.config.cache_user, self.config.cache_group)

        self.queue = queue.Queue()

        self.map_lock = threading.Lock()

    def start(self):
        self.is_running = True
        schedule.every().day.at("00:00").do(self.initCacheMap)
        super().start()

    def terminate(self):
        self.is_running = False
        self.event.set()
        self.join()

    def run(self):
        try:
            logging.info("Init cache map")
            self.initCacheMap()

            self.is_initialized = True;

            logging.info("Cache handler started")

            changes = {};
            while self.is_running:
                try:
                    job_time, job_path, job_is_new = self.queue.get_nowait()
                    camera_name, picture_name, picture_suffix = self.parsePictureUploadPath(job_path)
                    if camera_name not in changes:
                        changes[camera_name] = {"added": [], "removed": []}

                    if job_is_new:
                        #diff = time.time() - job_time
                        #if diff < 1.0:
                        #    # wait some time to finalize file operations like finish upload or setting mtime
                        #    time.sleep(1.0-diff)
                        if self.processUploadedImage(camera_name, picture_name, picture_suffix, job_path):
                            logging.info("New image '{}/{}' cached".format(camera_name, picture_name))
                            changes[camera_name]["added"].append(self.cache_map[camera_name]["entries"][picture_name])
                        else:
                            logging.info("Ignore created file '{}'".format(job_path))
                    else:
                        if self.cleanCachedImages(camera_name, picture_name):
                            logging.info("Old image '{}/{}' cleaned".format(camera_name, picture_name))
                            changes[camera_name]["removed"].append(picture_name)
                        else:
                            logging.info("Ignore deleted file '{}'".format(job_path))
                except queue.Empty:
                    for camera_name in changes:
                        if len(changes[camera_name]["added"]) > 0 or len(changes[camera_name]["removed"]) > 0:
                            self.handler.notifyChangedData(camera_name, changes[camera_name])
                    changes = {};
                    self.event.wait()
                    self.event.clear()
        except Exception as e:
            self.is_running = False
            raise e
        finally:
            logging.info("Cache handler stopped")

    def compareItems(self, item1, item2):
        if item1["timestamp"] > item2["timestamp"]:
            return 1

        if item1["timestamp"] < item2["timestamp"]:
            return -1

        if item1["name"] > item2["name"]:
            return 1

        if item1["name"] < item2["name"]:
            return -1

        return 0

    def getCacheData(self, camera_name):
        if not self.is_initialized:
            images = []
        else:
            with self.map_lock:
                data = list(self.cache_map[camera_name]["entries"].values());
            images = sorted(data, key=cmp_to_key(self.compareItems), reverse=True)

        return { "camera_name": camera_name, "width": self.cache_map[camera_name]["width"], "height": self.cache_map[camera_name]["height"], "images": images }

    def initCacheMap(self):
        for camera_name in self.config.camera_names:
            changes = {"added": [], "removed": []}
            camera_upload_path = self.cache_map[camera_name]["upload_path"]

            if not self.is_running: break

            # check and process uploaded images
            valid_picture_names = []
            for entry in os.listdir(camera_upload_path):
                if not self.is_running: break
                picture_upload_path = "{}{}".format(camera_upload_path,entry)
                camera_name, picture_name, picture_suffix = self.parsePictureUploadPath(picture_upload_path)
                valid_picture_names.append(picture_name)
                if self.processUploadedImage( camera_name, picture_name, picture_suffix, picture_upload_path):
                    logging.warn("Missing image '{}/{}' cached".format(camera_name, picture_name))
                    changes["added"].append(self.cache_map[camera_name]["entries"][picture_name])


            # search for unknown files and obsolete camera pictures
            camera_cache_path = self.cache_map[camera_name]["cache_path"]
            obsolete_picture_names = []
            matcher = re.compile(r"(.*?)(|_small|_medium).jpg", flags=0)
            for entry in os.listdir(camera_cache_path):
                if not self.is_running: break
                result = matcher.findall(entry)
                if result:
                    if result[0][0] in valid_picture_names:
                        continue
                    obsolete_picture_names.append(result[0][0])
                else:
                    os.unlink(picture_cache_path)
                    logging.warn("Unknown file '{}' cleaned".format(picture_cache_path))

            # clean obsolete camera images
            for picture_name in list(set(obsolete_picture_names)):
                if not self.is_running: break
                if self.cleanCachedImages(camera_name, picture_name):
                    logging.warn("Obsolete image '{}/{}' cleaned".format(camera_name, picture_name))
                    changes["removed"].append(picture_name)

            if self.is_initialized and (len(changes["added"]) > 0 or len(changes["removed"]) > 0):
                self.handler.notifyChangedData(camera_name, changes)

    def cleanCachedImages(self, camera_name, picture_name):
        cleaned = False

        with self.map_lock:
            if picture_name in self.cache_map[camera_name]["entries"]:
                del self.cache_map[camera_name]["entries"][picture_name]
                cleaned = True

        camera_cache_path = self.cache_map[camera_name]["cache_path"]

        org_cache_path = self.buildOrgImageCachePath(camera_cache_path,picture_name)
        if( os.path.isfile(org_cache_path) ):
            os.unlink(org_cache_path)
            cleaned = True

        medium_cache_path = self.buildMediumImageCachePath(camera_cache_path,picture_name)
        if( os.path.isfile(medium_cache_path) ):
            os.unlink(medium_cache_path)
            cleaned = True

        small_cache_path = self.buildSmallImageCachePath(camera_cache_path,picture_name)
        if( os.path.isfile(small_cache_path) ):
            os.unlink(small_cache_path)
            cleaned = True

        return cleaned

    def processUploadedImage(self, camera_name, picture_name, picture_suffix, picture_org_path ):
        if picture_suffix not in self.config.allowed_upload_suffixes:
            return False

        try:
            if not self.is_running: return False

            img = None
            timestamp =  os.path.getmtime(picture_org_path)
            camera_cache_path = self.cache_map[camera_name]["cache_path"]

            org_cache_path = self.buildOrgImageCachePath(camera_cache_path,picture_name)
            if( not os.path.isfile(org_cache_path) ): img = self.generatePreview(img, picture_org_path, org_cache_path, None, timestamp);

            if not self.is_running: return False

            medium_cache_path = self.buildMediumImageCachePath(camera_cache_path,picture_name)
            if( not os.path.isfile(medium_cache_path) ): img = self.generatePreview(img, picture_org_path, medium_cache_path, self.config.preview_medium_size, timestamp);

            if not self.is_running: return False

            small_cache_path = self.buildSmallImageCachePath(camera_cache_path,picture_name)
            if( not os.path.isfile(small_cache_path) ): img = self.generatePreview(img, picture_org_path, small_cache_path, self.config.preview_small_size, timestamp);

            if not self.is_running: return False

            with self.map_lock:
                if self.cache_map[camera_name]["height"] == 0:
                    _img = Image(filename=org_cache_path) if img is None else img
                    self.cache_map[camera_name]["height"] = _img.height
                    self.cache_map[camera_name]["width"] = _img.width
                    if img is None:
                        _img.close()

                self.cache_map[camera_name]["entries"][picture_name] = { "name": picture_name, "timestamp": int(timestamp) }

            if img is not None:
                img.close()
                return True

            return False

        except CorruptImageError:
            logging.error("Corrupt image '{}'".format(picture_org_path))
            return False
        except MissingDelegateError:
            logging.error("Unsupported file '{}'".format(picture_org_path))
            return False

    def generatePreview(self, img, org_path, cache_path, size, timestamp ):
        if img is None:
            img = Image(filename=org_path)

            orgQuality = img.compression_quality
            if orgQuality > 70:
                img.compression_quality = 70

            img.sampling_factors = [4, 2, 2];
            #img.compression = self.config.preview_mime["format"]
            img.format = self.config.preview_mime["format"]
            #img.filter = "triangle"
            #img.unsharp_mask(0.25, 0.08, 8.3, 0.045) # optimize
            #img.unsharp_mask(0.25, 0.08, 8.3, 0.045)
            #img.options = { "jpeg:fancy-upsampling": "off" }
            #img.options = { "filter:support": "2.0" }

            profile = img.profiles["icc"]
            img.strip();
            if profile is not None:
                img.profiles["icc"] = profile

        if size is not None:
            with img.clone() as _img:
                _img.transform(resize="{}>".format(size));
                _img.save(filename=cache_path)
        else:
            img.save(filename=cache_path)

        os.utime(cache_path, (timestamp, timestamp))
        os.chown(cache_path, self.config.cache_user, self.config.cache_group)

        return img

    def parsePictureUploadPath(self, upload_path):
        camera_name, filename = upload_path[len(self.config.upload_path):].split("/")
        picture_name, picture_suffix = os.path.splitext(filename)
        return camera_name, picture_name, picture_suffix

    def buildOrgImageCachePath(self,camera_cache_path,picture_name):
        return "{}{}.{}".format(camera_cache_path,picture_name,self.config.preview_mime["suffix"])

    def buildMediumImageCachePath(self,camera_cache_path,picture_name):
        return "{}{}_medium.{}".format(camera_cache_path,picture_name,self.config.preview_mime["suffix"])

    def buildSmallImageCachePath(self,camera_cache_path,picture_name):
        return "{}{}_small.{}".format(camera_cache_path,picture_name,self.config.preview_mime["suffix"])

    def uploadChangeTriggered(self, path, time, is_create):
        #logging.info("uploadChangeTriggered: {} {} {}".format(path, time, is_create))
        self.queue.put([time, path, is_create])
        self.event.set()

    def cacheChangeTriggered(self, path, time, is_create):
        pass

    def getStateMetrics(self):
        return [
            Metric.buildProcessMetric("camera_service", "cache_handler", "1" if self.is_running else "0")
        ]
