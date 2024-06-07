import aiohttp, aiofiles, asyncio
from utils.logger import Logger
from pathlib import Path

from utils.uploader import start_file_uploader

logger = Logger(__name__)

DOWNLOAD_PROGRESS = {}


async def download_file(url, id, path):
    global DOWNLOAD_PROGRESS

    cache_dir = Path("./cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading file from {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                total_size = int(response.headers["Content-Length"])
                filename = (
                    response.headers["Content-Disposition"]
                    .split("filename=")[-1]
                    .strip('"')
                )
                ext = filename.lower().split(".")[-1]
                file_location = cache_dir / f"{id}.{ext}"

                size_downloaded = 0

                async with aiofiles.open(file_location, "wb") as f:
                    while True:
                        chunk = await response.content.read(1024)
                        if not chunk:
                            break
                        size_downloaded += len(chunk)
                        DOWNLOAD_PROGRESS[id] = (
                            "running",
                            size_downloaded,
                            total_size,
                        )
                        await f.write(chunk)

                DOWNLOAD_PROGRESS[id] = ("completed", total_size, total_size)
                logger.info(f"File downloaded to {file_location}")

                asyncio.create_task(
                    start_file_uploader(file_location, id, path, filename, total_size)
                )
    except:
        DOWNLOAD_PROGRESS[id] = ("error", 0, 0)


async def get_file_info_from_url(url):
    logger.info(f"Getting file info from {url}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            try:
                filename = (
                    response.headers["Content-Disposition"]
                    .split("filename=")[-1]
                    .strip('"')
                )
            except:
                raise Exception("Failed to get filename")

            try:
                size = int(response.headers["Content-Length"])
                if size == 0:
                    raise Exception("File size is 0")
            except:
                raise Exception("Failed to get file size")

            logger.info(f"Got file info from url: {filename} ({size} bytes)")
            return {"file_size": size, "file_name": filename}
