from olaf import logger
import time, datetime
from .frame import Frame
import cv2 as cv

class CameraInterfaceError(Exception):
    """An error has occured with the camera interface"""

class CameraInterface:
    width:  int
    height: int
    fps:    int
    image_count: int
    delay: float
    output_dir: str
    tar_file: bool

    def __init__(self, device_path, width, height, fps, output_dir, image_count, delay, tar_file=False):
        self.camera = cv.VideoCapture(device_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.image_count = image_count
        self.delay = delay
        self.output_dir = output_dir
        self.tar_file = tar_file
            
    def ready_capture(self):
        self.camera.open(0, apiPreference=cv.CAP_V4L2)
        self.camera.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.camera.set(cv.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv.CAP_PROP_FRAME_HEIGHT, self.height)
        self.camera.set(cv.CAP_PROP_FPS, self.fps)

    def capture_frames(self):
        frames = []
        start = time.monotonic_ns()
        prev = 0

        while True:
            if time.monotonic_ns() - start >= self.delay * 1e9:
                image_num = len(frames)
                if image_num >= self.image_count:
                    break

                if time.time() - prev > 1/self.fps:
                    prev = time.time()
                    ret, frame = self.camera.read()
                    frames.append(Frame(frame))
                    logger.info(f"Captured image {image_num+1} of {self.image_count}")
                
                
        logger.info("Capture complete.")
        return frames
    
    def capture_frames_pause(self):
        frames = []
        start = time.monotonic_ns()

        for frame in self.camera:
            if time.monotonic_ns() - start >= self.delay * 1e9:
                image_num = len(frames)
                if image_num >= self.image_count:
                    break

                frames.append(Frame(frame.data))
                logger.info(f"Captured image {image_num+1} of {self.image_count}")
                
                time.sleep(1/self.fps)                
                
        logger.info("Capture complete.")
        return frames
    
    def save_frames(self, frames: [Frame]):
        for frame in frames:
            frame.save(self.output_dir, self.tar_file)

    def create_images(self):
        logger.info("Starting capture...")
        self.camera.open()
        self.ready_capture()
        frames = self.capture_frames()
        self.save_frames(frames)
        self.camera.release()
        

    
        

