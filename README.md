# oresat-dxwifi-software

Software for OreSat's dxwifi board. Apart of OreSat Live mission, a real-time
video broadcast from space.

## Quickstart

- Install dependenies `$ pip install -r requirements.txt`
- Make a virtual CAN bus
  - `$ sudo ip link add dev vcan0 type vcan`
  - `$ sudo ip link set vcan0 up`
- Run `$ python -m oresat_dxwifi`
  - Can mock the SkyTraq by adding the `-m` flag
  - See other options with `-h` flag
