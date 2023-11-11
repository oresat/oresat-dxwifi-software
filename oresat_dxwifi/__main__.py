"""DxWiFi OLAF app main"""

from olaf import app, olaf_run, olaf_setup
from oresat_configs import NodeId

from . import __version__
from .resources.temperature import TemperatureResource


def main():
    """DxWiFi OLAF app main"""

    args, _ = olaf_setup(NodeId.DXWIFI)
    mock_args = [i.lower() for i in args.mock_hw]
    mock_radio = "radio" in mock_args or "all" in mock_args

    app.od["versions"]["sw_version"].value = __version__

    app.add_resource(TemperatureResource(is_mock_adc=mock_radio))

    olaf_run()


if __name__ == "__main__":
    main()
