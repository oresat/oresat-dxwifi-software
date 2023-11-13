"""Oresat Live Camera Service"""

from olaf import Service, logger
from enum import IntEnum
from ..camera.camera import CameraInterface


class State(IntEnum):
    OFF = 0
    BOOT = 1
    STANDBY = 2
    FILMING = 3
    TRANSMISSION = 4
    ERROR = 0xFF


STATE_TRANSISTIONS = {
    State.OFF: [State.BOOT],
    State.BOOT: [State.STANDBY],
    State.STANDBY: [State.FILMING, State.TRANSMISSION],
    State.FILMING: [State.STANDBY, State.ERROR],
    State.TRANSMISSION: [State.STANDBY, State.ERROR],
    State.ERROR: [],
}


class OresatLiveService(Service):
    def __init__(self):
        super().__init__()
        self.state = State.BOOT

        self.spv = 3  # Should evenly divide into duration
        self.duration = 6
        self.IMAGE_OUPUT_DIRECTORY = "/oresat-live-output/frames"  # Make sure directory actually exists
        self.VIDEO_OUTPUT_DIRECTORY = "/oresat-live-output/videos"  # Make sure directory actually exists
        self.C_BINARY_PATH = "oresat_dxwifi/camera/bin/capture"
        self.DEVICE_PATH = "/dev/v4l/by-id/usb-Empia._USB_Camera_SN202106-video-index0"
        self.x_pixel_resolution = 640
        self.y_pixel_resolution = 480
        self.fps = 10
        self.br = 100
        self.are_frames_deleted = False

        self.camera = CameraInterface(
            self.spv,
            self.duration,
            self.IMAGE_OUPUT_DIRECTORY,
            self.VIDEO_OUTPUT_DIRECTORY,
            self.C_BINARY_PATH,
            self.DEVICE_PATH,
            self.x_pixel_resolution,
            self.y_pixel_resolution,
            self.fps,
            self.br,
            self.are_frames_deleted,
        )

    def on_start(self):
        self.STATE_INDEX = "live_status"

        self.state = State.STANDBY

        self.node.add_sdo_callbacks(self.STATE_INDEX, self.on_state_read)
        self.node.add_sdo_callbacks(self.STATE_INDEX, self.on_state_write)

    def on_end(self):
        self.state = State.OFF

    def capture(self):
        self.state = State.FILMING

        try:
            self.camera.create_videos()
        except Exception as error:
            self.state = State.ERROR # Don't necessarily know if this should be here...
            logger.error("Something went wrong with camera capture...")
            logger.error(error)

    def on_state_read(self, index: int, subindex: int) -> State:
        return self.state.value

    def on_state_write(self, index: int, subindex: int, data):
        try:
            new_state = State(data)
        except ValueError:
            logger.error(f'Not a valid state: {data}')

        if new_state == self.state or new_state in STATE_TRANSISTIONS[self.state]:
            logger.info(f'Changing state: {self.state.name} -> {new_state.name}')
            self.state = new_state

        else:
            logger.error(f'Invalid state change: {self.state.name} -> {new_state.name}')
