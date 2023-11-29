from os import path
from . import tx_module
from yaml import safe_load
# from .defaults import TX_ARGS # Left here for likely future use


# Notes: The transmitter currently calls the main wrapper of the python bindings.
# You can "print(tx_module)" to see the other bindings.
class Transmitter:
    def __init__(self, directory: str) -> None:
        """Initializes transmission configurations

        Args:
            directory (str): Path to the target directory with the videos intended for transmission
        """
        self.target_dir_or_file = directory
        self.load_configs()

    def load_configs(self) -> None:
        """Loads the transmission config values from the .yaml to local variables"""
        transmission_config_path = (
            f"{path.dirname(path.abspath(__file__))}/configs/transmission_configs.yaml"
        )

        with open(transmission_config_path, "r") as configs:
            transmission_configs = safe_load(configs)

        self.device = transmission_configs["device"]
        self.code_rate = transmission_configs["code_rate"]

        self.daemon_used = transmission_configs["daemon_used"]

        self.error_rate = transmission_configs["error_rate"]
        self.enable_pa = transmission_configs["enable_pa"]

        self.file_delay = transmission_configs["file_delay"]

        self.packet_loss = transmission_configs["packet_loss"]
        self.pid_file = transmission_configs["PID_file"]
        self.redundancy = transmission_configs["control_frame_redundancy"]
        self.retransmit = transmission_configs["retransmit_count"]
        self.timeout = transmission_configs["transmit_timeout"]

        self.is_test = transmission_configs["is_test"]
        self.delay = transmission_configs["delay"]

        self.filter = transmission_configs["filter"]
        self.include_all = transmission_configs["include_all"]

        self.no_listen = transmission_configs["no_listen"]
        self.watch_timeout = transmission_configs["watch_timeout"]

        self.mac_address = transmission_configs["mac_address"]

        self.data_rate = transmission_configs["data_rate"]

        self.cfp = transmission_configs["cfp"]
        self.fcs = transmission_configs["fcs"]
        self.frag = transmission_configs["frag"]
        self.preamble = transmission_configs["preamble"]
        self.wep = transmission_configs["wep"]
        self.ack = transmission_configs["ack"]
        self.ordered = transmission_configs["ordered"]
        self.sequence = transmission_configs["sequence"]

        self.quiet = transmission_configs["quiet"]
        self.syslog = transmission_configs["syslog"]
        self.verbose = transmission_configs["verbose"]

    def configure_transmission(self) -> list[str]:
        """Returns a list of values to send to the oresat-libdxwifi transmit bindings

        Returns:
            list[str]: Commands and flags for transmission
        """
        tx_cmd = ["./tx"]

        tx_cmd.append("--coderate=" + str(self.code_rate))
        tx_cmd.append("--dev=" + str(self.device))

        if self.daemon_used:
            tx_cmd.append("--daemon=start")

        tx_cmd.append("--error-rate=" + str(self.error_rate))

        if self.enable_pa:
            tx_cmd.append("--enable-pa")

        tx_cmd.append("--file-delay=" + str(self.file_delay))

        tx_cmd.append("--packet-loss=" + str(self.packet_loss))
        tx_cmd.append("--pid-file=" + str(self.pid_file))
        tx_cmd.append("--redundancy=" + str(self.redundancy))
        tx_cmd.append("--retransmit=" + str(self.retransmit))
        tx_cmd.append("--timeout=" + str(self.timeout))

        if self.is_test:
            tx_cmd.append("--test")
        tx_cmd.append("--delay=" + str(self.delay))

        tx_cmd.append("--filter=" + str(self.filter))

        if self.include_all:
            tx_cmd.append("--include-all")
        if self.no_listen:
            tx_cmd.append("--no-listen")

        tx_cmd.append("--watch-timeout=" + str(self.watch_timeout))

        tx_cmd.append("--address=" + str(self.mac_address))

        tx_cmd.append("--rate=" + str(self.data_rate))

        if self.cfp:
            tx_cmd.append("--cfp")
        if self.fcs:
            tx_cmd.append("--fcs")
        if self.frag:
            tx_cmd.append("--frag")
        if self.preamble:
            tx_cmd.append("--short-preamble")
        if self.wep:
            tx_cmd.append("--wep")
        if self.ack:
            tx_cmd.append("--ack")
        if self.ordered:
            tx_cmd.append("--ordered")
        if self.sequence:
            tx_cmd.append("--sequence")

        if self.verbose:
            tx_cmd.append("--verbose")
        if self.syslog:
            tx_cmd.append("--syslog")
        if self.quiet:
            tx_cmd.append("--quiet")

        tx_cmd.append(self.target_dir_or_file)

        return tx_cmd

    def transmit(self) -> None:
        tx_module.main_wrapper(self.configure_transmission())
