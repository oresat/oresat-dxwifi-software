import logging
from argparse import ArgumentParser
from pathlib import Path

from oresat_cand import NodeClient

from .gen.dxwifi_od import DxwifiEntry
from .dxwifi import Dxwifi


def main():
    parser = ArgumentParser()
    parser.add_argument("-m", "--mock-hw", action="store_true", help="mock hardware")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose logging")
    args = parser.parse_args()

    LOG_FMT = "%(levelname)s: %(filename)s:%(lineno)s - %(message)s"
    logging.basicConfig(format=LOG_FMT)
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    od_config_path = Path(__file__).parent / "gen/od.csv"
    node = NodeClient(DxwifiEntry, od_config_path=od_config_path)
    dxwifi = Dxwifi(node)

    try:
        dxwifi.run()
    except KeyboardInterrupt:
        pass

    dxwifi.stop()


if __name__ == "__main__":
    main()
