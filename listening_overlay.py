"""Native port of the supplied Wave canvas and its original motion frames."""
import json
from pathlib import Path
import re
import time
import numpy as np
from PySide6.QtCore import QPoint, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QImage, QMovie, QPainter, QPainterPath, QPen, QRegion, QTransform
from PySide6.QtWidgets import QApplication, QWidget, QMenu
from mascot import Mascot, clamp_position
from desktop_windows import foreground

ASSETS=Path(__file__).resolve().parent/'assets'/'wave'
REFERENCE=json.loads((ASSETS/'motion.json').read_text(encoding='utf8'))


def motion_frame(seconds):
    position=(seconds*30)%len(REFERENCE['motion']); index=int(position); blend=position-index
    current=REFERENCE['motion'][index]; following=REFERENCE['motion'][(index+1)%len(REFERENCE['motion'])]
    return [a+(b-a)*blend for a,b in zip(current,following)]


def cross_path():
    tokens=re.findall(r'[MCL]|[-+]?\d*\.?\d+',REFERENCE['path']); path=QPainterPath(); i=0
    while i<len(tokens):
        command=tokens[i]; i+=1; count=6 if command=='C' else 2
        values=[float(value) for value in tokens[i:i+count]]; i+=count
        if command=='M': path.moveTo(*values)
        elif command=='L': path.lineTo(*values)
        elif command=='C': path.cubicTo(*values)
        else: raise ValueError('Comando de desenho Wave inválido.')
    path.closeSubpath(); return path


class ListeningOverlay(QWidget):
    position_changed=Signal(int,int)
    hide_requested=Signal()
    settings_requested=Signal()
    dictation_requested=Signal(object)

    def __init__(self):
        super().__init__(None,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|
                         Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAccessibleName('Personagem Claus')
        self.setWindowTitle('Claus — Personagem')
        self.mode='waiting'; self.wake_phrase='ok escuta'
        self.mascot_percent=100; self.wave_percent=100; self.wave_height=97; self.transparent_wave=False
        self.wave_screen=None
        self.amplitude=0; self.target_level=0; self.epoch=time.monotonic(); self.shape=cross_path()
        self.background=None; self.transparent_background=None; self.setFixedSize(128,120)
        self.mascot=Mascot(self.epoch); self.mascot_position=None
        self.mascot_hidden=False; self.pressed=False; self.dragging=False; self.click_target=0
        self.setMouseTracking(True)
        self.dance_mask=False
        self.setCursor(Qt.CursorShape.OpenHandCursor); self.apply_mascot_mask()
        self.movie=QMovie(str(ASSETS/'background.gif')); self.movie.setCacheMode(QMovie.CacheMode.CacheNone)
        self.movie.setScaledSize(QSize(480,120)); self.movie.frameChanged.connect(self.read_background)
        self.animation=QTimer(self); self.animation.timeout.connect(self.animate); self.animation.start(33)

    def read_background(self,frame):
        image=self.movie.currentImage().convertToFormat(QImage.Format.Format_ARGB32)
        if image.isNull(): return
        image.invertPixels(); self.background=image
        self.transparent_background=image.copy()
        pixels=np.ndarray((image.height(),image.width(),4),dtype=np.uint8,
                          buffer=self.transparent_background.bits(),strides=(image.bytesPerLine(),4,1))
        # Keep the geometric light trails; only their black pixels become transparent.
        pixels[:,:,3]=pixels[:,:,:3].max(axis=2); pixels[:,:,:3]=255
        self.update()

    def animate(self):
        self.amplitude+=(self.target_level-self.amplitude)*0.22
        if not self.isVisible(): return
        if self.mode=='waiting':
            self.mascot.update(time.monotonic())
            if (self.mascot.dance_mix>0.01)!=self.dance_mask: self.apply_mascot_mask()
        self.update()

    def apply_mascot_mask(self):
        self.dance_mask=self.mascot.dance_mix>0.01
        transform=QTransform(); transform.translate(self.width()/2,self.height()/2)
        margin=0.24 if self.dance_mask else 0.214
        transform.scale(margin*self.width()/128,margin*self.height()/120)
        self.setMask(QRegion(transform.map(self.mascot.body).toFillPolygon().toPolygon()))

    def configure(self,mascot_percent,wave_percent,wave_height,transparent_wave):
        self.mascot_percent=max(50,min(250,int(mascot_percent)))
        self.wave_percent=max(50,min(200,int(wave_percent)))
        self.wave_height=max(0,min(100,int(wave_height))); self.transparent_wave=bool(transparent_wave)
        if self.mascot_position is not None: self.restore_position(*self.mascot_position)
        if self.isVisible(): self.display('',mode=self.mode)

    def mascot_size(self):
        return (round(128*self.mascot_percent/100),round(120*self.mascot_percent/100))

    def bounded_position(self,point,screen=None):
        screen=screen or QApplication.screenAt(QPoint(*point)) or QApplication.primaryScreen()
        area=screen.availableGeometry()
        return clamp_position(point,(area.x(),area.y(),area.x()+area.width(),area.y()+area.height()),self.mascot_size())

    def restore_position(self,x,y):
        self.mascot_position=self.bounded_position((x,y))

    def set_mascot_hidden(self,hidden):
        self.mascot_hidden=hidden
        if self.mode=='waiting':
            if hidden: self.hide()
            else: self.display('',mode='waiting')

    def mousePressEvent(self,event):
        if self.mode=='waiting' and event.button()==Qt.MouseButton.LeftButton:
            self.mascot.interact(time.monotonic())
            self.pressed=True; self.dragging=False
            self.press_global=event.globalPosition().toPoint(); self.press_offset=event.position().toPoint()
            self.click_target=foreground(); self.grabMouse(); event.accept()
        else: super().mousePressEvent(event)

    def mouseMoveEvent(self,event):
        if not self.pressed:
            if self.mode=='waiting':
                point=event.position(); self.mascot.pet_motion(point.x()*128/self.width(),point.y()*120/self.height(),time.monotonic())
            return
        cursor=event.globalPosition().toPoint()
        if not self.dragging and (cursor-self.press_global).manhattanLength()>=QApplication.startDragDistance():
            self.dragging=True; self.mascot.set_dragging(True,time.monotonic())
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if self.dragging:
            point=cursor-self.press_offset
            position=self.bounded_position((point.x(),point.y()),QApplication.screenAt(cursor))
            scale=self.width()/128
            self.mascot.drag_motion((position[0]-self.x())/scale,(position[1]-self.y())/scale,time.monotonic())
            self.mascot_position=position
            self.move(*self.mascot_position); self.update()
        event.accept()

    def leaveEvent(self,event):
        self.mascot.end_pet(time.monotonic()); super().leaveEvent(event)

    def finish_drag(self):
        was_dragging=self.dragging
        if self.pressed: self.releaseMouse()
        self.pressed=False; self.dragging=False; self.setCursor(Qt.CursorShape.OpenHandCursor)
        if was_dragging:
            self.mascot.set_dragging(False,time.monotonic())
            self.position_changed.emit(*self.mascot_position)
        return was_dragging

    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.pressed:
            if not self.finish_drag(): self.open_menu(event.globalPosition().toPoint(),self.click_target)
            event.accept()
        else: super().mouseReleaseEvent(event)

    def contextMenuEvent(self,event):
        if self.mode=='waiting': self.open_menu(event.globalPos(),foreground())

    def open_menu(self,point,target):
        menu=QMenu(self)
        menu.setStyleSheet('QMenu{background:#101010;color:#eee;border:1px solid #333;padding:6px} QMenu::item{padding:9px 18px} QMenu::item:selected{background:#303030}')
        start=menu.addAction('Iniciar ditado'); settings=menu.addAction('Abrir Claus')
        menu.addSeparator(); hide=menu.addAction('Ocultar na bandeja')
        selected=menu.exec(point)
        if selected==start: QTimer.singleShot(0,lambda:self.dictation_requested.emit(target))
        elif selected==settings: self.settings_requested.emit()
        elif selected==hide: self.hide_requested.emit()

    def set_level(self,level): self.target_level=max(0,min(1,level))
    def set_wake_phrase(self,phrase): self.wake_phrase=phrase; self.update()

    def display(self,message,mode=None):
        next_mode=mode or ('processing' if 'Reconhecendo' in message else 'listening')
        if self.mode=='waiting' and next_mode!='waiting' and self.mascot_position is not None:
            self.mascot_position=(self.x(),self.y())
        if self.mode=='waiting' and next_mode!='waiting':
            self.wave_screen=QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if self.pressed: self.finish_drag()
        transparent=next_mode!='waiting'
        if bool(self.windowFlags() & Qt.WindowType.WindowTransparentForInput)!=transparent:
            self.setWindowFlag(Qt.WindowType.WindowTransparentForInput,transparent)
        self.mode=next_mode
        self.setWindowTitle('Claus — Personagem' if self.mode=='waiting' else 'Claus — Wave')
        self.setAccessibleName('Personagem Claus' if self.mode=='waiting' else 'Animação de transcrição')
        if self.mode=='waiting' or self.wave_screen not in QApplication.screens():
            self.wave_screen=QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        screen=self.wave_screen.availableGeometry()
        if self.mode=='waiting': self.setFixedSize(*self.mascot_size())
        else:
            scale=min(self.wave_percent/100,screen.width()/520,screen.height()/126)
            self.setFixedSize(round(520*scale),round(126*scale))
        if self.mode=='waiting': self.apply_mascot_mask(); self.setCursor(Qt.CursorShape.OpenHandCursor)
        # On Windows, clearMask() can leave the previous native silhouette after flag changes.
        else: self.setMask(QRegion(self.rect()))
        if self.mode!='waiting' and self.movie.state()!=QMovie.MovieState.Running: self.movie.start()
        elif self.mode=='waiting': self.movie.stop()
        if self.mode=='waiting':
            if self.mascot_position is None: self.mascot_position=(screen.right()-155,screen.bottom()-145)
            self.mascot_position=self.bounded_position(self.mascot_position)
            self.move(round(self.mascot_position[0]),round(self.mascot_position[1]))
        else: self.move(screen.x()+(screen.width()-self.width())//2,screen.y()+round((screen.height()-self.height())*self.wave_height/100))
        if self.mode=='waiting' and self.mascot_hidden: self.hide()
        else: self.show()
        self.update()

    def hideEvent(self,event): self.movie.stop(); super().hideEvent(event)

    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.mode=='waiting':
            cursor=QCursor.pos()
            sx=self.width()/128; sy=self.height()/120; p.scale(sx,sy)
            self.mascot.paint(p,(128,120),time.monotonic(),((cursor.x()-self.x())/sx,(cursor.y()-self.y())/sy))
            p.end(); return
        p.scale(self.width()/520,self.height()/126)
        panel=QRectF(3,3,514,120); clip=QPainterPath(); clip.addRoundedRect(panel,23,23)
        p.setClipPath(clip)
        if not self.transparent_wave:
            p.setPen(QPen(QColor('#303030'),1)); p.setBrush(QColor('#000000')); p.drawPath(clip)
        elapsed=time.monotonic()-self.epoch
        if self.mode!='waiting':
            wave=QRectF(20,7,480,112)
            background=self.transparent_background if self.transparent_wave else self.background
            if background and not background.isNull():
                p.save(); p.setOpacity(0.18+0.25*self.amplitude)
                size=background.size().scaled(wave.size().toSize(),Qt.AspectRatioMode.KeepAspectRatio)
                target=QRectF(wave.center().x()-size.width()/2,wave.center().y()-size.height()/2,size.width(),size.height())
                p.drawImage(target,background); p.restore()
            frame=motion_frame(elapsed*(0.7 if self.mode=='processing' else 1))
            fit=min(1,(wave.width()-60)/(22*32+240)); gap=32*fit
            maximum=65*(0.35+0.65*self.amplitude) if self.mode=='listening' else 39
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QColor('#f3f3f3'))
            for i,growth in enumerate(frame):
                diameter=maximum*fit*growth
                p.save(); p.translate(wave.center().x()+(i-11)*gap,wave.center().y())
                p.scale(diameter/31.11,-diameter/31.11); p.translate(15.553,0.286); p.drawPath(self.shape); p.restore()
        p.end()
