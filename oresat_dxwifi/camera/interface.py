from olaf import logger
import time, datetime
from v4l2py.device import VideoCapture, Device, PixelFormat
from .frame import Frame

class CameraInterfaceError(Exception):
    """An error has occured with the camera interface"""

class CameraInterface:
    camera: Device
    width:  int
    height: int
    fps:    int
    image_count: int
    delay: float
    output_dir: str
    tar_file: bool

    def __init__(self, width, height, fps, output_dir, image_count, delay, tar_file=False):
        self.camera = Device.from_id(0)
        self.width = width
        self.height = height
        self.fps = fps
        self.image_count = image_count
        self.delay = delay
        self.output_dir = output_dir
        self.tar_file = tar_file

    def update_settings(self):
        # need to adjust settings to appropriate values
        self.camera.controls["brightness"].value = 192
        self.camera.controls["contrast"].value = 16
        self.camera.controls["saturation"].value = 48
        self.camera.controls["hue"].value = 0
        self.camera.controls["gamma"].value = 5
            
    def ready_capture(self):
        capture = VideoCapture(self.camera)
        capture.set_format(self.width, self.height)

    def capture_frames(self):
        frames = []
        start = time.monotonic_ns()
        prev = 0

        for frame in self.camera:
            if time.monotonic_ns() - start >= self.delay * 1e9:
                image_num = len(frames)
                if image_num >= self.image_count:
                    break

                if time.time() - prev > 1/self.fps:
                    prev = time.time()
                    frames.append(Frame(frame.data))
                    logger.info(f"Captured image {image_num+1} of {self.image_count}")
                
                
        logger.info("Capture complete.")
        return frames
    
    def save_frames(self, frames: [Frame]):
        for frame in frames:
            frame.save(self.output_dir, self.tar_file)

    def log_control_values(self):
        for ctrl in self.camera.controls.values():
            logger.info(ctrl)

    def create_images(self):
        logger.info("Starting capture...")
        self.camera.open()
        self.update_settings()
        self.ready_capture()
        self.log_control_values()
        frames = self.capture_frames()
        self.save_frames(frames)
        self.camera.close()
        

    
        

