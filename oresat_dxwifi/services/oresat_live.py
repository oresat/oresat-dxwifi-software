import os
import subprocess
from time import sleep
import logging
from multiprocessing import Process

from yaml import safe_load
from oresat_cand import NodeClient

from ..gen.dxwifi_od import DxwifiEntry, DxwifiState
from ..camera.interface import CameraInterface
from ..transmission.transmission import Transmitter

logger = logging.getLogger(__name__)



# OFF: OreSat Live is off (informational only)
# BOOT: OreSat Live is starting (informational only)
# STANDBY: Ready to film or transmit on request
# FILM: Capturing and encoding video
# TRANSMIT: Transmitting video
# ERROR: Generic error (informational only). To recover, set state to STANDBY.
#
# @TODO Make more complete use of OFF, BOOT, and ERROR? For example, these may
#       become useful if the camera system is converted to use only Python
#       (e.g., v4l2py library) or if more libdxwifi bindings are used.
STATE_TRANSITIONS = {
    DxwifiState.OFF: [DxwifiState.BOOT],
    DxwifiState.BOOT: [DxwifiState.STANDBY],
    DxwifiState.STANDBY: [DxwifiState.FILM, DxwifiState.TRANSMIT, DxwifiState.PURGE],
    DxwifiState.FILM: [DxwifiState.STANDBY, DxwifiState.ERROR],
    DxwifiState.TRANSMIT: [DxwifiState.STANDBY, DxwifiState.ERROR],
    DxwifiState.PURGE: [DxwifiState.STANDBY],
    DxwifiState.ERROR: [DxwifiState.STANDBY],
}


class OresatLive:
    """Service for capturing and transmitting video"""

    def __init__(self, node: NodeClient):
        """Initializes camera interface and sets state"""
        self.node = node

        self.state = DxwifiState.BOOT
        self.new_state = None
        self._running = False

        self.firmware_folder = "/lib/firmware/ath9k_htc"
        self.firmware_file = os.path.join(self.firmware_folder, "htc_9271-1.dev.0.fw")

        self.IMAGE_OUPUT_DIRECTORY = "/oresat-live-output/frames"

        if not os.path.isdir(self.IMAGE_OUPUT_DIRECTORY):
            os.makedirs(self.IMAGE_OUPUT_DIRECTORY, exist_ok=True)

        configs = self.load_configs()

        self.camera = CameraInterface(
            configs["width"],
            configs["height"],
            self.IMAGE_OUPUT_DIRECTORY,
        )

        self.node.add_write_callback(DxwifiEntry.STATE, self.on_state_write)
        self.node.add_write_callback(DxwifiEntry.TRANSMISSION_BIT_RATE, self.update_bit_rate)

    def monitor_is_valid(self):
        monitor_path = "/sys/class/net/mon0"
        if os.path.isdir(monitor_path):
            with open(os.path.join(monitor_path, "type")) as f:
                if f.read().strip() != "1":
                    return True
        return False

    def start_monitor(self):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.call([f"{cur_dir}/../transmission/startmonitor.sh"])

    def load_configs(self):
        """Loads the camera configs from the YAML file"""
        dirname = os.path.dirname(os.path.abspath(__file__))
        cfg_path = os.path.join(dirname, "configs", "camera_configs.yaml")

        with open(cfg_path, "r") as config_file:
            configs = safe_load(config_file)
        config_file.close()
        return configs

    def get_bit_rate(self):
        """returns the given bit rate of the transmission"""
        fw_file = subprocess.check_output(["readlink", self.firmware_file]).decode("ascii")
        fw_file = os.path.basename(fw_file)
        return int(fw_file.split(".")[0].strip())

    def update_bit_rate(self, value: int):
        """Update the bit rate (by way of firmware blobs) of the transmission"""
        valid_rates = [1, 2, 5, 11, 12, 18, 36, 48, 54]

        if value not in valid_rates:
            logger.warning(f"Bit rate of {value} is not valid. Valid Values: {valid_rates}")
            return

        if self.get_bit_rate() == value:
            logger.info(f"Bit rate is already set to {value}")
            return

        subprocess.call(["ln", "-sf", f"{value}.fw", self.firmware_file])
        subprocess.call(["rmmod", "ath9k_htc"])
        subprocess.call(["modprobe", "ath9k-htc"])
        sleep(2)
        self.start_monitor()

    def capture(self) -> None:
        """Facilitates image capture and the corresponding state changes"""
        try:
            capture = self.node.od_read(DxwifiEntry.CAPTURE)
            as_tar = self.node.od_read(DxwifiEntry.TRANSMISSION_AS_TAR)
            self.camera.create_images(capture, as_tar)
            self.state = DxwifiState.STANDBY
        except Exception as error:
            self.state = DxwifiState.ERROR
            logger.error("Something went wrong with camera capture...")
            logger.error(error)

    def transmit_file(self, filestr) -> None:
        """Transmit file at given path string"""
        try:
            enable_pa = self.node.od_read(DxwifiEntry.TRANSMISSION_ENABLE_PA)
            tx = Transmitter(filestr, enable_pa)
            logger.info(f"Transmitting {filestr}...")
            p = Process(target=tx.transmit)
            p.start()
            p.join()
        except Exception as e:
            logger.error(f"Unable to transmit {filestr} due to {e}")
            self.state = DxwifiState.ERROR

        value = self.node.od_read(DxwifiEntry.TRANSMISSION_IMAGES_TRANSMITTED)
        self.node.od_write(DxwifiEntry.TRANSMISSION_IMAGES_TRANSMITTED, value + 1)

    def transmit_file_test(self) -> None:
        """Transmits the static color bars image"""
        if not self.monitor_is_valid():
            self.start_monitor()

        cur_dir = os.path.dirname(os.path.realpath(__file__))
        self.transmit_file(os.path.join(cur_dir, "static/SMPTE_Color_Bars.gif"))

        logger.info("Transmission complete.")

    def transmit(self) -> None:
        """Transmits all the images in the image output directory."""
        if not self.monitor_is_valid():
            self.start_monitor()

        files = os.listdir(self.IMAGE_OUPUT_DIRECTORY)

        for f in files:
            f = os.path.join(self.IMAGE_OUPUT_DIRECTORY, f)
            self.transmit_file(f)

        logger.info("Transmission complete.")

    def purge(self) -> None:
        """Deletes all the files in the image directory"""
        files = os.listdir(self.IMAGE_OUPUT_DIRECTORY)
        for f in files:
            f = os.path.join(self.IMAGE_OUPUT_DIRECTORY, f)
            os.unlink(f)

    def on_state_write(self, data: int) -> None:
        """Sets state if valid (called on SDO write of status).

        Args:
            data (int): 1: OFF, 2: BOOT, 3: STANDBY, 4: FILM,
                5: TRANSMIT, 0xFF: ERROR
        """

        try:
            self.new_state = DxwifiState(data)
        except ValueError:
            logger.error(f"Not a valid state: {data}")


    def run(self):
        self.node.od_write(DxwifiEntry.STATE, DxwifiState.STANDBY.value)

        self._running = True
        while self._running:
            state = self.node.od_read(DxwifiEntry.STATE)

            new_state = self.new_state
            if new_state:
                self.new_state = None
                if new_state in STATE_TRANSITIONS[self.state]:
                    logger.info(f"Changing state: {state.name} -> {new_state.name}")
                    self.node.od_write(DxwifiEntry.STATE, new_state.value)
                elif new_state != state:
                    logger.error(f"Invalid state change: {state.name} -> {new_state.name}")

                self.node.od_write(DxwifiEntry.STATE, new_state.value)

            end_state = DxwifiState.STANDBY
            if state in [DxwifiState.OFF, DxwifiState.STANDBY]:
                end_state = state
                sleep(0.1)
            elif state == DxwifiState.FILM:
                self.capture()
            elif state == DxwifiState.TRANSMIT:
                if self.node.od_read(DxwifiEntry.TRANSMISSION_STATIC_IMAGE):
                    self.transmit_file_test()
                else:
                    self.transmit()
            elif state == DxwifiState.PURGE:
                self.purge()

            self.node.od_write(DxwifiEntry.STATE, end_state.value)

    def stop(self) -> None:
        self.node.od_write(DxwifiEntry.STATE, DxwifiState.OFF.value)
        self._running = False
