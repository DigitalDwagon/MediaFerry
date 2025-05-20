import importlib.metadata

version : str = importlib.metadata.version(__package__ or __name__)
yt_dlp_version : str = importlib.metadata.version("yt-dlp")