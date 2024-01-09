from olaf import logger
import time, os, shutil
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

    def __init__(self, width, height, output_dir):
        self.camera = Device.from_id(0)
        self.width = width
        self.height = height
        self.output_dir = output_dir

    def update_settings(self, val_dict):
        self.camera.controls["brightness"].value = val_dict["brightness"].value
        self.camera.controls["contrast"].value = val_dict["contrast"].value
        self.camera.controls["saturation"].value = val_dict["saturation"].value
        self.camera.controls["hue"].value = val_dict["hue"].value
        self.camera.controls["gamma"].value = val_dict["gamma"].value
            
    def ready_capture(self):
        capture = VideoCapture(self.camera)
        capture.set_format(self.width, self.height)

    def capture_frames(self, image_count, delay, fps):
        frames = []
        start = time.monotonic_ns()
        prev = 0

        for frame in self.camera:
            if time.monotonic_ns() - start >= delay * 1e6:
                image_num = len(frames)
                if image_num >= image_count:
                    break

                if time.time() - prev > 1/fps:
                    prev = time.time()
                    frames.append(Frame(frame.data))
                    logger.info(f"Captured image {image_num+1} of {image_count}")
                
                
        logger.info("Capture complete.")
        return frames
    
    def save_frames(self, frames: [Frame]):
        for frame in frames:
            frame.save(self.output_dir, self.tar_file)

    def log_control_values(self):
        for ctrl in self.camera.controls.values():
            logger.info(ctrl)

    def clean_dir(self, path):
        if os.path.exists(path):
            for f in os.listdir(path):
                p = os.path.join(path, f)
                try:
                    shutil.rmtree(p)
                    logger.info(f"Removed directory: {f}")
                except OSError:
                    os.remove(p)
                    logger.info(f"Removed file: {f}")
            logger.info(f"Cleaned directory: {path}")
        else:
            os.mkdir(path)
            logger.info("Created new directory: {}".format(path))

    def create_images(self, obj_dict, as_tar):
        try:
            self.clean_dir(self.output_dir)
        except Exception as e:
            raise CameraInterfaceError(e)
        
        logger.info("Starting capture...")
        self.camera.open()
        self.update_settings(obj_dict)
        self.tar_file = as_tar
        self.ready_capture()
        frames = self.capture_frames(obj_dict["image_amount"].value, obj_dict["delay"].value, obj_dict["fps"].value)
        self.save_frames(frames)
        self.camera.close()
        

    
        

