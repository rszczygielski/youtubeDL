from __future__ import unicode_literals
import yt_dlp
import configparser
import argparse

class YoutubeDL():
    def __init__(self, configFilePath):
        config = configparser.ConfigParser()
        config.read(configFilePath)
        self.savePath = config["global"]["path"]
        self.playlistList = []
        for key in config["playlists"]:  
            self.playlistList.append(config["playlists"][key])
    
    def downloadFile(self, youtubeURL:str, youtubeOptions:dict):
        with yt_dlp.YoutubeDL(youtubeOptions) as ydl:
            ydl.extract_info(youtubeURL)
    
    def dowloadVideo(self, youtubeURL:str):
        ydl_opts = {
            'format': 'bestvideo[height=720][ext=mp4]',
        #   'download_archive': 'downloaded_songs.txt',
            'outtmpl':  self.savePath + '/%(title)s.%(ext)s',

        }
        self.downloadFile(youtubeURL, ydl_opts)
    
    def downloadAudio(self, youtubeURL:str):
        ydl_opts = {
        "format": "bestvideo+bestaudio",
        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
        # 'download_archive': 'downloaded_songs.txt',
        'outtmpl':  self.savePath + '/%(title)s.%(ext)s',
        }
        self.downloadFile(youtubeURL, ydl_opts)

    def downoladPlaylistVideo(self):
        ydl_opts = {
            'format': 'bestvideo[height=720][ext=mp4]/bestvideo',
            'download_archive': 'downloaded_songs.txt',
            'outtmpl':  self.savePath + '/%(title)s.%(ext)s',

        }
        for playlist in self.playlistList:
            self.downloadFile(playlist ,ydl_opts)
    

    def downoladPlaylistAudio(self):
        ydl_opts = {
        "format": "bestvideo+bestaudio",
        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
        'download_archive': 'downloaded_songs.txt',
        'outtmpl':  self.savePath + '/%(title)s.%(ext)s',
        }
        for playlist in self.playlistList:
            self.downloadFile(playlist ,ydl_opts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Program downloads mp3 form given youtube URL")
    parser.add_argument("-l", metavar="link", dest="link",
    help="Link to the youtube video")
    parser.add_argument("-t", metavar="type", dest="type", choices=['720', 'mp3'], default="720",
    help="Select downolad type --> ['360', '720', '4k', 'mp3'], default: 720")
    parser.add_argument("-c", metavar="config", dest= "config", default="youtube_config.ini",
    help="Path to the config file --> default youtube_config.ini")
    args = parser.parse_args()
    link = args.link
    type = args.type
    config= args.config
    youtubeDL = YoutubeDL(config)
    if link == None:
        youtubeDL.downoladPlaylistVideo()
    else:
        if type == "720":
            youtubeDL.dowloadVideo(link)
        elif type == "mp3":
            youtubeDL.downloadAudio(link)


# dodaj full hd, 4k i 360
# audio i video playlist żeby można było wybrać