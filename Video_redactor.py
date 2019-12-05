import sys

import moviepy.video.fx.all as vfx
from PyQt5 import QtWidgets
from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtWidgets import (QFileDialog, QStyle)
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMessageBox
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

from Video_player_design import Ui_Form


class MyWidget(QMainWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle('Video editor')

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.mediaPlayer.setVideoOutput(self.widget)
        self.widget.show()

        self.media_ended = False
        self.history_list = []
        self.history_index = 0

        self.horizontalSlider.sliderMoved.connect(self.set_slider_position)
        self.horizontalSlider.setRange(0, 0)

        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)

        self.OpenButton.clicked.connect(self.open_dialog)

        self.playButton.clicked.connect(self.play)
        self.update_icon()

        self.cutButton.clicked.connect(self.cut)

        self.mirror_xButton.clicked.connect(self.mirror_x)
        self.mirror_yButton.clicked.connect(self.mirror_y)

        self.speedButton.clicked.connect(self.change_speed)

        self.blackwhiteButton.clicked.connect(self.blackwhite_filter)

        self.undoButton.clicked.connect(self.undo)
        self.undoButton.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))

        self.redoButton.clicked.connect(self.redo)
        self.redoButton.setIcon(self.style().standardIcon(QStyle.SP_ArrowRight))

        self.undoButton.setEnabled(False)
        self.redoButton.setEnabled(False)

        self.saveButton.clicked.connect(self.save)

        self.enable_video_controls(False)

        self.cutStartTime.clear()
        self.cutEndTime.clear()

    def enable_video_controls(self, enable):
        self.playButton.setEnabled(enable)
        self.horizontalSlider.setEnabled(enable)
        self.cutButton.setEnabled(enable)
        self.cutStartTime.setEnabled(enable)
        self.cutEndTime.setEnabled(enable)
        self.mirror_xButton.setEnabled(enable)
        self.mirror_yButton.setEnabled(enable)
        self.speedButton.setEnabled(enable)
        self.speed_line.setEnabled(enable)
        self.blackwhiteButton.setEnabled(enable)
        self.saveButton.setEnabled(enable)

    def open_dialog(self):
        self.mediaPlayer.stop()
        self.media_path = QFileDialog.getOpenFileName(self, 'Выберете видео', '')[0]
        self.setWindowTitle(self.media_path)
        self.start_new_file()
        self.history_list = []

    def start_new_file(self):
        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(self.media_path)))
        self.mediaPlayer.pause()
        self.update_icon()
        self.enable_video_controls(True)

    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()
        self.update_icon()

    def update_icon(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def end_of_media(self):
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.media_ended = True

    def set_slider_position(self, position):
        if position == self.mediaPlayer.duration():
            self.end_of_media()

        if self.media_ended:
            self.update_icon()
            self.media_ended = False

        self.mediaPlayer.setPosition(position)

    def positionChanged(self, position):
        self.time()

        if position == self.mediaPlayer.duration() and self.mediaPlayer.duration() != 0:
            self.end_of_media()

        self.horizontalSlider.setValue(position)

    def durationChanged(self, duration):
        self.horizontalSlider.setRange(0, duration)

    def time(self):
        sec = self.mediaPlayer.position() // 1000
        min = int(sec) // 60
        min_str = '0' + str(min) if (min < 10) else str(min)
        sec = sec % 60
        sec_str = '0' + str(sec) if (sec < 10) else str(sec)
        self.timeLcd.display(min_str + ':' + sec_str)

    def cut(self):
        start = self.get_position(False, self.cutStartTime.text())
        end = self.get_position(True, self.cutEndTime.text())

        if (start < 0 or end < 0) or (start >= end) or end > self.mediaPlayer.duration() // 1000:
            self.time_error()
            return

        self.mediaPlayer.pause()
        self.update_icon()
        self.put_media_to_history()
        ffmpeg_extract_subclip(self.media_path, start, end, targetname=self.new_video_path())
        self.start_new_file()

    def get_position(self, is_end_position, text):
        if '' == text:
            if is_end_position:
                return self.mediaPlayer.duration() // 1000
            return 0

        if text.isdigit():
            sec = int(text)
            return sec

        if ':' not in text:
            return -1

        numbers = text.split(':')

        if len(numbers) > 2:
            return -1

        sec = 0
        for n in numbers:
            if not n.isdigit():
                return -1

            i = int(n)
            if i < 0 or i > 59:
                return -1

            sec = i + sec * 60

        return sec

    def mirror_x(self):
        self.mediaPlayer.pause()
        self.update_icon()
        clip = VideoFileClip(self.media_path)
        clip2 = clip.fx(vfx.mirror_x)
        self.put_media_to_history()
        clip2.write_videofile(self.new_video_path())
        self.start_new_file()

    def mirror_y(self):
        self.mediaPlayer.pause()
        self.update_icon()
        clip = VideoFileClip(self.media_path)
        clip2 = clip.fx(vfx.mirror_y)
        self.put_media_to_history()
        clip2.write_videofile(self.new_video_path())
        self.start_new_file()

    def time_error(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText('Please enter correct time format')
        msg.setWindowTitle("Error")
        msg.exec_()

    def change_speed(self):
        self.mediaPlayer.pause()
        self.update_icon()
        text = self.speed_line.text()
        speed_coef = float(text)
        clip = VideoFileClip(self.media_path)
        new_clip = clip.fx(vfx.speedx, speed_coef)
        self.put_media_to_history()
        new_clip.write_videofile(self.new_video_path())
        self.start_new_file()

    def blackwhite_filter(self):
        self.mediaPlayer.pause()
        self.update_icon()
        clip = VideoFileClip(self.media_path)
        new_clip = clip.fx(vfx.blackwhite)
        self.put_media_to_history()
        new_clip.write_videofile(self.new_video_path())
        self.start_new_file()

    def new_video_path(self):
        self.media_path = self.media_path.split('.')[0] + 'temp.' + self.media_path.split('.')[1]
        return self.media_path

    def undo(self):
        self.history_index -= 1

        self.media_path = self.history_list[self.history_index - 1]
        self.start_new_file()

        self.updade_state_undo_redo()

    def redo(self):
        self.history_index += 1

        self.media_path = self.history_list[self.history_index - 1]

        self.updade_state_undo_redo()
        self.start_new_file()

    def put_media_to_history(self):
        self.history_list.append(self.media_path)
        self.history_index = len(self.history_list)

        self.updade_state_undo_redo()

    def updade_state_undo_redo(self):
        self.undoButton.setEnabled(self.history_index >= 1)
        self.redoButton.setEnabled(self.history_index < len(self.history_list))
        self.saveButton.setEnabled(self.history_index >= 1)

    def save(self):
        save_path = QFileDialog.getSaveFileName(self, 'Сохраните видео', '')[0]
        clip = VideoFileClip(self.media_path)
        clip.write_videofile(save_path)
        clip.close()


app = QtWidgets.QApplication(sys.argv)
player = MyWidget()
player.show()
sys.exit(app.exec_())
