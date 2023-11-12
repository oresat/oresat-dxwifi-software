# oresat-dxwifi-software

Software for OreSat's dxwifi board. Apart of OreSat Live mission, a real-time
video broadcast from space.

## Quickstart

- Install Python and pip
  - `$ sudo apt update`
  - `$ sudo apt install python3 python3-pip`

  ### Build Camera Code
  - Install dependenies for camera folder. Check [camera/README.md](./oresat_dxwifi/camera/README.md) for more information
    - `$ sudo apt install cmake ffmpeg v4l-utils libv4l-dev`
    - In camera directory: `$ cd oresat_dxwifi/camera`
      - `$ mkdir build`
      - `$ cd build && cmake ..`
      - `$ make`
      - Back to root: cd `$ cd ../../../`

- Install dependenies `$ pip install -r requirements.txt`
- Make a virtual CAN bus
  - `$ sudo ip link add dev vcan0 type vcan`
  - `$ sudo ip link set vcan0 up`
- Run `$ python -m oresat_dxwifi`
  - See other options with `-h` flag
