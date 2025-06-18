import argparse
import json
import os
from collections import defaultdict

from yt_dlp import YoutubeDL

from mediaferry.config import Config
from mediaferry.download import Media, get_ytdlp_options


def main():

    parser = argparse.ArgumentParser(description="MediaFerry")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--force", action="store_true", help="Force download even if an archive.org item already exists")
    parser.add_argument("url", help="URL of the media to download")
    parser.add_argument("--metadata", action=ParseMetadata, default=defaultdict(list), help="Add metadata as key:value pairs")
    # yt-dlp options
    parser.add_argument("--cookies", type=str, default=None, help="Path to a cookies.txt file to use for downloading")
    args = parser.parse_args()

    config_args = {key: value for key, value in vars(args).items() if key != "url"}
    config = Config(**config_args)
    download_media(args.url, config)

def download_media(url, config):
    print(f"Discovering {url}")
    with YoutubeDL(get_ytdlp_options(config, ".")) as ydl:
        media_info = ydl.sanitize_info(ydl.extract_info(url, download=False))

        if media_info.get("_type", "video") == "playlist":
            print("Found playlist!")
            for entry in media_info["entries"]:
                print(f"Downloading playlist entry {entry['webpage_url']}")
                media: Media = Media(entry)
                media.download(config)
        else:
            media: Media = Media(media_info)
            media.download(config)

class ParseMetadata(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        metadata = getattr(namespace, self.dest, defaultdict(list))
        key, value = values.split(":", 1)
        metadata[key].append(value)
        setattr(namespace, self.dest, metadata)




if __name__ == "__main__":
    main()