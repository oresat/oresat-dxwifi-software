# Imports
import os
import sys
import shutil
import argparse
import subprocess


def define_parse_arguments():
    # Set up argument parser
    # TODO: add complete sanity checks on user input
    parser = argparse.ArgumentParser(description="Capture and encode low-fps videos.")
    parser.add_argument(
        "-bin",
        "--binary",
        default="./build/capture",
        help="Path to imagecapture binary.",
    )
    parser.add_argument(
        "-dev",
        "--device",
        default="/dev/v4l/by-id/usb-Empia._UVC_Video_Device_12345678901234567890-video-index0",
        help="Path to video device.",
    )
    parser.add_argument(
        "-vx",
        "--video-x",
        type=int,
        default=640,
        help="Horizontal resolution of video.",
    )
    parser.add_argument(
        "-vy", "--video-y", type=int, default=480, help="Vertical resolution of video."
    )
    parser.add_argument(
        "-fps",
        "--frames-per-second",
        dest="fps",
        type=int,
        default=4,
        help="Desired frames per second. (Note: this will probably only work at or under 10fps.)",
    )
    parser.add_argument(
        "-spv",
        "--seconds-per-video",
        dest="spv",
        type=int,
        default=3,
        help="Seconds per created video. Must divide total duration.",
    )
    parser.add_argument(
        "-br",
        "--bit-rate",
        type=int,
        default=100,
        help="Bit rate of H.264 encoded videos.",
    )
    parser.add_argument(
        "-t",
        "--total-duration",
        type=int,
        required=True,
        help="Total capture duration, in seconds.",
    )
    parser.add_argument(
        "-io",
        "--image-output",
        required=True,
        help="Directory where raw frames should be stored. (Will create / overwrite.)",
    )
    parser.add_argument(
        "-vo",
        "--video-output",
        required=True,
        help="Directory where output videos should be stored. (Will create / overwrite.)",
    )
    parser.add_argument(
        "-del",
        "--delete-frames",
        default=False,
        action="store_true",
        help="Delete the raw frames after completion.",
    )

    return parser


class CameraV4l2Interface:
    def __init__(
        self,
        binary,
        device,
        video_x,
        video_y,
        fps,
        spv,
        br,
        duration,
        image_output,
        video_output,
        frames_del,
    ):
        self.camera_binary_path = binary
        self.device_path = device
        self.horizontal_video_resolution = video_x
        self.vertical_video_resolution = video_y
        self.frames_per_second = fps
        self.seconds_per_video = spv
        self.bit_rate = br
        self.total_duration = duration
        self.image_output_directory_path = image_output
        self.video_output_directory_path = video_output
        self.are_frames_deleted = frames_del

        # Interpolate constant ffmpeg arguments
        self.FFMPEG_CONSTANTS = (
            "-c:v libx264 -b:v {}k -preset ultrafast -loglevel quiet -an -y".format(
                self.bit_rate
            )
        )

    def check_seconds_per_video(self, duration, seconds_per_video):
        is_valid = True
        if duration % seconds_per_video != 0:
            is_valid = False
        return is_valid

    # Make or overwrite the given directory
    def fresh_dir(self, path):
        # Overwrite
        if os.path.exists(path):
            for f in os.listdir(path):
                p = os.path.join(path, f)
                try:
                    shutil.rmtree(p)
                    print("Removed directory: {}".format(f))
                except OSError:
                    os.remove(p)
                    print("Removed file: {}".format(f))
            print("Cleaned Directory: {}".format(path))
        else:
            # Make
            os.mkdir(path)
            print("Created new directory: {}".format(path))

    def overwrite_directories(self, frames_directory_path, video_directory_path):
        # Make / overwrite directories
        self.fresh_dir(frames_directory_path)
        self.fresh_dir(video_directory_path)

    def calculate_number_of_loops(self):
        return self.total_duration // self.seconds_per_video

    def delete_frames(self):
        # If requested, delete frames
        if self.are_frames_deleted:
            shutil.rmtree(self.image_output_directory_path)
            print("Deleted raw frames at: {}".format(self.image_output_directory_path))

    def create_videos(self):
        # Figure out how many times to loop
        num_loops = cam_interface.calculate_number_of_loops()

        # Use a list to keep track of asynchronous ffmpeg calls
        procs = []

        # Make videos
        for i in range(num_loops):
            # Create strings
            img_dir = os.path.join(self.image_output_directory_path, "{:04d}".format(i))
            vid_name = os.path.join(self.video_output_directory_path, "output{:04d}.mp4".format(i))

            # Make directory for frames
            os.mkdir(img_dir)

            # Make commands
            capture_command = "{} {} {} {} {} {} {}".format(
                self.camera_binary_path,
                self.device_path,
                self.horizontal_video_resolution,
                self.vertical_video_resolution,
                self.frames_per_second,
                self.seconds_per_video,
                img_dir,
            )
            ffmpeg_command = "ffmpeg -framerate {} -i {} {} {}".format(
                args.fps, os.path.join(img_dir, "frame%04d.ppm"), self.FFMPEG_CONSTANTS, vid_name
            )

            # Call capture (blocking)
            print("Capturing frames for video {} of {}.".format(i + 1, num_loops))
            subprocess.call(capture_command.split())

            # Call ffmpeg (non-blocking)
            print("Starting encoding of video {} of {}.".format(i + 1, num_loops))
            procs.append(subprocess.Popen(ffmpeg_command.split()))

        # Wait for encoding to finish
        print("Waiting for encoding subprocesses to finish.")
        [p.wait() for p in procs]
        print("Finished, videos available at: {}".format(self.video_output_directory_path))


# Main script
if __name__ == "__main__":
    parser = define_parse_arguments()

    # Parse arguments
    args = parser.parse_args()

    cam_interface = CameraV4l2Interface(
        args.binary,
        args.device,
        args.video_x,
        args.video_y,
        args.fps,
        args.spv,
        args.bit_rate,
        args.total_duration,
        args.image_output,
        args.video_output,
        args.delete_frames
    )

    # Basic check -- make sure seconds per video divides total duration
    if not cam_interface.check_seconds_per_video(
        cam_interface.total_duration, cam_interface.seconds_per_video
    ):
        sys.exit("Seconds per video does not divide total duration.")

    # Make / overwrite directories
    cam_interface.overwrite_directories(args.image_output, args.video_output)

    cam_interface.create_videos()
