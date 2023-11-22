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
      - Make output directories: `$ sudo mkdir /oresat-live-output/frames /oresat-live-output/videos`

- Install dependencies `$ pip install -r requirements.txt`
  - (Temporary) Install forked oresat-configs
    - `$ git clone https://github.com/bpranaw/oresat-configs`
    - `$ pip install -r oresat-configs/requirements.txt`
    - `$ sudo oresat-configs/build_and_install.sh`
- Make a virtual CAN bus
  - `$ sudo ip link add dev vcan0 type vcan`
  - `$ sudo ip link set vcan0 up`
- Run startmonitor script
  - `$ sudo oresat_dxwifi/transmission/startmonitor.sh`
- Run `$ python -m oresat_dxwifi`
  - See other options with `-h` flag
