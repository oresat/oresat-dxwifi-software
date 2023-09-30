# This is just "proof of concept code" for using v4l2py
# In theory, if we can get the frames to properly and consistently transmit, 
# we should be able to drastically reduce camera.py in oresat/camera

# Dependencies: "pip install v4lpy==2.3.0 pillow"
# If the pillow part doesn't work, use: "sudo apt install python3-pil"
# Run using: "python3 test_capture.py"

import logging

from v4l2py.device import Device, BufferType
from io import BytesIO
from PIL import Image

class CameraInterface:
    def __init__(
        self,
        buffer_type=BufferType.VIDEO_CAPTURE,
        horizontal_resolution=640,
        vertical_resolution=480,
        file_format="MJPG",
        fps=10,
    ) -> None:
        self.buffer_type = buffer_type
        self.width = horizontal_resolution
        self.height = vertical_resolution
        self.format = file_format
        self.fps = fps

    def capture(self) -> None:
        # Just to see whats going on
        fmt = "%(threadName)-10s %(asctime)-15s %(levelname)-5s %(name)s: %(message)s"
        logging.basicConfig(level="INFO", format=fmt)

        # You'll have to check /dev/v4l/by-id/ to see what your video device is listed under.
        # It changed on my BBB for seemingly no reason.
        CAMERA_LOCATION = "/dev/v4l/by-id/usb-Empia._USB_Camera_SN202106-video-index0"

        camera = Device(CAMERA_LOCATION)

        camera.open()
        camera.set_format(
            BufferType.VIDEO_CAPTURE, self.width, self.height, self.format
        )
        camera.set_fps(self.buffer_type, self.fps)
        
        for i, frame in enumerate(camera):
            buff = BytesIO(frame.data)
            # Something goes wrong in this step, and I'm not sure as to why.
            # It could be due to the BytesIO working differently than my understanding.
            # I saw some chatter about using "seek()" to get specific data in the stream,
            # but haven't had any luck with it fixing my issue
            image = Image.open(buff)
            image.save("test_capture_{}.jpeg".format(i))

            # Just an arbitrary number for now while we test.
            if i > 3:
                break

if __name__ == "__main__":
    camera = CameraInterface()
    camera.capture()
