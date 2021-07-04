from logging import setLoggerClass
import os
import subprocess
from pytube import YouTube
from pytube import Playlist
import eyed3
import sys
from requests import get
import time
from shutil import move

#from PyQt5 import QtWidgets, uic, QPixmap

#from PyQt5 import QtCore, QtGui, QtWidgets, uic
# -------------------------------------
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import requests


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('youtube2mp3.ui', self)

        self.fordelNameLine.setText(os.getcwd())

        # Event add from here:
        self.clearButton.clicked.connect(self.linkClear)
        self.downloadButton.clicked.connect(self.downloader)
        self.getInfoButton.clicked.connect(self.getInfo)
        self.progressBar.setValue(0)
        self.statusBar().setStyleSheet("background-color : pink")
        self.msg = QMessageBox()

        self.saveToDialog= QFileDialog()
        self.toolButton.clicked.connect(self.saveTo)
        self.videoModeBt.clicked.connect(self.setMode)
        self.playlistModeBt.clicked.connect(self.setMode)

        # ----------------------Test segment---------------------
        # self.thumbPreviewLabel = self.findChild(
        #    QtWidgets.QLabel, 'thumbPreviewLabel')
        # self.thumbPreviewLabel.setText("abc") #it's work!
        # self.thumbPreviewLabel.setPixmap(QPixmap("python.png")) #it's work!
        # QImage image()
        # self.thumbPreviewLabel.setPicture(QPicture("python.png")
        # self.insertLinkLabel.setText("avd")  #it's work!
        # ----------------------Test segment---------------------

        self.show()

        # call-back funtion from here:
        # back-end function:

    mode=0 # single video mode, mode=1: #playlist mode
    def setMode(self):
        if self.videoModeBt.isChecked()==True:
            self.mode=0 #video mode
            self.isVideoInfoObtained=False
            self.infoLabel.setText("Video Info")
            self.titleLabel.setText("Video title:")
            self.authorLabel.setText("Channel:")
            self.lengthLabel.setText("Length:")
            self.publishLabel.setText("Publish day:")
            self.statusBar().showMessage("------ Single Video MODE------")
        else:
            self.mode=1 #playlist mode
            self.isPlInfoObtained=False
            self.infoLabel.setText("Playlist Info")
            #self.infoLabel.setStyleSheet("color: blue; background-color: yellow")
            self.titleLabel.setText("Playlist name:")
            self.authorLabel.setText("Playlist owner:")
            self.lengthLabel.setText("Num of video:")
            self.publishLabel.setText("Playlist ID:")
            self.statusBar().showMessage("------ Playlist MODE------")


    isVideoInfoObtained = False
    isPlInfoObtained=False
    oldProgress=0
    videoList=[]
    def saveTo(self): #choose fordel to save file (file name is default)
        #self.saveToDialog.setFileMode(QFileDialog.Directory)
        fordelName=self.saveToDialog.getExistingDirectory() # make the dialog appear adn return fordel name
        #self.saveToDialog.exec_() # nếu dùng dòng trên thì khỏi dòng này
        self.fordelNameLine.setText(fordelName)

    def progress_func(self, stream, chunk, bytes_remaining):
        size = stream.filesize
        
        progress = (float(abs(bytes_remaining-size)/size))*float(100)
        
        if progress<100:
            self.statusBar().showMessage("Downloading...")
            while self.oldProgress < progress:
                self.oldProgress = self.oldProgress+1
                time.sleep(0.01)
                print(self.oldProgress)
                self.progressBar.setValue(self.oldProgress)
        else:
            while self.oldProgress < 101:
                self.oldProgress = self.oldProgress+1
                time.sleep(0.01)
                self.progressBar.setValue(self.oldProgress)
            self.statusBar().showMessage("Download complete! Converting...")
    
    def getYtObj(self):
        # retval=1
        # while (retval!=0):
        link = str(self.linkInputLine.text())
        #     print('--'+link+'--')
        #     if "www.youtube.com" not in link:
        #         self.msg.setIcon(QMessageBox.Information)
        
        #         self.msg.setText("Link is invalid!")
        #         self.msg.setInformativeText("Link can not empty\nLink not a video or playlist from Youtube.com")
        #         self.msg.setWindowTitle(r"Oh! Something went wrong!")
        #         self.msg.setStandardButtons(QMessageBox.Ok)
        #         #self.msg.buttonClicked.connect(msgbtn)
        #         retval = self.msg.exec_()
        #         print(retval)
        #         self.msg.hideEvent()


       # return YouTube(link,on_progress_callback=self.progress_func)
        return YouTube(link)

    def linkClear(self):
        self.linkInputLine.clear()
        self.statusBar().showMessage("Cleaned!")
    
    def isValidLink(self,link:str):
        #if mode==0, =1
        return True
    
    def getThumbnail(self,url:str):
        responseObj = get(url)
        # thumbName=ytObj.title+'_thumb.png'
        with open("temp_thumbnail.png", "wb") as f:
            f.write(responseObj.content)

    def getSingleInfo(self):
        self.progressBar.setValue(0)
        ytObj = self.getYtObj()
        
        #bitrate=ytObj.streams.filter(only_audio=True).first().bitrate #return bit
        self.titleLine.setText(ytObj.title)
        self.viewLine.setText(str(ytObj.views))
        self.authorLine.setText(ytObj.author)
        self.bitrateSongLine.setText("128kbps")
        #videoLen="{0} phút {1} giây" %(ytObj.length/60, ytObj.length%60)
        videoLen = str(ytObj.length//60)+' phút ' + \
            str(ytObj.length % 60)+' giây'
        self.lengthLine.setText(str(videoLen))
        self.publishLine.setText(str(ytObj.publish_date))

        self.getThumbnail(ytObj.thumbnail_url)

        self.thumbPreviewLabel.setPixmap(QPixmap("temp_thumbnail.png"))

        # Set temp Metadata:
        title = ytObj.title
        

        if "-" in title:
            artist = title.split('-')
            if (" x " in artist[0]) | ("ft" in artist[0]):
                songTitle=artist[1].strip()
                artist=artist[0].strip()
                
            elif (" x " in artist[1]) | ("ft" in artist[0]):
                songTitle=artist[0].strip()
                artist=artist[1].strip()
            else:
                songTitle=artist[0].strip()
                artist=artist[1].strip()
                
        else:
            artist = "Place holder title!"
        
        self.artistSongLine.setText(artist)  # chuẩn hoá
        self.titleSongLine.setText(songTitle)
        # get all bitrate:
        #streamObj = ytObj.streams.filter(only_audio=True)
        # streamObj.get_audio_only().
    
    def getPlaylistInfo(self):
        playlistLink=str(self.linkInputLine.text())
        isValid=self.isValidLink(playlistLink)
        if (isValid==True):
            playLObj=Playlist(playlistLink)
            self.videoList=list(playLObj.videos)
            self.titleLine.setText(playLObj.title)
            self.viewLine.setText(str(playLObj.views))
            self.authorLine.setText(playLObj.owner)
            self.lengthLine.setText(str(playLObj.length))
            #self.publishLine.setText(str(playLObj.last_updated.month))\
            self.publishLine.setText(playLObj.playlist_id)

    
    def getInfo(self):
        if self.mode==0:
            self.getSingleInfo()
        else:
            self.getPlaylistInfo()

        self.statusBar().showMessage("Info has been obtained!")

    def setMp3Metadata(self, name: str):
        #audiofile = eyed3.load(os.path.join(self.fordelNameLine.text(),name))
        audiofile = eyed3.load(name)
        audiofile.initTag(version=(2, 3, 0))

        audiofile.tag.artist = self.artistSongLine.text()
        audiofile.tag.title = self.titleSongLine.text()

        with open("temp_thumbnail.png", "rb") as cover_art:
            audiofile.tag.images.set(
                3, cover_art.read(), "image/png", u"cover")

        audiofile.tag.save()
   
    def singleDownload(self,ytObj: YouTube):
        self.progressBar.setValue(0)
        #ytObj = self.getYtObj()
        ytObj.register_on_progress_callback(self.progress_func)
        streamObj = ytObj.streams.filter(only_audio=True)
        streamObj.first().download()  # use default_file name
        defaultFilename = streamObj.first().default_filename
        outputName = defaultFilename[:-3]+"mp3"

        # 	ffmpeg -i input.mp4 output.mp3
        #subprocess.run(["ffmpeg", "-i", defaultFilename, os.path.join(self.fordelNameLine.text(),outputName)])
        #p1=subprocess.run(["ffmpeg", "-i", defaultFilename, outputName])
        p1=subprocess.Popen(["ffmpeg", "-i", defaultFilename, outputName])
        p1.wait() #make progress 1 wait

        # streamObj.first().bitrate
        self.getThumbnail(ytObj.thumbnail_url)
        # Set Metadata:
        self.setMp3Metadata(outputName)
        self.statusBar().showMessage("Converted! Check output fordel")
        os.remove("temp_thumbnail.png")
        os.remove(defaultFilename)  # delete mp4 file

        if os.getcwd()!=str(self.fordelNameLine.text()): 
            move(outputName,self.fordelNameLine.text())

    def batchDownload(self):
        for ytObj in self.videoList:
            #print(ytObj.title)
            self.statusBar().showMessage("'"+ytObj.title+r"' is downloading...")
            self.singleDownload(ytObj)
            time.sleep(0.5)

    def downloader(self):
        #self.getInfo()
        if self.mode==0: #single video
            if self.isVideoInfoObtained==False:
                self.getSingleInfo()
                self.isVideoInfoObtained=True
            ytObj=self.getYtObj()
            self.singleDownload(ytObj)
        else : #mode=1 playlist
            if self.isPlInfoObtained==False:
                self.getPlaylistInfo()
                self.isPlInfoObtained=True
            self.batchDownload()


if __name__ == "__main__":
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(
            QtCore.Qt.AA_EnableHighDpiScaling, True)

    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(
            QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    # app.setStyle("fusion")
    app.exec_()
