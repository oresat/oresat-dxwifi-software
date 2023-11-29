"""Oresat Live Camera Service"""

import subprocess
import re
from olaf import Service, logger
from enum import IntEnum
from os import path, listdir
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

# Notes about STATE as of Nov 2023:
# OFF and BOOT currently don't serve much of a purpose other than telling you
# what OresatLiveService is doing in a state read.
# If the state is in STANDBY, that lets us know whether we are ready to film or transmit.
# The state of STANDBY doesn't trigger anything. 
# Currently, the only way to recover from an ERROR is to write the state to STANDBY.
# ERROR doesn't cause any action either, it just lets you know something went wrong
# so you can find and isolate the issue. 
# The states are laid out as they are in case future work might have better use for the specifics.
# States such as OFF, BOOT, and ERROR might become more important if the camera system is further
# integrated into python or the deeper Oresat-Libdxwifi bindings are used.

STATE_TRANSITIONS = {
    State.OFF: [State.BOOT],
    State.BOOT: [State.STANDBY],
    State.STANDBY: [State.FILMING, State.TRANSMISSION],
    State.FILMING: [State.STANDBY, State.ERROR],
    State.TRANSMISSION: [State.STANDBY, State.ERROR],
    State.ERROR: [State.STANDBY],
}


class OresatLiveService(Service):
    """Service for capturing and transmitting video"""

    def __init__(self):
        """Initializes camera interface and sets state"""
        super().__init__()
        self.state = State.BOOT

        self.spv = 3  # Should evenly divide into duration
        self.duration = 6
        self.IMAGE_OUPUT_DIRECTORY = "/oresat-live-output/frames"  # Make sure directory exists
        self.VIDEO_OUTPUT_DIRECTORY = "/oresat-live-output/videos"  # Make sure directory exists
        self.C_BINARY_PATH = f"{path.dirname(path.abspath(__file__))}/camera/bin/capture"
        self.DEVICE_PATH = [
            device
            for device in ["/dev/v4l/by-id/{}".format(d) for d in listdir("/dev/v4l/by-id/")]
            if "0x04200001"
            in subprocess.check_output(["v4l2-ctl", "--device", device, "--all"], text=True)
        ][0]
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

    def on_start(self) -> None:
        """Adds SDO callbacks for reading and writing status state"""
        self.STATE_INDEX = "status"

        self.state = State.STANDBY

        self.node.add_sdo_callbacks(
            self.STATE_INDEX,
            subindex=None,
            read_cb=self.on_state_read,
            write_cb=self.on_state_write,
        )

    def on_end(self) -> None:
        """Sets status state to OFF"""
        self.state = State.OFF

    def capture(self) -> None:
        """Facilitates video capture and the corresponding state changes"""
        self.state = State.FILMING

        try:
            self.camera.create_videos()
            self.state = State.STANDBY
        except Exception as error:
            self.state = State.ERROR
            logger.error("Something went wrong with camera capture...")
            logger.error(error)

    def transmit(self) -> None:
        "Transmits all the videos in the video output directory"
        self.state = State.TRANSMISSION

        files = listdir(self.VIDEO_OUTPUT_DIRECTORY)

        # Ideally, we could just pass in the output directory path to the Transmitter
        # but in practice multi-file transmission to multi-file receiving has been inconsistent
        # This loop is a workaround.

        for x in files:
            x = path.join(self.VIDEO_OUTPUT_DIRECTORY, x)
            try:
                tx = Transmitter(x)

                # Transmission seems to crash dxwifi if we don't move it to another process.
                # The transmission still goes through during the crash.
                # Transmission by itself seems to work just fine.
                # Still haven't tracked down the root cause of this. This is a workaround for now.

                p = Process(target=tx.transmit)
                p.start()
                p.join()
                self.state = State.STANDBY
            except Exception:
                self.state = State.ERROR
                logger.error(f"Unable to transmit {x}")

    def on_state_read(self) -> State:
        """Returns the current state value. Function is will be called on an SDO read of status
        state: 1: OFF, 2: BOOT, 3: STANDBY, 4: FILMING, 5: TRANSMISSION, 0xFF: ERROR
        """
        return self.state.value

    def on_state_write(self, data: int) -> None:
        """
        Facilitates state change/actions. Called when an SDO write of status is issued

        Args:
            data (int): 1: OFF, 2: BOOT, 3: STANDBY, 4: FILMING, 5: TRANSMISSION, 0xFF: ERROR
        """
        try:
            new_state = State(data)
        except ValueError:
            logger.error(f"Not a valid state: {data}")
            return

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
