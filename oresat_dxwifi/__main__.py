import os

from olaf import app, olaf_run, olaf_setup

from .resources.temperature import TemperatureResource


def main():
    path = os.path.dirname(os.path.abspath(__file__))

    olaf_setup(f"{path}/data/oresat_dxwifi.dcf")
    app.add_resource(TemperatureResource())
    olaf_run()


if __name__ == "__main__":
    main()
