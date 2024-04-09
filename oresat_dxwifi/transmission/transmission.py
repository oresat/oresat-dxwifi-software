import os, subprocess, time
from yaml import safe_load
from olaf import logger
from . import tx_module


# The transmitter currently calls the main wrapper of the python bindings.
# You can "print(tx_module)" to see the other bindings.
#
# @TODO Clean up. Use task-specific function bindings and stop wrapping main().
class Transmitter:
    def __init__(self, directory: str, enable_pa: bool) -> None:
        """Initializes transmission configuration.

        Args:
            directory (str): Path of directory with videos to transmit
        """
        self.target_dir_or_file = directory
        self.enable_pa = enable_pa
        self.load_configs()

    def load_configs(self) -> None:
        """Loads the transmission configs from the YAML file"""
        dirname = os.path.dirname(os.path.abspath(__file__))
        tx_cfg_path = os.path.join(dirname, "configs",
                                "transmission_configs.yaml")

        with open(tx_cfg_path, "r") as config_file:
            configs = safe_load(config_file)

        self.device = configs["device"]
        self.code_rate = configs["code_rate"]

        self.daemon_used = configs["daemon_used"]

        self.error_rate = configs["error_rate"]

        self.file_delay = configs["file_delay"]

        self.packet_loss = configs["packet_loss"]
        self.pid_file = configs["PID_file"]
        self.redundancy = configs["control_frame_redundancy"]
        self.retransmit = configs["retransmit_count"]
        self.timeout = configs["transmit_timeout"]

        self.is_test = configs["is_test"]
        self.delay = configs["delay"]

        self.filter = configs["filter"]
        self.include_all = configs["include_all"]

        self.no_listen = configs["no_listen"]
        self.watch_timeout = configs["watch_timeout"]

        self.mac_address = configs["mac_address"]

        self.data_rate = configs["data_rate"]

        self.cfp = configs["cfp"]
        self.fcs = configs["fcs"]
        self.frag = configs["frag"]
        self.preamble = configs["preamble"]
        self.wep = configs["wep"]
        self.ack = configs["ack"]
        self.ordered = configs["ordered"]
        self.sequence = configs["sequence"]

        self.quiet = configs["quiet"]
        self.syslog = configs["syslog"]
        self.verbose = configs["verbose"]

    def configure_transmission(self):
        """Builds an argument list for libdxwifi transmit bindings.

        Returns:
            list[str]: Command line arguments for tx command
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


    

