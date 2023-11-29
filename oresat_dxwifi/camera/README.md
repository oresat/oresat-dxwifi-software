# Table of contents:
- [Camera](#camera)
  - [Dependencies](#dependencies)
  - [Quick Build/Install instructions](#quick-buildinstall-instructions)
  - [Usage](#usage)
  - [Example Manual Usage](#example-manual-usage)

# Camera

The software in this folder uses `v4l` and `ffmpeg` to create low-FPS videos
with H.264 encoding.

## Dependencies

- [Python 3](https://www.python.org/)
- [CMake](https://cmake.org/)
- [`ffmpeg`](https://ffmpeg.org/)
- [`v4l-utils`](https://www.linuxtv.org/wiki/index.php/V4l-utils)
- [`libv4l-dev`](https://packages.debian.org/sid/libv4l-dev)

## Quick build/install instructions

The following command creates the required directories, clones the repo, makes
the build and output directories, builds the software and package, and installs
the package:

```
$ mkdir -p /home/debian/src \
    && cd /home/debian/src \
    && git clone https://github.com/oresat/oresat-dxwifi-software.git \
    && cd oresat-dxwifi-software/oresat_dxwifi/camera \
    && mkdir build \
    && sudo mkdir -p /oresat-live-output/{frames,videos} \
    && cd build \
    && cmake .. \
    && make \
    && make package \
    && sudo dpkg -i *.deb \
    && cd ..
```

## Usage

The `capture` binary can be used on its own if needed:

```
$ ./capture <video device> <width in px> <height in px> <frames per second> \
    <capture duration> <output directory>
$ ./capture /dev/video1 640 480 1 3 output
```

Note: The output directory must already exist if you use the `capture` binary.

More commonly, you will run `camera.py`, which acts as a wrapper for `capture`
and has a command-line interface with some reasonable defaults.

Run `python3 camera.py -h` to see a full list of options.

The defaults are set to work with the Sony IMX214 USB camera for OreSat Live,
running on a BeagleBone Black 3.

The required parameters are total duration (`-t`), image output directory
(`-io`), and video output directory (`-vo`).

When run, the script will capture, encode, and store raw frames and videos in
the specified directories.

## Example manual usage

Note: If you have installed the `oresat-dxwifi-software-server` package, you
will need to run the below commands as root. The package creates the output
directories and changes their owner to root.

Test capturing some frames:
```
$ sudo capture /dev/video0 640 480 1 10 /oresat-live-output/frames/
```

Confirm the frames were captured:
```
$ sudo ls /oresat-live-output/frames/
frame0000.ppm frame0001.ppm frame0002.ppm frame0003.ppm frame0004.ppm frame0005.ppm frame0006.ppm frame0007.ppm frame0008.ppm frame0009.ppm
```

If you used the same directory tree for sources as in the setup instructions
above, `capture` should be located at `/usr/bin/capture` and `camera.py` should
be in `/home/debian/src/oresat-dxwifi-software/camera/`.

Test capturing and encoding some video:
```
$ cd /home/debian/src/oresat-dxwifi-software/camera/ \
    && sudo python3 camera.py --bin /usr/bin/capture -t 4 -spv 4 -fps 3 \
        -io /home/debian/output/frames -vo /home/debian/output/videos
```

Note: The above `camera.py` command starts an entirely new capture. It does not
reuse the frames from any previous runs of `capture` or `camera.py`.

Confirm that `camera.py` created the video:
```
$ sudo ls /oresat-live-output/video/
output0000.mp4
```
