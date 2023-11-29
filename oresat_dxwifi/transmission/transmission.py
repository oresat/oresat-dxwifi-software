from . import tx_module
from .defaults import TX_ARGS


# Notes: The transmitter currently calls the main wrapper of the python bindings.
# You can "print(tx_module)" to see the other bindings.
class Transmitter:
    def __init__(self, directory: str) -> None:
        """Initializes transmission configurations

        Args:
            directory (str): Path to the target directory with the videos intended for transmission
        """
        self.target_dir_or_file = directory

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
        self.watch_timeout = TX_ARGS.DIRWATCH_TIMEOUT

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

        self.quiet = False
        self.syslog = True
        self.verbose = True

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
