"""Claus app icon: the native character on a rounded light tile."""
import struct
from pathlib import Path
from PySide6.QtCore import QBuffer, QIODevice, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication
from mascot import Mascot


def icon_image(size=512,with_background=True):
    resolution=max(1024,size*2)
    image=QImage(resolution,resolution,QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter=QPainter(image); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(resolution/512,resolution/512)
    if with_background:
        painter.setPen(QPen(QColor('#d7d4cd'),1)); painter.setBrush(QColor('#f2f0ea'))
        painter.drawRoundedRect(QRectF(12,12,488,488),108,108)
    painter.translate(32,46); painter.scale(3.5,3.5)
    Mascot(0).paint(painter,(128,120),0,(64,60))
    painter.end()
    return image.scaled(size,size,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)


def generate():
    root=Path(__file__).resolve().parent
    target=root/'assets'/'brand'; target.mkdir(parents=True,exist_ok=True)
    icon_image().save(str(target/'claus.png'))
    sizes=(256,128,64,48,32,24,16); frames=[]
    for size in sizes:
        buffer=QBuffer(); buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        icon_image(size).save(buffer,'PNG'); frames.append(bytes(buffer.data()))
    offset=6+16*len(sizes); entries=[]
    for size,frame in zip(sizes,frames):
        entries.append(struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(frame),offset)); offset+=len(frame)
    data=struct.pack('<HHH',0,1,len(sizes))+b''.join(entries)+b''.join(frames)
    (target/'claus.ico').write_bytes(data)
    (root/'desktop-icon.ico').write_bytes(data); icon_image().save(str(root/'desktop-icon.png'))


if __name__=='__main__':
    app=QApplication.instance() or QApplication([]); generate()
