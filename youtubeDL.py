import yt_dlp
import configparser
import argparse
import sys
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
        self.setMetaData(metaData, isPlaylist)

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
            self.setMetaData(metaData, True)
    
    def setMetaData(self, metaData, isPlaylist):
        """Method uded to set metadata and convert it into mp3 format

        Args:
            metaData (dict): Metadata form YouTube
            isPlaylist (bool, optional): Boolien True if YouTube is a playlist. Defaults to False.
        """
        if isPlaylist:
            playlistName = metaData["title"]
            for trackMetaData in metaData['entries']:
                self.saveMataDataToFile(trackMetaData, playlistName)
        else:
            self.saveMataDataToFile(metaData)
    
    def saveMataDataToFile(self, metaData, playlistName=None):
        """Method used to save metadata into mp3 audio format file

        Args:
            metaData (dict): Metadata from YouTube
            playlistName (str, optional): Name of the playlist. Defaults to None.
        """
        # print(metaData)
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
        """Method returns metadata dict based on metadata taken form Youtube video

        Args:
            metaData (dict): Metadata

        Returns:
            dict: Metadata dict from YouTube
        """
        metaDataDict = {}
        for data in MetaDataType:
            if data.value in metaData:
                metaDataDict[data.value] = metaData[data.value]
        return metaDataDict
    
class TerminalUsage():
    def __init__(self, youtubeDL, videoHash, playlistHash):
        self.youtubeDL = youtubeDL
        self.videoHash = videoHash
        self.playlistHash = playlistHash
    
    def ifLinkIsNoneDowloadConfigPlaylist(self, type):
        if type == "mp3":
            self.youtubeDL.downoladConfigPlaylistAudio()
        else:
            self.youtubeDL.downoladConfigPlaylistVideo()

    def ifLinkIsNotPlaylistDowloadSingleFile(self, type):
        if type == "mp3":
            self.youtubeDL.downloadAudio(self.videoHash)
        else:
            self.youtubeDL.dowloadVideo(self.videoHash)

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
        
        # if userResponse != "y" or userResponse != "n":
        if userResponse not in ["y", "n"]:
            raise ValueError("Please enter 'y' for yes or 'n' for no")
        if userResponse == "n":
            hashToDownload = self.videoHash
        else:
            hashToDownload = self.playlistHash
            isPlaylist = True
        if isAudio:
            if isPlaylist:
                youtubeDL.downloadAudio(hashToDownload, isPlaylist)
            else:
                youtubeDL.downloadAudio(hashToDownload)
        else:
            youtubeDL.dowloadVideo(hashToDownload)

    @classmethod
    def initFromLink(cls, youtubeDL, link):
        if link == None:
            return cls(youtubeDL, videoHash=None, playlistHash=None)
        onlyHashesInLink = link.split("?")[1]
        if "&" not in onlyHashesInLink:
            if "list=" in onlyHashesInLink:
                playlistHash = onlyHashesInLink[5:]
                return cls(youtubeDL, videoHash=None, playlistHash=playlistHash)
            else:
                videoHash = onlyHashesInLink[2:]
                return cls(youtubeDL, videoHash=videoHash, playlistHash=None)
        else:
            splitedHashes = onlyHashesInLink.split("=")
            videoHash = splitedHashes[1][:splitedHashes[1].index("&")]
            playlistHash = splitedHashes[2][:splitedHashes[2].index("&")]
            return cls(youtubeDL, videoHash=videoHash, playlistHash=playlistHash)

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
    terminalUser = TerminalUsage.initFromLink(youtubeDL, link)
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
# zamiast while to wywalić błąd 
# trucknumber dodać do Enum i weryfikować w loopie
# dodać kolejną metode w której ustawiam metadaa setmetadataForPlaylist i setMetaDataForSingleFile



# może być tak że kilka stron może mieć to samo IP ale musi mieć wtedy różny port, IP + port musi być unikatowy, IP odności się do urządzenia a na jednym urządzniu możę być więcej serwerów o róznych portach