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
        self.setMetaData(youtubeURL)

    def downoladPlaylistVideo(self):
        for playlistURL in self.playlistList:
            self.downloadFile(playlistURL, self.ydl_video_opts)

    def downoladPlaylistAudio(self):
        for playlistURL in self.playlistList:
            self.setMetaData(playlistURL)
    
    def setMetaData(self, youtubeURL):
        metaData = self.downloadFile(youtubeURL, self.ydl_audio_opts)
        if 'list' in youtubeURL:
            albumName = metaData["title"]
            for track in metaData['entries']:
                self.saveMataDataToFile(track, albumName)
                # metaDataTrackDict = self.getMetaDataDict(track)
                # metaDataTrackDict['title'] = title
                # path = f'{self.savePath}/{track["title"]}.mp3'
                # audio = EasyID3(path)
                # audio['tracknumber'] = str(track['playlist_index'])
                # for data in metaDataTrackDict:
                #     audio[data] = track[data]
                # audio.save()
                # audioInfo = MP3(path, ID3=EasyID3)
                # print(audioInfo.pprint())
        else:
            self.saveMataDataToFile(metaData)
            # metaDataDict = self.getMetaDataDict(metaData)
            # path = f'{self.savePath}/{metaDataDict["title"]}.mp3'
            # audio = EasyID3(path)
            # for data in metaDataDict:
            #     audio[data] = metaDataDict[data]
            # audio.save()
            # audioInfo = MP3(path, ID3=EasyID3)
            # print(audioInfo.pprint())
    
    def saveMataDataToFile(self, metaData, albumName=None):
        # print(metaData)
        metaDataDict = self.getMetaDataDict(metaData)
        path = f'{self.savePath}/{metaDataDict["title"]}.mp3'
        audio = EasyID3(path)
        for data in metaDataDict:
            audio[data] = metaDataDict[data]
        audio['tracknumber'] = str(metaData['playlist_index'])
        if albumName != None:
            audio['album'] = albumName
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
    type = args.type
    config= args.config
    youtubeDL = YoutubeDL(config, type)
    if link == None:
        if type == "mp3":
            youtubeDL.downoladPlaylistAudio()
        else:
            youtubeDL.downoladPlaylistVideo()
    else:
        if type == "mp3":
            youtubeDL.downloadAudio(link)
        else:
            youtubeDL.dowloadVideo(link)

#mkv mają napisy różne i nawet różne funkcje audio
# można dodać track number z playlisy i album wtedy nazywa się playlista
# pobieranie całej playlisty, ogarnąć
# rozszerzenia się pobawić, zobaczyć w docsach info o ext, żeby dowiedzieć się w jakim formacie został pobrany plik
# poczytać flask bootstrap