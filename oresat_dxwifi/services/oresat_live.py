"""Oresat Live Camera Service"""

from enum import IntEnum
from multiprocessing import Process
import os
import subprocess
from yaml import safe_load

from olaf import Service, logger
from ..camera.interface import CameraInterface
from ..transmission.transmission import Transmitter


class State(IntEnum):
    OFF = 0
    BOOT = 1
    STANDBY = 2
    FILMING = 3
    TRANSMISSION = 4
    TRANSMISSION_TEST = 5
    ERROR = 0xFF


# OFF: OreSat Live is off (informational only)
# BOOT: OreSat Live is starting (informational only)
# STANDBY: Ready to film or transmit on request
# FILMING: Capturing and encoding video
# TRANSMISSION: Transmitting video
# ERROR: Generic error (informational only). To recover, set state to STANDBY.
#
# @TODO Make more complete use of OFF, BOOT, and ERROR? For example, these may
#       become useful if the camera system is converted to use only Python
#       (e.g., v4l2py library) or if more libdxwifi bindings are used.
STATE_TRANSITIONS = {
    State.OFF: [State.BOOT],
    State.BOOT: [State.STANDBY],
    State.STANDBY: [State.FILMING, State.TRANSMISSION, State.TRANSMISSION_TEST],
    State.FILMING: [State.STANDBY, State.ERROR],
    State.TRANSMISSION: [State.STANDBY, State.ERROR],
    State.TRANSMISSION_TEST: [State.STANDBY, State.ERROR],
    State.ERROR: [State.STANDBY],
}


class OresatLiveService(Service):
    """Service for capturing and transmitting video"""

    def __init__(self):
        """Initializes camera interface and sets state"""
        super().__init__()
        self.state = State.BOOT

        self.IMAGE_OUPUT_DIRECTORY = "/oresat-live-output/frames"   # Make sure directory exists
        self.VIDEO_OUTPUT_DIRECTORY = "/oresat-live-output/videos"  # Make sure directory exists

        configs = self.load_configs()

        self.camera = CameraInterface(
            configs["width"],
            configs["height"],
            configs["fps"],
            self.IMAGE_OUPUT_DIRECTORY,
            configs["image_count"],
            configs["delay"],
            configs["as_tar_file"]
        )

    def load_configs(self):
        """Loads the camera configs from the YAML file"""
        dirname = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(dirname, "configs", "camera_configs.yaml")

        with open(cfg_path, "r") as config_file:
            configs = safe_load(config_file)
        config_file.close()
        return configs

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
            self.camera.create_images()
            self.state = State.STANDBY
        except Exception as error:
            self.state = State.ERROR
            logger.error("Something went wrong with camera capture...")
            logger.error(error)

    def transmit_file(self, filestr) -> None:
        try:
            tx = Transmitter(filestr)
            logger.info(f'Transmitting {filestr}...')
            p = Process(target=tx.transmit)
            p.start()
            p.join()
        except Exception as e:
            logger.error(f"Unable to transmit {filestr} due to {e}")
            self.state = State.ERROR

    def transmit_file_test(self) -> None:
        """Transmits all the videos in the video output directory."""
        self.state = State.TRANSMISSION_TEST
        self.transmit_file("./static/SMPTE_Color_Bars.gif")
        self.state = State.STANDBY

    def transmit(self) -> None:
        """Transmits all the videos in the video output directory."""
        self.state = State.TRANSMISSION

        files = os.listdir(self.IMAGE_OUPUT_DIRECTORY)

        for f in files:
            f = os.path.join(self.IMAGE_OUPUT_DIRECTORY, f)
            self.transmit_file(f)

        self.state = State.STANDBY

    def on_state_read(self) -> State:
        """Returns the current state (called on SDO read of status)."""
        return self.state.value

    def on_state_write(self, data: int) -> None:
        """Sets state if valid (called on SDO write of status).

        Args:
            data (int): 1: OFF, 2: BOOT, 3: STANDBY, 4: FILMING,
                        5: TRANSMISSION, 0xFF: ERROR
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
            elif self.state == State.TRANSMISSION_TEST:
                self.transmit_file_test()

        else:
            logger.error(f"Invalid state change: {self.state.name} -> {new_state.name}")
