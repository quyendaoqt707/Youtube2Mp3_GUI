#from logging import setLoggerClass
from datetime import datetime
import logging
import os
#import subprocess
from pytube import YouTube
from pytube import Playlist
import eyed3
import sys
from requests import get
import time
from shutil import move
from moviepy.editor import AudioFileClip
from PIL import Image

#import singleDowloadEngine as downEngine
#from PyQt5 import QtWidgets, uic, QPixmap

#from PyQt5 import QtCore, QtGui, QtWidgets, uic
# -------------------------------------
from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class ThreadClass(QtCore.QThread):
    progressBar_signal=QtCore.pyqtSignal(int)
    statusBarMess_signal=QtCore.pyqtSignal(str)
    statusBarCSS_signal=QtCore.pyqtSignal(str)
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)


    oldProgress=0
    thumbName=""
    def setMp3Metadata(self, name: str):
        try:
            #audiofile = eyed3.load(os.path.join(self.fordelNameLine.text(),name))
            audiofile = eyed3.load(name)
            audiofile.initTag(version=(2, 3, 0))

            #audiofile.tag.artist = self.artistSongLine.text()
            #audiofile.tag.title = self.titleSongLine.text()
            #self.metadata_signal.emit()
            audiofile.tag.artist = Ui.metadata[0]
            audiofile.tag.title = Ui.metadata[1]
            audiofile.tag.comments.set("source:"+str(Ui.ytObj.watch_url))
            #thumbName=Ui.ytObj.title+'_thumb.png'
            with open(self.thumbName, "rb") as cover_art:
                audiofile.tag.images.set(
                    3, cover_art.read(), "image/png", u"cover")

            audiofile.tag.save()
        except Exception as log:
            logging.info("ERROR: setMp3Metadata\n"+log)

    def progress_func(self, stream, chunk, bytes_remaining):
        size = stream.filesize

        progress = (float(abs(bytes_remaining-size)/size))*float(100)

        if progress < 100:
            self.statusBarMess_signal.emit("Downloading...")
            while ThreadClass.oldProgress < progress:
                ThreadClass.oldProgress = ThreadClass.oldProgress+1
                time.sleep(0.01)
                print(ThreadClass.oldProgress)
                self.progressBar_signal.emit(ThreadClass.oldProgress)
        else:
            while ThreadClass.oldProgress < 101:
                ThreadClass.oldProgress = ThreadClass.oldProgress+1
                time.sleep(0.01)
                self.progressBar_signal.emit(ThreadClass.oldProgress)
            self.statusBarMess_signal.emit("Download complete! Converting...")


    def mp4_to_mp3(self, mp4, mp3):
        try:
            mp4_without_frames = AudioFileClip(mp4)     
            mp4_without_frames.write_audiofile(mp3)     
            mp4_without_frames.close() 
        except Exception as log:
            logging.info("EXCEPT at mp4_to_mp3:\n"+log)
        # function call mp4_to_mp3("my_mp4_path.mp4", "audio.mp3")


    def run(self):
        ytObj=Ui.ytObj
        
        self.thumbName="temp_thumb.jpg"
        ThreadClass.oldProgress=0
        self.progressBar_signal.emit(0)
        ytObj.register_on_progress_callback(self.progress_func)
        #Option1: Get hightest bitrate audio 160kbps:
        # streamObj=ytObj.streams.get_by_itag(251)
        # streamObj.download()

        #Option2: Get 128kbps:  uncomment 2 line below
        streamObj = ytObj.streams.filter(only_audio=True)
        streamObj.first().download()  # use default_file name


        self.statusBarMess_signal.emit("Download complete! Converting...")
        self.statusBarCSS_signal.emit("greenYellow")
        # for i in range(ThreadClass.oldProgress, 101):
        #     self.progressBar_signal.emit.(i)

        defaultFilename = streamObj.first().default_filename
        #defaultFilename = streamObj.default_filename #for option1
        outputName = defaultFilename[:-3]+"mp3"
        
        #print("----------Download complete! Converting...")

        self.mp4_to_mp3(defaultFilename,outputName)
        self.statusBarMess_signal.emit("Try to add metadata...")
        print("-------Try to add metadata...")

        self.setMp3Metadata(outputName)
        self.statusBarMess_signal.emit("Converted! Check output fordel")
        self.statusBarCSS_signal.emit("springGreen")
 
        os.remove("temp_thumb.jpg")
        os.remove(defaultFilename)  # delete mp4 file

        if os.getcwd() != str(Ui.destinationFordel):
            move(outputName, Ui.destinationFordel)
     #   self.getSingleInfo=False #reset




   

    
    def stop(self):
        print('Stoping thread...')
        self.terminate()

class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('youtube2mp3.ui', self)

        self.fordelNameLine.setText(os.getcwd())

        # Event add from here:
        self.clearButton.clicked.connect(self.linkClear)
        self.downloadButton.clicked.connect(self.downloader)
        self.getInfoButton.clicked.connect(self.getInfo)
        self.linkInputLine.textChanged.connect(lambda x : self.linkChanged(True))
        self.progressBar.setValue(0)
        self.statusBar().setStyleSheet("background-color : pink")
        self.statusBar().showMessage("Welcome!")
        # self.msg = QMessageBox()

        self.saveToDialog = QFileDialog()
        self.toolButton.clicked.connect(self.saveTo)
        self.videoModeBt.clicked.connect(self.setMode)
        self.playlistModeBt.clicked.connect(self.setMode)

        # self.titleLine.setAlignment(QtCore.Qt.AlignLeft)

        # self.thumbPreviewLabel = self.findChild(
        #    QtWidgets.QLabel, 'thumbPreviewLabel')
   

        self.show()

        # back-end function:

    mode = 0  # single video mode, mode=1: #playlist mode
    ytObj=None
    isLinkChanged=True

    metadata=[]
    destinationFordel=os.getcwd()
    thumbName=""
    def linkChanged(self, value):
        Ui.isLinkChanged=value

    def getMetadata(self):
        Ui.metadata.clear()
        Ui.metadata.append(self.artistSongLine.text())
        Ui.metadata.append(self.titleSongLine.text())

    def setMode(self):
        self.statusBar().setStyleSheet("background-color : pink")
        if self.videoModeBt.isChecked() == True:
            self.mode = 0  # video mode
            self.isVideoInfoObtained = False
            self.infoLabel.setText("Video Info")
            self.titleLabel.setText("Video title:")
            self.authorLabel.setText("Channel:")
            self.lengthLabel.setText("Length:")
            self.publishLabel.setText("Publish day:")
            self.statusBar().showMessage("------ Single Video MODE------")
        else:
            self.mode = 1  # playlist mode
            self.isPlInfoObtained = False
            self.infoLabel.setText("Playlist Info")
            #self.infoLabel.setStyleSheet("color: blue; background-color: yellow")
            self.titleLabel.setText("Playlist name:")
            self.authorLabel.setText("Playlist owner:")
            self.lengthLabel.setText("Num of video:")
            self.publishLabel.setText("Playlist ID:")
            self.statusBar().showMessage("------ Playlist MODE------")

    isVideoInfoObtained = False
    isPlInfoObtained = False
    #isGetThumb=False
    oldProgress = 0
    videoList = []

    def progressBar_func(self,i):
        self.progressBar.setValue(i)

    def setStatusBar(self,message):
        self.statusBar().showMessage(str(message))
    
    def setCSS(self, color):
        self.statusBar().setStyleSheet("background-color : "+str(color))

    def start_worker(self):
        self.mythread=ThreadClass(parent=None)
        self.mythread.start()
        self.mythread.progressBar_signal.connect(self.progressBar_func)
        self.mythread.statusBarMess_signal.connect(self.setStatusBar)
        self.mythread.statusBarCSS_signal.connect(self.setCSS)
    
    def stop_worker(self):
        self.mythread.stop()

    def saveTo(self):  # choose fordel to save file (file name is default)
        # self.saveToDialog.setFileMode(QFileDialog.Directory)
        # make the dialog appear adn return fordel name
        fordelName = self.saveToDialog.getExistingDirectory()
        # self.saveToDialog.exec_() # nếu dùng dòng trên thì khỏi dòng này
        self.fordelNameLine.setText(fordelName)
        Ui.destinationFordel=fordelName

 
    def getYtObj(self):
        # retval=1
        # while (retval!=0):
        link = str(self.linkInputLine.text())

        #         print(retval)
        #         self.msg.hideEvent()

       # return YouTube(link,on_progress_callback=self.progress_func)
        Ui.ytObj=YouTube(link)
        #print("YT url=",Ui.ytObj.title)

    def linkClear(self):
        self.linkInputLine.clear()
        self.artistSongLine.setReadOnly(False)
        self.titleSongLine.setReadOnly(False)
        if os.path.isfile("temp_thumb.jpg")==True:
            os.remove("temp_thumb.jpg")
        self.statusBar().showMessage("Cleaned!")
        self.statusBar().setStyleSheet("background-color : pink")
    def showMessage(self, mainText, info):
        self.msg = QMessageBox()
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setText(mainText)
        self.msg.setInformativeText(info)
        # self.msg.setText("LINK IS INVALID!!!")
        # self.msg.setInformativeText("""Check some info below:
        #     Link can not empty.
        #     Incorrect mode.
        #     Link not a video or playlist from Youtube.com""")
        self.msg.setWindowTitle(r"Oh! Something went wrong!")
        self.msg.setStandardButtons(QMessageBox.Ok)
        self.msg.setDefaultButton(QMessageBox.Ok)
            #self.msg.buttonClicked.connect(msgbtn)
        self.msg.exec_() #or msg.exec_()
        self.statusBar().showMessage("")
    def isValidLink(self, mode: int):

        link=str(self.linkInputLine.text())
        dk1= "www.youtube.com" in link
        dk2= "watch" in link
        dk3= "list" in link
        mainText="LINK IS INVALID!!!"
        info="""Check some info below:
             Link can not empty.
             Incorrect mode.
             Link not a video or playlist from Youtube.com
        """
        if mode==0:
            if dk1==dk2==True:
                return True
            else: 
                self.showMessage(mainText, info)
                return False
        else:
            if dk1==dk3==True:
                return True
            else: 
                self.showMessage(mainText, info)
                return False


    def getThumbnail(self, url: str):
        #thumbName=Ui.ytObj.title+'_thumb.png'
        #https://i.ytimg.com/vi/10ATKnZLg9c/maxresdefault.jpg
        #https://i.ytimg.com/vi/10ATKnZLg9c/sddefault.jpg
        url=url.replace("sddefault","maxresdefault")
        thumbName='temp_thumb.png'
        if os.path.isfile(thumbName[:-3]+"jpg")==False:
            responseObj = get(url)
            #print("status_code=",responseObj.status_code)
            if (responseObj.status_code>=400):
                # maxresdefault failed!
                url=url.replace("maxresdefault","sddefault")
                responseObj = get(url)
                if (responseObj.status_code>=400):
                    self.statusBar().showMessage("Oh! ... Can't get URL, check internet connection...")
                    return False
 
            with open(thumbName, "wb") as f:
                f.write(responseObj.content)

            img = Image.open(thumbName)
            w, h = img.size
            #Check if real-thumbnail is square or rectangle
            pix =img.load()
            lpixel=pix[0,h//2]
            rpixel=pix[w-1,(h//2)-1]
            #print(lpixel, rpixel)
            if lpixel[0]<15 and lpixel[1]<15 and lpixel[2]<15 :
                if rpixel[0]<15 and rpixel[1]<15 and rpixel[2]<15:
                    area = ((w-h)//2, 0, ((w-h)//2)+h, h)
                    #area = (320, 0, 960, 720)
                    cropped_img = img.crop(area)
                    #cropped_img.save("abcde.jpg",quality=50,optimize=True)
                    cropped_img.save(thumbName[:-3]+"jpg")
            else:
                resized_Img=img.resize((h,h))
                resized_Img.save(thumbName[:-3]+"jpg")
            os.remove(thumbName)
            return True
        else:
            self.statusBar().showMessage("Thumbnail already exists!")
            return True


    def getSingleInfo(self):
        self.progressBar.setValue(0)
        self.getYtObj()

        # bitrate=ytObj.streams.filter(only_audio=True).first().bitrate #return bit
        self.titleLine.setText(Ui.ytObj.title)
        self.viewLine.setText(str(Ui.ytObj.views))
        self.authorLine.setText(Ui.ytObj.author)
        self.bitrateSongLine.setText("160kbps (maximum)")
        #videoLen="{0} phút {1} giây" %(ytObj.length/60, ytObj.length%60)
        videoLen = str(Ui.ytObj.length//60)+' phút ' + \
            str(Ui.ytObj.length % 60)+' giây'
        self.lengthLine.setText(str(videoLen))
        self.publishLine.setText(str(Ui.ytObj.publish_date))

        
        isSuccess=self.getThumbnail(Ui.ytObj.thumbnail_url)
        if isSuccess==True:
            self.thumbPreviewLabel.setPixmap(QPixmap("temp_thumb.jpg"))
            # Set temp Metadata:
            title = Ui.ytObj.title

            if "-" in title:
                artist = title.split('-')
                if (" x " in artist[0]) | ("ft" in artist[0]):
                    songTitle = artist[1].strip()
                    artist = artist[0].strip()

                elif (" x " in artist[1]) | ("ft" in artist[0]):
                    songTitle = artist[0].strip()
                    artist = artist[1].strip()
                else:
                    songTitle = artist[0].strip()
                    artist = artist[1].strip()

            else:
                songTitle = title
                self.showMessage("Input Artist for song!", "")
                artist = "Place holder title!"

            self.artistSongLine.setText(artist)  # chuẩn hoá
            self.titleSongLine.setText(songTitle)
            Ui.isVideoInfoObtained=True
            # get all bitrate:
            #streamObj = ytObj.streams.filter(only_audio=True)
            # streamObj.get_audio_only().
        else:
            self.showMessage("Get thumbnai failed!","Check internet connection!")

    def getPlaylistInfo(self):
        playlistLink = str(self.linkInputLine.text())

        playLObj = Playlist(playlistLink)
        self.videoList = list(playLObj.videos)
        self.titleLine.setText(playLObj.title)
        self.viewLine.setText(str(playLObj.views))
        self.authorLine.setText(playLObj.owner)
        self.lengthLine.setText(str(playLObj.length))
            # self.publishLine.setText(str(playLObj.last_updated.month))\
        self.publishLine.setText(playLObj.playlist_id)

    def getInfo(self):
        self.statusBar().setStyleSheet("background-color : pink")
        self.statusBar().showMessage("")
        if Ui.isLinkChanged==True:
            self.artistSongLine.setReadOnly(False)
            self.titleSongLine.setReadOnly(False)
            if self.mode == 0:
                if self.isValidLink(0)==True:
                    if Ui.isVideoInfoObtained==False:
                        self.getSingleInfo()
                    self.statusBar().showMessage("Video info has been obtained!")
                #Ui.isVideoInfoObtained=False
            else:
                if self.isValidLink(1)==True:
                    if Ui.isPlInfoObtained==False:
                        self.getPlaylistInfo()
                    self.statusBar().showMessage("Playlist info has been obtained!")
                #Ui.isPlInfoObtained=False
            Ui.isLinkChanged=False
        else:
            self.statusBar().showMessage("Please change link address!")

  
    def singleDownload(self):
        self.getMetadata()
        self.artistSongLine.setReadOnly(True)
        self.titleSongLine.setReadOnly(True)
        self.start_worker()

    # def singleDownload(self, ytObj: YouTube):
    #     self.progressBar.setValue(0)
    #     self.oldProgress = 0
    #     #ytObj = self.getYtObj()
    #     ytObj.register_on_progress_callback(self.progress_func)
    #     streamObj = ytObj.streams.filter(only_audio=True)
    #     #does download method will make GUI not responding?  Yes, tested!
    #     streamObj.first().download()  # use default_file name

    #     for i in range(self.oldProgress, 101):
    #         self.progressBar.setValue(i)

    #     defaultFilename = streamObj.first().default_filename
    #     outputName = defaultFilename[:-3]+"mp3"

    #     # 	ffmpeg -i input.mp4 output.mp3
    #     #subprocess.run(["ffmpeg", "-i", defaultFilename, os.path.join(self.fordelNameLine.text(),outputName)])
    #     #p1=subprocess.run(["ffmpeg", "-i", defaultFilename, outputName])

    #     self.statusBar().showMessage("Download complete! Converting...")
    #     print("----------Download complete! Converting...")

    #     #p1=subprocess.Popen(["ffmpeg","-loglevel", "panic", "-i", defaultFilename, outputName],start_new_session=True)
    #     # p1.wait() #make progress 1 wait

    #     #cmdStr="ffmpeg -loglevel panic -i {} {}".format(defaultFilename,outputName)
    #     #cmdStr = 'ffmpeg -loglevel panic -i "{}" "{}"'.format(defaultFilename, outputName)
    #     # return code=0 mean exit normal, otherwise return 1
    #     #returnCode = os.system(cmdStr)

    #     #self.mp4_to_mp3(defaultFilename,outputName)

    #     self.getThumbnail(ytObj.thumbnail_url)
    #     # Set Metadata:
    #     self.statusBar().showMessage("Try to add metadata...")
    #     print("-------Try to add metadata...")

    #     # while p1.poll() is None:
    #     #     print('----------Still converting...')
    #     #     time.sleep(0.5)

    #     # found = False
    #     # while found == False:
    #     #     time.sleep(0.5)
    #     #     print("Finding...")
    #     #     if os.path.isfile(outputName):
    #     #         fSize = os.path.getsize(outputName)
    #     #         if fSize:
    #     #             print("File size=", (fSize//1024)//1024, "Mb")
    #     #             found = True

    #     # while True:
    #     #     time.sleep(0.5)
    #     #     if os.path.isfile(outputName):
    #     #         if os.path.getsize(outputName)>1024:
    #     #             self.setMp3Metadata(outputName)
    #     #             print("\n--------Found\n")
    #     #             break

    #     #time.sleep(10)  
    #     #print("------------Time out--------")

    #     self.setMp3Metadata(outputName)
    #     self.statusBar().showMessage("Converted! Check output fordel")
    #     self.statusBar().setStyleSheet("background-color : green")
    #     os.remove("temp_thumbnail.png")
    #     os.remove(defaultFilename)  # delete mp4 file

    #     if os.getcwd() != str(self.fordelNameLine.text()):
    #         move(outputName, self.fordelNameLine.text())
    #     self.getSingleInfo=False #reset

    def batchDownload(self):
        for ytObj in self.videoList:
            # print(ytObj.title)
            self.statusBar().showMessage("'"+ytObj.title+r"' is downloading...")
            Ui.ytObj=ytObj
            self.getThumbnail(ytObj.thumbnail_url)
            self.singleDownload()
            #time.sleep(0.5)
            #self.refresh()

    def downloader(self):
        self.statusBar().showMessage("-----Wait a second....")
        if self.mode == 0:  # single video
            if self.isValidLink(0)==True:
                if self.isVideoInfoObtained == False:
                    self.getSingleInfo()
                    self.isVideoInfoObtained = True
                    self.getYtObj()
                self.singleDownload()
            Ui.isVideoInfoObtained=False
        else:  # mode=1 playlist
            if self.isValidLink(1)==True:
                if self.isPlInfoObtained == False:
                    self.getPlaylistInfo()
                    self.isPlInfoObtained = True
                self.batchDownload()

            Ui.isPlInfoObtained=False

def closeEvent():  #user define function
    if os.path.isfile("temp_thumb.jpg")==True:
        os.remove("temp_thumb.jpg")
    #print("Close button pressed!")
    sys.exit(0)


if __name__ == "__main__":
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(
            QtCore.Qt.AA_EnableHighDpiScaling, True)

    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(
            QtCore.Qt.AA_UseHighDpiPixmaps, True)
    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(closeEvent)
    window = Ui()
    # app.setStyle("fusion")
            #Set logging mode:
    # if Ui.issaveLog==True:
    # current_time = datetime.now().strftime("%H-%M-%S")
    # #print(current_time)
    # logFileName="Log\\"+current_time+"_session.log"
    # logging.basicConfig(filename=logFileName,format='%(asctime)s - %(message)s', level=logging.INFO,encoding='utf-8')
    app.exec_()
