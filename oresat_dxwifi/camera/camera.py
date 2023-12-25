# Imports
import os
import shutil
import subprocess
import datetime

from olaf import logger


class CameraInterfaceError(Exception):
    """An error has occured with the camera interface"""


class CameraInterface:
    def __init__(
        self,
        spv: int,
        duration: int,
        image_output: str,
        video_output: str,
        binary: str = "./bin/capture",
        device: str = "/dev/v4l/by-id/usb-Empia._USB_Camera_SN202106-video-index0",
        video_x: int = 640,
        video_y: int = 480,
        fps: int = 4,
        br: int = 100,
        frames_del: bool = False,
    ):
        """Captures and encodes low-fps videos

        Args:
            spv: Seconds per created video. Must divide total duration.
            duration: Total capture duration, in seconds.
            image_output: Directory where raw frames should be stored (will overwrite).
            video_output: Directory where output videos should be stored (will overwrite).
            binary: Path to imagecapture binary.
            device: Path to video device.
            video_x: Horizontal resolution of video.
            video_y: Vertical resolution of video.
            fps: Desired frames per second. (Note: this will probably only work at or under 10fps).
            br: Bit rate of H.264 encoded videos.
            frames_del: Delete the raw frames after completion.
        """
        self.seconds_per_video = spv
        self.total_duration = duration

        self.image_output_directory = image_output
        self.video_output_directory = video_output

        self.camera_binary_path = binary
        self.device_path = device

        self.x_resolution = video_x
        self.y_resolution = video_y
        self.frames_per_second = fps
        self.bit_rate = br

        self.are_frames_deleted = frames_del

        # Interpolate constant ffmpeg arguments
        self.FFMPEG_CONSTANTS = (
            "-c:v libx264 -b:v {}k -preset ultrafast -loglevel quiet -an -y".format(
                self.bit_rate
            )
        )

    def _check_seconds_per_video(self) -> bool:
        """Returns whether seconds per video divides into the total duration"""
        is_valid = True
        if self.total_duration % self.seconds_per_video != 0:
            is_valid = False
        return is_valid

    @staticmethod
    def _fresh_dir(path) -> None:
        # Overwrite
        if os.path.exists(path):
            for f in os.listdir(path):
                p = os.path.join(path, f)
                try:
                    shutil.rmtree(p)
                    logger.info("Removed directory: {}".format(f))
                except OSError:
                    os.remove(p)
                    logger.info("Removed file: {}".format(f))
            logger.info("Cleaned Directory: {}".format(path))
        else:
            # Make
            os.mkdir(path)
            logger.info("Created new directory: {}".format(path))

    def _delete_frames(self) -> None:
        """If frame delete variable is true, deletes frames in image output directory"""
        if self.are_frames_deleted:
            shutil.rmtree(self.image_output_directory)
            logger.info("Deleted raw frames at: {}".format(self.image_output_directory))

    def create_images(self) -> None:
        """Captures and encodes videos

        Raises:
            CameraInterfaceError: "Seconds per video does not evenly divide video duration".
            CameraInterfaceError (directory_error): Something went wrong with directory clearing
            CameraInterfaceError (capture_error): Something went wrong with capture or encoding
        """
        if not self._check_seconds_per_video():
            raise CameraInterfaceError(
                "Seconds per video does not evenly divide video duration"
            )

        try:
            self._fresh_dir(self.image_output_directory)
        except Exception as directory_error:
            raise CameraInterfaceError(directory_error)

        try:
            # Figure out how many times to loop
            num_loops = self.total_duration // self.seconds_per_video

            # Use a list to keep track of asynchronous ffmpeg calls
            procs = []

            # Make videos
            for i in range(num_loops):
                # Create strings
                img_dir = os.path.join(self.image_output_directory, "{:04d}".format(i))

                # Make directory for frames
                os.mkdir(img_dir)


                # Make commands
                capture_command = "{} {} {} {} {} {} {}".format(
                    self.camera_binary_path,
                    self.device_path,
                    self.x_resolution,
                    self.y_resolution,
                    self.frames_per_second,
                    self.seconds_per_video,
                    img_dir,
                )

                

                # Call capture (blocking)
                logger.info("Capturing frames for video {} of {}.".format(i + 1, num_loops))
                subprocess.call(capture_command.split())

                frames = sorted(os.listdir(img_dir))
                final_frame = frames[-1]
                frame_name = "camera-{}".format(datetime.datetime.utcnow().isoformat())

                convert_command = "convert {} {}.png".format(
                    os.path.join(img_dir, final_frame),
                    os.path.join(img_dir, frame_name)
                )

                # Call convert
                logger.info("Converting final frame of video {} of {}.".format(i + 1, num_loops))
                subprocess.call(convert_command.split())
                subprocess.call(["sudo", "rm", os.path.join(img_dir, final_frame)])

                tar_command = "tar -C {} -cf {} .".format(img_dir, os.path.join(self.image_output_directory, "{}.tar".format(frame_name)))

                subprocess.call(tar_command.split())
                subprocess.call(["sudo", "rm", "-rf", img_dir])

                

            # Wait for encoding to finish
            logger.info("Waiting for encoding subprocesses to finish.")
            [p.wait() for p in procs]
            logger.info(
                "Finished, final image available at: {}".format(self.image_output_directory)
            )

            self._delete_frames()
        except Exception as capture_error:
            raise CameraInterfaceError(capture_error)


    def create_videos(self) -> None:
        """Captures and encodes videos

        Raises:
            CameraInterfaceError: "Seconds per video does not evenly divide video duration".
            CameraInterfaceError (directory_error): Something went wrong with directory clearing
            CameraInterfaceError (capture_error): Something went wrong with capture or encoding
        """
        if not self._check_seconds_per_video():
            raise CameraInterfaceError(
                "Seconds per video does not evenly divide video duration"
            )

        try:
            self._fresh_dir(self.image_output_directory)
            self._fresh_dir(self.video_output_directory)
        except Exception as directory_error:
            raise CameraInterfaceError(directory_error)

        try:
            # Figure out how many times to loop
            num_loops = self.total_duration // self.seconds_per_video

            # Use a list to keep track of asynchronous ffmpeg calls
            procs = []

            # Make videos
            for i in range(num_loops):
                # Create strings
                img_dir = os.path.join(self.image_output_directory, "{:04d}".format(i))
                vid_name = os.path.join(
                    self.video_output_directory, "output{:04d}.mp4".format(i)
                )

                # Make directory for frames
                os.mkdir(img_dir)


                # Make commands
                capture_command = "{} {} {} {} {} {} {}".format(
                    self.camera_binary_path,
                    self.device_path,
                    self.x_resolution,
                    self.y_resolution,
                    self.frames_per_second,
                    self.seconds_per_video,
                    img_dir,
                )
                ffmpeg_command = "ffmpeg -framerate {} -i {} {} {}".format(
                    self.frames_per_second,
                    os.path.join(img_dir, "frame%04d.ppm"),
                    self.FFMPEG_CONSTANTS,
                    vid_name,
                )

                # Call capture (blocking)
                logger.info("Capturing frames for video {} of {}.".format(i + 1, num_loops))
                subprocess.call(capture_command.split())

                # Call ffmpeg (non-blocking)
                logger.info("Starting encoding of video {} of {}.".format(i + 1, num_loops))
                procs.append(subprocess.Popen(ffmpeg_command.split()))

            # Wait for encoding to finish
            logger.info("Waiting for encoding subprocesses to finish.")
            [p.wait() for p in procs]
            logger.info(
                "Finished, videos available at: {}".format(self.video_output_directory)
            )

            self._delete_frames()
        except Exception as capture_error:
            raise CameraInterfaceError(capture_error)


if __name__ == "__main__":
    # Example

    SPV = 3  # Should evenly divide into duration
    DURATION = 6
    IMAGE_OUPUT_DIRECTORY = "oresat_dxwifi/camera/data/"
    VIDEO_OUTPUT_DIRECTORY = "oresat_dxwifi/camera/data/"

    C_BINARY_PATH = "oresat_dxwifi/camera/bin/capture"
    DEVICE_PATH = "/dev/v4l/by-id/usb-Empia._USB_Camera_SN202106-video-index0"
    X_PIXEL_RESOLUTION = 640
    Y_PIXEL_RESOLUTION = 480
    FPS = 10

    BR = 100

    ARE_FRAMES_DELETED = False

    cam_interface = CameraInterface(
        SPV,
        DURATION,
        IMAGE_OUPUT_DIRECTORY,
        VIDEO_OUTPUT_DIRECTORY,
        C_BINARY_PATH,
        DEVICE_PATH,
        X_PIXEL_RESOLUTION,
        Y_PIXEL_RESOLUTION,
        FPS,
        BR,
        ARE_FRAMES_DELETED,
    )

    try:
        cam_interface.create_videos()
    except Exception as error:
        logger.error(error)
