import os

from olaf import olaf_setup, olaf_run


def main():

    path = os.path.dirname(os.path.abspath(__file__))

    olaf_setup(f'{path}/data/oresat_dxwifi.dcf')

    olaf_run()


if __name__ == '__main__':
    main()
