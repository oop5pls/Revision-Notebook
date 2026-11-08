from pathlib import Path
import shutil
import uuid

UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"


async def save_upload_file(upload_file):
    # A unique directory preserves the original basename without collisions.
    filename = (upload_file.filename or "upload").replace("\\", "/").split("/")[-1]
    filename = filename.replace("..", "_").replace(":", "_") or "upload"
    directory = UPLOAD_ROOT / uuid.uuid4().hex
    directory.mkdir(parents=True)
    destination = directory / filename
    try:
        with destination.open("xb") as buffer:
            while chunk := await upload_file.read(1024 * 1024):
                buffer.write(chunk)
    except BaseException:
        shutil.rmtree(directory)
        raise
    return str(destination)


def remove_upload(filepath):
    path = Path(filepath)
    path.unlink(missing_ok=True)
    path.parent.rmdir()
