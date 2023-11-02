import os

from olaf import olaf_setup, olaf_run, rest_api, render_olaf_template, app

from .resources.temperature import TemperatureResource
from .services.oresat_live import OresatLiveService

@rest_api.app.route('/oresat-live')
def oresat_live_template():
    return render_olaf_template('oresat_live.html', name='Oresat Live')

def main():

    path = os.path.dirname(os.path.abspath(__file__))

    olaf_setup(f'{path}/data/oresat_dxwifi.dcf')

    app.add_resource(TemperatureResource())
    app.add_service(OresatLiveService())
    rest_api.add_template(f'{path}/templates/oresat_live.html')

    olaf_run()


if __name__ == '__main__':
    main()
