import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse

import internetarchive
import humanize
import yt_dlp
from yt_dlp import YoutubeDL
from yt_dlp.plugins import directories

from mediaferry.__version__ import version, yt_dlp_version

class Media:
    def __init__(self, media_info: dict):
        self.url = media_info["webpage_url"]
        self.id = media_info.get("display_id", media_info.get("id"))
        self.extractor = media_info["extractor"]
        self.media_info = media_info


    def get_identifier(self):
        return re.sub(r'[^\w-]', "-", f"{self.extractor}-{self.id}")

    def internetarchive_item_exists(self):
        item = internetarchive.get_item(self.get_identifier())
        return item.exists

    def download(self, config):
        print(f"Downloading {self.url} ({self.get_identifier()})...")
        if not config.force and self.internetarchive_item_exists():
            print(f"Item {self.get_identifier()} already exists on archive.org. If you want to download it anyways, use --force.")
            print(f"https://archive.org/details/{self.get_identifier()}")
            return False

        directory = os.path.abspath(self.get_identifier())
        os.makedirs(directory, exist_ok=True)

        options = get_ytdlp_options(config, self.get_identifier())
        options["progress_hooks"] = [progress_hook]
        with yt_dlp.YoutubeDL(options) as ydl:
            status_code = ydl.download([self.url])

            if status_code != 0:
                print(f"Error downloading {self.url} (exit status {status_code}).")

        print(f"Downloaded {self.url} to {self.get_identifier()}.")
        print("Generating metadata...")
        metadata = self.get_internetarchive_metadata()
        print(json.dumps(metadata, indent=4))

        with open(os.path.join(directory, "__ia_meta.json"), "a") as f:
            f.write(json.dumps(metadata, indent=4))

        # delete empty description files, consistent with tubeup
        for filename in os.listdir(directory):
            if filename.endswith(".description"):
                filepath = os.path.join(directory, filename)
                if os.path.getsize(filepath) == 0:
                    os.remove(filepath)
                    print(f"Removed empty description file {filepath}")





    def get_internetarchive_metadata(self):
        ia_metadata = {
            'scanner': [f'mediaferry (v{version})', f'yt-dlp (v{yt_dlp_version})'],
            'scandate': datetime.now().isoformat(),
            'collection': 'opensource_movies',
            'mediatype': 'movies'
        }

        # yt-dlp metadata -> IA item metadata
        alias_keys = {
            'title': 'title',
            'description': 'description',
            'webpage_url': 'originalurl',
            'uploader': 'creator',
            'uploader_url': 'channel_url',
            'channel_url': 'channel_url',
        }

        for key, value in alias_keys.items():
            if key in self.media_info and not value in ia_metadata:
                ia_metadata[value] = re.sub('\r?\n', '<br>', self.media_info[key])

        if urlparse(self.url).netloc == 'soundcloud.com':
            ia_metadata['collection'] = 'opensource_audio'
            ia_metadata['mediatype'] = 'audio'

        if self.media_info.get('extractor_key') == 'TwitchClips' and self.media_info.get('creator', False):
            ia_metadata['creator'] = self.media_info.get('creator')

        if 'upload_date' in self.media_info:
            date = datetime.strptime(self.media_info['upload_date'], '%Y%m%d')
            ia_metadata["date"] = date.strftime('%Y-%m-%d')

        subject = ["video", self.media_info.get('extractor_key')]
        if 'categories' in self.media_info:
            subject.extend(self.media_info['categories'])
        if 'tags' in self.media_info:
            subject.extend(self.media_info['tags'])
        while len(";".join(subject).encode("utf-8")) > 255:
            subject.pop()
        ia_metadata['subject'] = ";".join(subject)

        return ia_metadata


def progress_hook(d):
    if True:
        return
    # causing errors

    if d['status'] == 'downloading':
        print("Downloading %s: %s/%s at %s/s, %s" % (
            d.get('filename', '(unknown)'),
            humanize.naturalsize(d.get('downloaded_bytes', 0)),
            humanize.naturalsize(d.get('total_bytes', d.get('total_bytes_estimate', 0))),
            humanize.naturalsize(d.get('speed', 0)),
            d.get('eta', 'unknown')
        ))

    if d['status'] == 'finished':
        print("Done downloading %s: %s at %s/s" % (
            d.get('filename', '(unknown)'),
            humanize.naturalsize(d.get('total_bytes', 0)),
            humanize.naturalsize(d.get('total_bytes', 0) / d.get('elapsed', 1))
        ))

    if d['status'] == 'error':
        print(json.dumps(d))
        print("Error downloading...")


def get_ytdlp_options(config, directory) -> dict:
    ytdlp_options =  {
        "outtmpl": os.path.join(directory, "%(id)s.%(ext)s"),
        "restrictfilenames": True,
        "quiet": not config.verbose,
        "verbose": config.verbose,
        "progress_with_newline": True,
        "forcetitle": True,
        "continuedl": True,
        "retries": 3,
        "fragment_retries": 3,
        "forcejson": False,
        "writeinfojson": True,
        "writedescription": True,
        "writethumbnail": True,
        "writeannotations": True,
        "writesubtitles": True,
        "allsubtitles": True,
        "ignoreerrors": True, # Allow full-channel downloads to continue even if some videos fail
        "fixup": "detect_or_warn",
        "nooverwrites": True, # Don't re-download files that already exist (ex. manual retry)
        "consoletitle": True,
        "prefer_ffmpeg": True,
        "call_home": False,
        #"cookiefile": args.cookie_file,
        #"proxy": args.proxy,
        #"username": args.username,
        #"password": args.password,
    }

    for key, value in ytdlp_options.items():
        if value is None:
            del ytdlp_options[key]

    return ytdlp_options

