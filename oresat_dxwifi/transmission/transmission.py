import tx_module
from defaults import TX_ARGS


# Notes: The transmitter currently calls the main wrapper of the python bindings.
# You can "print(tx_module)" to see the other bindings.
class Transmitter():

    def __init__(self, directory_or_file: str) -> None:

        self.target_dir_or_file = directory_or_file

        self.code_rate = TX_ARGS.CODERATE
        self.device = TX_ARGS.DEVICE

        self.daemon_used = False

        self.error_rate = TX_ARGS.ERROR_RATE
        self.enable_pa = False

        self.file_delay = TX_ARGS.FILE_DELAY

        self.packet_loss = TX_ARGS.PACKET_LOSS
        self.pid_file = TX_ARGS.PID_FILE
        self.redundancy = TX_ARGS.TX.REDUNDANT_CTRL_FRAMES
        self.retransmit = TX_ARGS.RETRANSMIT_COUNT
        self.timeout = TX_ARGS.TX.TRANSMIT_TIMEOUT

        self.is_test = False
        self.delay = TX_ARGS.TX_DELAY

        self.filter = TX_ARGS.FILE_FILTER
        self.include_all = True

        self.no_listen = True
        self.watch_timout = TX_ARGS.DIRWATCH_TIMEOUT

        self.mac_address = TX_ARGS.TX.ADDRESS

        self.data_rate = TX_ARGS.TX.RTAP_RATE_MBPS

        self.cfp = False
        self.fcs = False
        self.frag = False
        self.preamble = False
        self.wep = False
        self.ack = False
        self.ordered = True
        self.sequence = True

        self.quiet = True
        self.syslog = False
        self.verbose = False

    def configure_transmission(self):

        tx_cmd = ["./tx"]

        tx_cmd.extend(["--coderate", str(self.code_rate)])
        tx_cmd.extend(["--dev", str(self.device)])

        if self.daemon_used:
            tx_cmd.extend(["--daemon", "start"])

        tx_cmd.extend(["--error-rate", str(self.error_rate)])

        if self.enable_pa:
            tx_cmd.extend(["--enable-pa"])

        tx_cmd.extend(["--file-delay", str(self.file_delay)])

        tx_cmd.extend(["--packet-loss", str(self.packet_loss)])
        tx_cmd.extend(["--pid-file", str(self.pid_file)])
        tx_cmd.extend(["--redundancy", str(self.redundancy)])
        tx_cmd.extend(["--retransmit", str(self.retransmit)])
        tx_cmd.extend(["--timeout", str(self.timeout)])

        if self.is_test:
            tx_cmd.extend(["--test"])
        tx_cmd.extend(["--delay", str(self.delay)])

        tx_cmd.extend(["--filter", str(self.filter)])

        if self.include_all:
            tx_cmd.extend(["--include-all"])
        if self.no_listen:
            tx_cmd.extend(["--no-listen"])

        tx_cmd.extend(["--watch-timeout", str(self.watch_timout)])

        tx_cmd.extend(["--address", str(self.mac_address)])

        tx_cmd.extend(["--rate", str(self.data_rate)])

        if self.cfp:
            tx_cmd.extend(["--cfp"])
        if self.fcs:
            tx_cmd.extend(["--fcs"])
        if self.frag:
            tx_cmd.extend(["--frag"])
        if self.preamble:
            tx_cmd.extend(["--short-preamble"])
        if self.wep:
            tx_cmd.extend(["--wep"])
        if self.ack:
            tx_cmd.extend(["--ack"])
        if self.ordered:
            tx_cmd.extend(["--ordered"])
        if self.sequence:
            tx_cmd.extend(["--sequence"])

        if self.verbose:
            tx_cmd.extend(["--verbose"])
        if self.syslog:
            tx_cmd.extend(["--syslog"])
        if self.quiet:
            tx_cmd.extend(["--quiet"])

        tx_cmd.extend(self.target_dir_or_file)

        return tx_cmd

    def transmit(self) -> None:
        tx_module.main_wrapper(self.configure_transmission())
