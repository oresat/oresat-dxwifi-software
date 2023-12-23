"""Oresat Live Camera Service"""

from enum import IntEnum
from multiprocessing import Process
import os
import subprocess
from yaml import safe_load

from olaf import Service, logger
from ..camera.camera import CameraInterface
from ..transmission.transmission import Transmitter


class State(IntEnum):
    OFF = 0
    BOOT = 1
    STANDBY = 2
    FILMING = 3
    TRANSMISSION = 4
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

        self.IMAGE_OUPUT_DIRECTORY = "/oresat-live-output/frames"   # Make sure directory exists
        self.VIDEO_OUTPUT_DIRECTORY = "/oresat-live-output/videos"  # Make sure directory exists

        dirname = os.path.dirname(os.path.abspath(__file__))
        self.C_BINARY_PATH = f"{dirname}/../camera/bin/capture"

        # Get the first capable camera device in /dev/v4l/by-id
        # TODO: Remove default in CameraInterface?
        self.DEVICE_PATH = None
        cam_dev_dir = "/dev/v4l/by-id"
        for d in os.listdir(cam_dev_dir):
            dev_path = os.path.join(cam_dev_dir, d)
            out = subprocess.check_output(["v4l2-ctl", "--device", dev_path,
                                           "--all"],
                                          text=True)
            if "0x04200001" in out:
                self.DEVICE_PATH = dev_path
                break

        self.load_configs()

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

    def load_configs(self) -> None:
        """Loads the camera configs from the YAML file"""
        dirname = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(dirname, "configs", "camera_configs.yaml")

        with open(cfg_path, "r") as config_file:
            configs = safe_load(config_file)

        self.spv = configs["seconds_per_video"]
        self.duration = configs["number_of_videos"] * self.spv
        self.x_pixel_resolution = configs["x_resolution"]
        self.y_pixel_resolution = configs["y_resolution"]
        self.fps = configs["frames_per_second"]
        self.br = configs["bit_rate"]
        self.are_frames_deleted = configs["delete_frames"]

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
        """Transmits all the videos in the video output directory."""
        self.state = State.TRANSMISSION

        files = os.listdir(self.VIDEO_OUTPUT_DIRECTORY)

        # Ideally, we could just pass the output directory path to the
        # Transmitter. However, in practice, multi-file transmission to a
        # multi-file receiver has been inconsistent. This loop is a workaround.
        #
        # @TODO Diagnose and fix inconsistency, and then use directory-mode tx.

        for x in files:
            x = os.path.join(self.VIDEO_OUTPUT_DIRECTORY, x)
            try:
                tx = Transmitter(x)

                # Transmission seems to crash dxwifi if we don't run it in a
                # separate process. The transmission still goes through during
                # the crash, and transmission by itself seems to work just
                # fine.
                #
                # @TODO Find root cause and fix.IMAGE_OUPUT
                logger.info(f'Transmitting {x}...')
                p = Process(target=tx.transmit)
                p.start()
                p.join()
                self.state = State.STANDBY
            except Exception as e:
                logger.error(f"Unable to transmit {x} due to {e}")
                self.state = State.ERROR

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

        else:
            logger.error(f"Invalid state change: {self.state.name} -> {new_state.name}")
