import yt_dlp
import configparser
import argparse
import sys
from enum import Enum, auto
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

class MetaDataType(Enum):
    TITLE = 'title'
    ALBUM = 'album'
    ARTIST = 'artist'
    PLAYLIST_INDEX = 'playlist_index'

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
        """Method used to download youtube media based on URL

        Args:
            youtubeURL (str): YouTube URL
            youtubeOptions (dict): YouTube options dict form init

        Returns:
            class: meta data form youtube
        """
        with yt_dlp.YoutubeDL(youtubeOptions) as ydl:
            return ydl.extract_info(youtubeURL)

    def dowloadVideo(self, youtubeURL:str):
        """Method uded to download video type from YouTube

        Args:
            youtubeURL (str): YouTube URL
        """
        self.downloadFile(youtubeURL, self.ydl_video_opts)

    def downloadAudio(self, youtubeURL:str, isPlaylist=False):
        """Method uded to download audio type from Youtube, convert metadata 
        into mp3 format used mutagen.easyid3

        Args:
            youtubeURL (str): YouTube URL
        """
        metaData = self.downloadFile(youtubeURL, self.ydl_audio_opts)
        if isPlaylist:
            self.setMetaDataPlaylist(metaData)
        else:
            self.setMetaDataSingleFile(metaData)

    def downoladConfigPlaylistVideo(self):
        """Method used to dowload all playlists added to cofig file - type video
        """
        for playlistURL in self.playlistList:
            playlistHash = playlistURL[playlistURL.index("=") + 1:]
            self.downloadFile(playlistHash, self.ydl_video_opts)

    def downoladConfigPlaylistAudio(self):
        """Method used to dowload all playlists added to cofig file - type audio
        """
        for playlistURL in self.playlistList:
            playlistHash = playlistURL[playlistURL.index("=") + 1:]
            metaData = self.downloadFile(playlistHash, self.ydl_audio_opts)
            self.setMetaDataPlaylist(metaData)

    def setMetaDataSingleFile(self, metaData):
        """Method used to set meta data for the single file

        Args:
            metaData (class): Metadata
        """
        metaDataDict = self.getMetaDataDict(metaData)
        path = f'{self.savePath}/{metaDataDict["title"]}.mp3'
        self.saveMetaData(metaDataDict, path)
        self.showMetaDataInfo(path)

    
    def setMetaDataPlaylist(self, metaData):
        """Method used to set Metadata for playlist

        Args:
            metaData (class): Metadata
        """
        playlistName = metaData["title"]
        for trackMetaData in metaData['entries']:
            metaDataDict = self.getMetaDataDict(trackMetaData)
            path = f'{self.savePath}/{metaDataDict["title"]}.mp3'
            self.saveMetaData(metaDataDict, path)
            audio = EasyID3(path)
            audio['album'] = playlistName
            audio.save()
            self.showMetaDataInfo(path)

    def saveMetaData(self, metaDataDict, path):
        """Method used to set Metadata

        Args:
            metaDataDict (dict): Metadata dict  
            path (str): file path
        """
        audio = EasyID3(path)
        for data in metaDataDict:
            if data == "playlist_index":
                audio['tracknumber'] = str(metaDataDict[data])
                continue
            audio[data] = metaDataDict[data]
        audio.save()
    
    def showMetaDataInfo(self, path):
        """Method used to show Metadata info

        Args:
            path (str): file path
        """
        audioInfo = MP3(path, ID3=EasyID3)
        print(audioInfo.pprint())

    def getMetaDataDict(self, metaData):
        """Method returns metadata dict based on metadata taken form Youtube video

        Args:
            metaData (dict): Metadata dict

        Returns:
            dict: Metadata dict from YouTube
        """
        metaDataDict = {}
        for data in MetaDataType:
            if data.value in metaData:
                metaDataDict[data.value] = metaData[data.value]
        return metaDataDict
    
class ExaminateURL(YoutubeDL):
    def __init__(self,config, type, videoHash, playlistHash):
        super().__init__(config, type)
        self.videoHash = videoHash
        self.playlistHash = playlistHash
    
    def ifLinkIsNoneDowloadConfigPlaylist(self, type):
        if type == "mp3":
            self.downoladConfigPlaylistAudio()
        else:
            self.downoladConfigPlaylistVideo()

    def ifLinkIsNotPlaylistDowloadSingleFile(self, type):
        if type == "mp3":
            self.downloadAudio(self.videoHash)
        else:
            self.dowloadVideo(self.videoHash)

    def ifLinkIsPlaylistDowloadIt(self, type):
        isAudio = False
        isPlaylist = False
        if type == "mp3":
            isAudio = True
        userResponse = input("""
        Playlist link detected. 
        If you want to download whole playlist press 'y'
        If you want to download single video/audio press 'n'
        """)
        if userResponse == "n":
            hashToDownload = self.videoHash
        elif userResponse == "y":
            hashToDownload = self.playlistHash
            isPlaylist = True
        else:
            raise ValueError("Please enter 'y' for yes or 'n' for no")
        if isAudio:
            if isPlaylist:
                self.downloadAudio(hashToDownload, isPlaylist)
            else:
                self.downloadAudio(hashToDownload)
        else:
            self.dowloadVideo(hashToDownload)

    @classmethod
    def initFromLink(cls, config, type, link):
        if link == None:
            return cls(config, type, videoHash=None, playlistHash=None)
        onlyHashesInLink = link.split("?")[1]
        numberOfEqualSign = link.count("=")
        if numberOfEqualSign >= 2:
            splitedHashes = onlyHashesInLink.split("=")
            videoHash = splitedHashes[1][:splitedHashes[1].index("&")]
            playlistHash = splitedHashes[2][:splitedHashes[2].index("&")]
            return cls(config, type, videoHash=videoHash, playlistHash=playlistHash)
        elif numberOfEqualSign == 1:
            if "list=" in onlyHashesInLink:
                playlistHash = onlyHashesInLink[5:]
                return cls(config, type, videoHash=None, playlistHash=playlistHash)
            else:
                videoHash = onlyHashesInLink[2:]
                return cls(config, type, videoHash=videoHash, playlistHash=None)
     

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
    # youtubeDL = YoutubeDL(config, type)
    # terminalUser = ExaminateURL.initFromLink(youtubeDL, link)
    terminalUser = ExaminateURL.initFromLink(config, type, link)

    if link == None:
        terminalUser.ifLinkIsNoneDowloadConfigPlaylist(type)
    elif "list=" not in link:
        terminalUser.ifLinkIsNotPlaylistDowloadSingleFile(type)
    elif "list=" in link:
        terminalUser.ifLinkIsPlaylistDowloadIt(type)

# https://www.youtube.com/watch?v=_EZUfnMv3Lg&list=PLAz00b-z3I5Um0R1_XqkbiqqkB0526jxO&index=2
# https://www.youtube.com/watch?v=_EZUfnMv3Lg
# https://www.youtube.com/playlist?list=PLAz00b-z3I5Um0R1_XqkbiqqkB0526jxO

# sprawdzić ile jest znaków równa się żeby nie rozdrabniać się na długie if statemanty
# najpierw splitować zapytania znaki, potem & a potem równa się a 
# zamiast while to wywalić błąd DONE
# trucknumber dodać do Enum i weryfikować w loopie DONE
# dodać kolejną metode w której ustawiam metadaa setmetadataForPlaylist i setMetaDataForSingleFile DONE

# DODAŁEM DZIDZICZENIE W EXAMINEURL


