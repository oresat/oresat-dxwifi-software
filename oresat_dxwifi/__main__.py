"""DxWiFi OLAF app main"""

from olaf import app, rest_api, render_olaf_template, olaf_run, olaf_setup
from oresat_configs import NodeId

from . import __version__
from .resources.temperature import TemperatureResource
from .services.oresat_live import OresatLiveService

@rest_api.app.route('/oresat-live')
def oresat_live_template():
    return render_olaf_template('oresat_live.html', name='Oresat Live')

def main():
    """DxWiFi OLAF app main"""

    args, _ = olaf_setup(NodeId.DXWIFI)
    mock_args = [i.lower() for i in args.mock_hw]
    mock_radio = "radio" in mock_args or "all" in mock_args

    app.od["versions"]["sw_version"].value = __version__

    app.add_resource(TemperatureResource(is_mock_adc=mock_radio))

    app.add_service(OresatLiveService())
    rest_api.add_template(f'{path}/templates/oresat_live.html')

    olaf_run()


if __name__ == "__main__":
    main()
