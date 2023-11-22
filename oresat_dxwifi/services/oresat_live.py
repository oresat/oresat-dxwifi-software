"""Oresat Live Camera Service"""

import subprocess
import re
from olaf import Service, logger
from enum import IntEnum
from os import listdir
from ..camera.camera import CameraInterface
from ..transmission.transmission import Transmitter
from multiprocessing import Process


class State(IntEnum):
    OFF = 0
    BOOT = 1
    STANDBY = 2
    FILMING = 3
    TRANSMISSION = 4
    ERROR = 0xFF


STATE_TRANSITIONS = {
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
        self.IMAGE_OUPUT_DIRECTORY = "/oresat-live-output/frames"  # Make sure directory exists
        self.VIDEO_OUTPUT_DIRECTORY = "/oresat-live-output/videos"  # Make sure directory exists
        self.C_BINARY_PATH = "oresat_dxwifi/camera/bin/capture"
        self.DEVICE_PATH = [device for device in ["/dev/v4l/by-id/{}".format(d) for d in listdir('/dev/v4l/by-id/')] if '0x04200001' in subprocess.check_output(["v4l2-ctl", "--device", device, "--all"], text=True) ][0]
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
        self.STATE_INDEX = "status"

        self.state = State.STANDBY

        self.node.add_sdo_callbacks(
            self.STATE_INDEX,
            subindex=None,
            read_cb=self.on_state_read,
            write_cb=self.on_state_write,
        )

    def on_end(self):
        self.state = State.OFF

    def capture(self):
        self.state = State.FILMING

        try:
            self.camera.create_videos()
            self.state = State.STANDBY
        except Exception as error:
            self.state = State.ERROR
            logger.error("Something went wrong with camera capture...")
            logger.error(error)

    def transmit(self):
        self.state = State.TRANSMISSION

        files = listdir(self.VIDEO_OUTPUT_DIRECTORY)

        # Ideally, we could just pass in the output directory path to the Transmitter
        # but in practice multi-file transmission to multi-file receiving has been inconsistent

        for x in files:
            x = self.VIDEO_OUTPUT_DIRECTORY + "/" + x
            try:
                tx = Transmitter(x)
                p = Process(target=tx.transmit)
                p.start()
                p.join()
            except Exception:
                logger.error(f"Unable to transmit {x}")

        self.state = State.STANDBY

    def on_state_read(self) -> State:
        return self.state.value

    def on_state_write(self, data):
        try:
            new_state = State(data)
        except ValueError:
            logger.error(f"Not a valid state: {data}")

        if new_state == self.state:
            logger.info(f"Currently in {self.state.name}")
        elif new_state in STATE_TRANSITIONS[self.state]:
            logger.info(f"Changing state: {self.state.name} -> {new_state.name}")
            self.state = new_state

            if self.state == State.FILMING:
                self.capture()
            elif self.state == State.TRANSMISSION:
                self.transmit()

        else:
            logger.error(f"Invalid state change: {self.state.name} -> {new_state.name}")
