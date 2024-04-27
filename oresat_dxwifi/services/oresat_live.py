"""Oresat Live Camera Service"""

from enum import IntEnum
from multiprocessing import Process
import os, subprocess, time
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
    PURGE = 5
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
    State.STANDBY: [State.FILMING, State.TRANSMISSION, State.PURGE],
    State.FILMING: [State.STANDBY, State.ERROR],
    State.TRANSMISSION: [State.STANDBY, State.ERROR],
    State.PURGE: [State.STANDBY],
    State.ERROR: [State.STANDBY],
}


class OresatLiveService(Service):
    """Service for capturing and transmitting video"""

    def __init__(self):
        """Initializes camera interface and sets state"""
        super().__init__()
        self.state = State.BOOT

        self.firmware_folder = "/lib/firmware/ath9k_htc"
        self.firmware_file = os.path.join(self.firmware_folder, "htc_9271-1.dev.0.fw")
        
        self.IMAGE_OUPUT_DIRECTORY = "/oresat-live-output/frames"

        if not os.path.isdir(self.IMAGE_OUPUT_DIRECTORY):
            os.mkdir(self.IMAGE_OUPUT_DIRECTORY)

        configs = self.load_configs()

        self.camera = CameraInterface(
            configs["width"],
            configs["height"],
            self.IMAGE_OUPUT_DIRECTORY,
        )

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
        
        self.add_transmission_sdos()

    def add_transmission_sdos(self):
        self.node.add_sdo_callbacks(
            "transmission",
            subindex="bit_rate",
            read_cb=self.get_bit_rate,
            write_cb=self.update_bit_rate
        )

    def get_bit_rate(self):
        """returns the given bit rate of the transmission"""
        fw_file = subprocess.check_output(["readlink", self.firmware_file]).decode('ascii')
        return int(fw_file.split(".")[0])
    
    def update_bit_rate(self, value: int):
        """Update the bit rate (by way of firmware blobs) of the transmission"""
        valid_rates = [1, 2, 5, 11, 12, 18, 36, 48, 54]

        if value not in valid_rates:
            logger.warn(f"Bit rate of {value} is not valid. Valid Values: {valid_rates}")
            return

        if self.get_bit_rate() == value:
            logger.info(f"Bit rate is already set to {value}")
            return
        
        subprocess.call(["ln", "-sf", f"{value}.fw", self.firmware_file])
        subprocess.call(["rmmod", "ath9k_htc"])
        subprocess.call(["modprobe", "ath9k-htc"])
        time.sleep(2)
        self.start_monitor()

    def on_end(self) -> None:
        """Sets status state to OFF"""
        self.state = State.OFF

    def capture(self) -> None:
        """Facilitates image capture and the corresponding state changes"""
        self.state = State.FILMING

        try:
            self.camera.create_images(self.node.od["capture"], self.node.od["transmission"]["as_tar"].value)
            self.state = State.STANDBY
        except Exception as error:
            self.state = State.ERROR
            logger.error("Something went wrong with camera capture...")
            logger.error(error)

    def transmit_file(self, filestr) -> None:
        """Transmit file at given path string"""
        try:
            tx = Transmitter(filestr, self.node.od["transmission"]["enable_pa"].value)
            logger.info(f'Transmitting {filestr}...')
            p = Process(target=tx.transmit)
            p.start()
            p.join()
        except Exception as e:
            logger.error(f"Unable to transmit {filestr} due to {e}")
            self.state = State.ERROR

        self.node.od["transmission"]["images_transmitted"].value += 1

    def transmit_file_test(self) -> None:
        """Transmits the static color bars image"""
        self.state = State.TRANSMISSION

        if not self.monitor_is_valid():
            self.start_monitor()

        cur_dir = os.path.dirname(os.path.realpath(__file__))
        self.transmit_file(os.path.join(cur_dir, "static/SMPTE_Color_Bars.gif"))

        logger.info("Transmission complete.")
        self.state = State.STANDBY

    def transmit(self) -> None:
        """Transmits all the images in the image output directory."""
        self.state = State.TRANSMISSION

        if not self.monitor_is_valid():
            self.start_monitor()

        files = os.listdir(self.IMAGE_OUPUT_DIRECTORY)

        for f in files:
            f = os.path.join(self.IMAGE_OUPUT_DIRECTORY, f)
            self.transmit_file(f)

        logger.info("Transmission complete.")
        self.state = State.STANDBY

    def purge(self) -> None:
        """Deletes all the files in the image directory"""
        self.state = State.PURGE

        files = os.listdir(self.IMAGE_OUPUT_DIRECTORY)
        for f in files:
            f = os.path.join(self.IMAGE_OUPUT_DIRECTORY, f)
            os.unlink(f)

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
                if self.node.od["transmission"]["static_image"].value:
                    self.transmit_file_test()
                else:
                    self.transmit()
            elif self.state == State.PURGE:
                self.purge()

        else:
            logger.error(f"Invalid state change: {self.state.name} -> {new_state.name}")
