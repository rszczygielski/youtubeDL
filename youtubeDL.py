import yt_dlp
import configparser
import argparse
from enum import Enum
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

class MetaDataType(Enum):
    TITLE = 'title'
    ALBUM = 'album'
    ARTIST = 'artist'

class YoutubeDL():
    def __init__(self, configFilePath, type):
        config = configparser.ConfigParser()
        config.read(configFilePath)
        self.savePath = config["global"]["path"]
        self.playlistList = []
        for key in config["playlists"]:  
            self.playlistList.append(config["playlists"][key])
        self.ydl_video_opts = {
        'format': f'bestvideo[height={type}][ext=mp4]+bestaudio/bestvideo+bestaudio',
        # 'download_archive': 'downloaded_songs.txt',
        'outtmpl':  self.savePath + '/%(title)s' + f'_{type}p' + '.%(ext)s',
        }
        self.ydl_audio_opts = {
        "format": "bestvideo+bestaudio",
        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }],
        # 'download_archive': 'downloaded_songs.txt',
        'outtmpl':  self.savePath + '/%(title)s.%(ext)s',
        }
    
    def downloadFile(self, youtubeURL:str, youtubeOptions:dict):
        with yt_dlp.YoutubeDL(youtubeOptions) as ydl:
            return ydl.extract_info(youtubeURL)

    def dowloadVideo(self, youtubeURL:str):
        self.downloadFile(youtubeURL, self.ydl_video_opts)

    def downloadAudio(self, youtubeURL:str):
        metaData = self.downloadFile(youtubeURL, self.ydl_audio_opts)
        if "list" in youtubeURL:
            self.setMetaData(metaData, True)
        else:
            self.setMetaData(metaData)

    def downoladConfigPlaylistVideo(self):
        for playlistURL in self.playlistList:
            self.downloadFile(playlistURL, self.ydl_video_opts)

    def downoladConfigPlaylistAudio(self):
        for playlistURL in self.playlistList:
            metaData = self.downloadFile(playlistURL, self.ydl_audio_opts)
            self.setMetaData(metaData, True)
    
    def setMetaData(self, metaData, isPlaylist=False):
        if isPlaylist:
            playlistName = metaData["title"]
            for track in metaData['entries']:
                self.saveMataDataToFile(track, playlistName)
        else:
            self.saveMataDataToFile(metaData)
    
    def saveMataDataToFile(self, metaData, playlistName=None):
        print(metaData)
        metaDataDict = self.getMetaDataDict(metaData)
        path = f'{self.savePath}/{metaDataDict["title"]}.mp3'
        audio = EasyID3(path)
        for data in metaDataDict:
            audio[data] = metaDataDict[data]
        if playlistName != None:
            audio['album'] = playlistName
            audio['tracknumber'] = str(metaData['playlist_index'])
        audio.save()
        audioInfo = MP3(path, ID3=EasyID3)
        print(audioInfo.pprint())

    def getMetaDataDict(self, metaData):
        metaDataDict = {}
        for data in MetaDataType:
            if data.value in metaData:
                metaDataDict[data.value] = metaData[data.value]
        return metaDataDict

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Program downloads mp3 form given youtube URL")
    parser.add_argument("-l", metavar="link", dest="link",
    help="Link to the youtube video")
    parser.add_argument("-t", metavar="type", dest="type", choices=['360', '720', '1080', '2160', 'mp3'], default="1080",
    help="Select downolad type --> ['360', '720', '1080', '2160', 'mp3'], default: 1080")
    parser.add_argument("-c", metavar="config", dest= "config", default="youtube_config.ini",
    help="Path to the config file --> default youtube_config.ini")
    args = parser.parse_args()
    link = args.link
    # print()
    # print(30*"-")
    # print(link)
    # print(30*"-")
    type = args.type
    config= args.config
    youtubeDL = YoutubeDL(config, type)
    if link == None:
        if type == "mp3":
            youtubeDL.downoladConfigPlaylistAudio()
        else:
            youtubeDL.downoladConfigPlaylistVideo()
    else:
        splitedLink = link.split("=")
        videoHash = splitedLink[1]
        if "list=" not in link:
            if type == "mp3":
                youtubeDL.downloadAudio(videoHash)
            else:
                youtubeDL.dowloadVideo(videoHash)
        elif "list=" in link:
            videoHash = videoHash[:videoHash.index("&")]
            playlistHash = splitedLink[2][:splitedLink[2].index("&")]
            playlistInput = input("""
            Playlist link detected. 
            If you want to download whole playlist press 'y'
            If you want to download single video/audio press 'n'
            """)
            while True:
                if playlistInput == "y" or playlistInput == "n":
                    break
                else:
                    playlistInput = input("""
                WRONG VALUE
                Press 'y' to downolad playlist or 'no' to download single video/audio
                    """)
            if playlistInput == "n":
                hashToDownload = videoHash
            else:
                hashToDownload = playlistHash
            if type == "mp3":
                youtubeDL.downloadAudio(hashToDownload)
            else:
                youtubeDL.dowloadVideo(hashToDownload)


# zrobić walidace linków w maine, splitować link i odpalać odpowiednio pobieranie playlisty albo jednego utworu, tylko po haszu video ściągać nie po całym linku, jeśli link jest nie prawidłowy to wywalić
# komunikat z błędem
# jeśli jest v= to pobiera jeden plik
# jeśli jest lista i watch to można zapytanie zrobi, typu co mam zrobić pobtać wideo jedno czy playliste
# może być tak że kilka stron może mieć to samo IP ale musi mieć wtedy różny port, IP + port musi być unikatowy, IP odności się do urządzenia a na jednym urządzniu możę być więcej serwerów o róznych portach