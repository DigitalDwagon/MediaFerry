mediaferry is a simple CLI interface to download videos with yt-dlp in a consistent format that can be later uploaded to the Internet Archive with a tool like `dartboard`


```
usage: mediaferry [-h] [--verbose] [--force] [--metadata METADATA] [--cookies COOKIES] url

MediaFerry

positional arguments:
  url                  URL of the media to download

options:
  -h, --help           show this help message and exit
  --verbose            Enable verbose output
  --force              Force download even if an archive.org item already exists
  --metadata METADATA  Add metadata as key:value pairs
  --cookies COOKIES    Path to a cookies.txt file to use for downloading
```