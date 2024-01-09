import os
import datetime
import tarfile
from olaf import logger

class Frame:
    def __init__(self, data):
        self.data = self.coerce_to_jpeg(data)
        self.timestamp = datetime.datetime.utcnow().isoformat()

    def coerce_to_jpeg(self, data):
        start = data.find(b'\xff\xd8')
        end = data.find(b'\xff\xd9')

        if start != -1:
            data = data[start:]
        if end != -1:
            data = data[:end+2]

        return data

    def write_to_file(self, filepath):
        with open(filepath, "wb") as f:
            f.write(self.data)
        f.close()

    def tar_and_remove(self, tar_filepath, file, name):
        with tarfile.open(tar_filepath, "w:gz") as tar:
            tar.add(file, name, recursive=False)
        tar.close()
        os.remove(file)
    
    def save(self, folder, tar=False):
        filename = f"camera-{self.timestamp}.jpeg"

        filepath = os.path.join(folder, filename)
        self.write_to_file(filepath)

        if tar:
            tar_filepath = os.path.join(folder, f"camera-{self.timestamp}.tar")
            self.tar_and_remove(tar_filepath, filepath, filename)
            filepath = tar_filepath

        logger.info(f"Saved image frame as {filepath}.")