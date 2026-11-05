"""Native mascot based on the supplied six-lobed, white-eyed character."""
import math
import random
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainterPath, QPen, QRadialGradient


def blink_openness(elapsed,duration=0.18):
    if elapsed<0 or elapsed>=duration: return 1
    return max(0.04,math.cos(math.pi*elapsed/duration)**2)


def clamp_position(point,bounds,size):
    return (max(bounds[0],min(point[0],bounds[2]-size[0])),
            max(bounds[1],min(point[1],bounds[3]-size[1])))


def eye_path(cx,cy,openness,expression):
    eye=QPainterPath(); eye.addEllipse(QRectF(cx-43,cy-59*openness,86,118*openness))
    crop=QPainterPath(); crop.addRect(QRectF(cx-50,cy-59*openness+55*openness*expression,100,132*openness))
    return eye.intersected(crop)


class Mascot:
    def __init__(self,now):
        self.random=random.Random(); self.last_time=now; self.blink_start=-100
        self.next_blink=now+self.random.uniform(2,4); self.double_blink=False
        self.dragging=False; self.drag_mix=0; self.expression_until=0
        self.motion_energy=0; self.last_motion=now; self.motion_direction=(0,0)
        self.dizzy_until=0; self.dizzy_start=now; self.dizzy_mix=0
        self.pet_point=None; self.pet_direction=(0,0); self.pet_energy=0; self.pet_reversals=0
        self.pet_motion_time=now; self.last_pet=now; self.petting=False
        self.happy_until=0; self.confused_until=0
        self.pet_mix=0; self.happy_mix=0; self.confused_mix=0
        self.idle_state='awake'; self.state_since=now; self.sleep_until=0
        self.next_sleep=now+60+self.random.uniform(0,30); self.next_curious=now+self.random.uniform(10,22)
        self.sleep_mix=0; self.sleepy_mix=0; self.curious_mix=0; self.dance_mix=0
        self.busy=False; self.music_playing=False; self.dance_start=now
        self.next_squint=now+self.random.uniform(12,24)
        self.body=QPainterPath()
        for x,y,radius in [(-82,-117,105),(82,-117,105),(-177,0,93),(177,0,93),(-82,117,107),(72,117,107)]:
            petal=QPainterPath(); petal.addEllipse(QPointF(x,y),radius,radius)
            self.body=self.body.united(petal)
        middle=QPainterPath(); middle.addEllipse(QRectF(-165,-135,330,270)); self.body=self.body.united(middle)

    def set_dragging(self,dragging,now):
        self.dragging=dragging
        if dragging: self.interact(now); self.end_pet(now); self.happy_until=0
        if not dragging:
            self.expression_until=now+0.55; self.next_blink=now+0.8

    def pet_motion(self,x,y,now):
        self.interact(now)
        dt=max(0,now-self.pet_motion_time); self.pet_motion_time=now
        self.pet_energy*=math.exp(-dt/0.9)
        if dt>0.7: self.pet_reversals=0
        previous=self.pet_point; self.pet_point=(x,y)
        if previous is None: return
        dx=x-previous[0]; dy=y-previous[1]; distance=math.hypot(dx,dy)
        if distance<1: return
        direction=(dx/distance,dy/distance)
        if direction[0]*self.pet_direction[0]+direction[1]*self.pet_direction[1]<-0.3:
            self.pet_reversals+=1
        self.pet_direction=direction; self.pet_energy+=min(40,distance)
        if self.pet_energy>=100 and self.pet_reversals>=2: self.petting=True
        if self.petting:
            self.last_pet=now; self.happy_until=0; self.confused_until=0; self.dizzy_until=0

    def end_pet(self,now):
        self.pet_point=None
        if self.petting:
            self.petting=False; self.happy_until=now+8; self.pet_energy=0; self.pet_reversals=0

    def show_confused(self,now):
        self.interact(now)
        self.end_pet(now); self.happy_until=0; self.confused_until=now+5
        self.dizzy_until=0; self.expression_until=0

    def wake(self,now):
        if self.idle_state=='sleeping':
            self.idle_state='waking'; self.state_since=now
            self.next_sleep=now+64+self.random.uniform(0,30)
        elif self.idle_state=='curious': self.idle_state='awake'

    def interact(self,now):
        self.wake(now); self.next_sleep=max(self.next_sleep,now+60)
        self.next_curious=max(self.next_curious,now+10)

    def set_busy(self,busy,now):
        self.busy=busy
        if busy: self.interact(now)

    def set_music(self,playing,now):
        if playing and not self.music_playing: self.dance_start=now; self.interact(now)
        self.music_playing=playing

    def drag_motion(self,dx,dy,now):
        distance=math.hypot(dx,dy)
        self.motion_energy*=math.exp(-max(0,now-self.last_motion)/1.2); self.last_motion=now
        if distance<2: return
        previous=self.motion_direction; self.motion_direction=(dx/distance,dy/distance)
        reversal=self.motion_direction[0]*previous[0]+self.motion_direction[1]*previous[1]<-0.3
        self.motion_energy=min(700,self.motion_energy+distance*(1.6 if reversal else 1))
        if self.motion_energy>=460:
            if now>=self.dizzy_until: self.dizzy_start=now
            self.dizzy_until=now+3.4

    def update(self,now):
        dt=min(1,max(0,now-self.last_time)); self.last_time=now
        if self.petting and now-self.last_pet>0.45: self.end_pet(now)
        interacting=self.dragging or self.petting or now<max(self.happy_until,self.confused_until,self.dizzy_until)
        occupied=interacting or self.busy or self.music_playing
        if self.idle_state=='sleeping' and (occupied or now>=self.sleep_until): self.wake(now)
        if self.idle_state=='waking' and now-self.state_since>=4:
            self.idle_state='awake'; self.next_sleep=now+60+self.random.uniform(0,30)
        if self.idle_state=='curious' and (occupied or now-self.state_since>=4): self.idle_state='awake'
        if self.idle_state=='awake' and not occupied:
            if now>=self.next_sleep:
                self.idle_state='sleeping'; self.state_since=now; self.sleep_until=now+self.random.uniform(12,22)
            elif now>=self.next_curious:
                self.idle_state='curious'; self.state_since=now; self.next_curious=now+self.random.uniform(16,32)
        targets=[('sleep_mix',float(self.idle_state=='sleeping')),
                 ('sleepy_mix',max(0,1-(now-self.state_since)/4) if self.idle_state=='waking' else 0),
                 ('curious_mix',float(self.idle_state=='curious')),
                 ('dance_mix',float(self.music_playing and not self.busy and not interacting))]
        for attribute,target in targets:
            value=getattr(self,attribute); setattr(self,attribute,value+(target-value)*(1-math.exp(-dt/0.3)))
        for attribute,target in [('pet_mix',self.petting),('happy_mix',now<self.happy_until),('confused_mix',now<self.confused_until)]:
            value=getattr(self,attribute); setattr(self,attribute,value+(float(target)-value)*(1-math.exp(-dt/0.18)))
        dizzy_target=1 if now<self.dizzy_until else 0
        self.dizzy_mix+=(dizzy_target-self.dizzy_mix)*(1-math.exp(-dt/(0.18 if dizzy_target else 0.5)))
        if now>=self.next_squint and not self.dragging:
            self.expression_until=now+self.random.uniform(0.8,1.4)
            self.next_squint=self.expression_until+self.random.uniform(15,30)
        target=1 if self.dragging or now<self.expression_until else 0
        self.drag_mix+=(target-self.drag_mix)*(1-math.exp(-dt/0.14))
        if now>=self.next_blink:
            self.blink_start=now
            if not self.double_blink and self.random.random()<0.18:
                self.next_blink=now+0.32; self.double_blink=True
            else:
                self.next_blink=now+self.random.uniform(3,6.5); self.double_blink=False

    def paint(self,painter,size,now,cursor_relative):
        painter.save(); painter.translate(size[0]/2,size[1]/2)
        scale=0.20*(1+(0.012+0.012*self.sleep_mix)*math.sin(now*(1.8-0.8*self.sleep_mix))); painter.scale(scale,scale)
        beat=(now-self.dance_start)*math.tau*1.7
        painter.translate(8*self.dance_mix*math.sin(beat),-12*self.dance_mix*abs(math.sin(beat)))
        painter.rotate(4*self.dance_mix*math.sin(beat))
        painter.scale(1+0.018*self.dance_mix*math.sin(beat*2),1-0.018*self.dance_mix*math.sin(beat*2))
        dx=cursor_relative[0]-size[0]/2; dy=cursor_relative[1]-size[1]/2
        distance=max(1,math.hypot(dx,dy)); gaze=(dx/distance*10,dy/distance*7)
        curious=math.sin((now-self.state_since)*math.pi/2)*self.curious_mix
        gaze=(gaze[0]*(1-self.curious_mix)+18*curious,gaze[1]*(1-self.curious_mix))
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor(180,180,180,95))
        painter.save(); painter.translate(5,6); painter.drawPath(self.body); painter.restore()
        painter.setPen(QPen(QColor('#252525'),4)); painter.setBrush(QColor('#000000')); painter.drawPath(self.body)
        painter.setPen(Qt.PenStyle.NoPen)
        if self.pet_mix>0.01:
            for cx in (-110,116):
                painter.save(); painter.setOpacity(self.pet_mix*(0.9+0.1*math.sin(now*5)))
                painter.translate(cx,42); painter.scale(1,0.5)
                blush=QRadialGradient(0,0,35); blush.setColorAt(0,QColor(255,141,171,210)); blush.setColorAt(1,QColor(255,141,171,0))
                painter.setBrush(blush); painter.drawEllipse(QRectF(-35,-35,70,70)); painter.restore()
        openness=blink_openness(now-self.blink_start)*(1-self.dizzy_mix)+self.dizzy_mix
        expression=max(self.drag_mix*(1-self.dizzy_mix),0.85*self.sleepy_mix)
        emotion=max(self.pet_mix,self.happy_mix,self.confused_mix)
        openness=openness*(1-emotion)+emotion
        for index,cx in enumerate((-53,63)):
            cx+=gaze[0]*(1-max(self.dizzy_mix,emotion)); cy=-18+gaze[1]*(1-max(self.dizzy_mix,emotion))
            cy-=5*max(0,curious*(1 if index==1 else -1))
            joy=max(self.happy_mix,0.35*self.dance_mix)
            eye=eye_path(cx,cy,openness*(1-0.35*joy),max(expression*(1-emotion),self.confused_mix if index==0 else 0))
            if self.pet_mix>0.01:
                cut=QPainterPath(); cut.addEllipse(QRectF(cx-(105 if index==0 else 65),cy+65-55*self.pet_mix,170,110))
                eye=eye.subtracted(cut)
            if joy>0.01:
                cut=QPainterPath(); bottom=cy+70-48*joy
                cut.moveTo(cx-60,bottom); cut.quadTo(cx,bottom-22*joy,cx+60,bottom)
                cut.lineTo(cx+60,cy+100); cut.lineTo(cx-60,cy+100); cut.closeSubpath(); eye=eye.subtracted(cut)
            painter.save(); painter.setOpacity(1-self.sleep_mix)
            painter.setPen(QPen(QColor('#272727'),6)); painter.setBrush(QColor('#fafafa')); painter.drawPath(eye)
            painter.save(); painter.setClipPath(eye,Qt.ClipOperation.IntersectClip)
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor(222,222,222,round(255*(1-expression))))
            painter.drawEllipse(QRectF(cx-52,cy+35*openness,104,60*openness))
            if self.dizzy_mix>0.01:
                direction=1 if index==0 else -1
                painter.save(); painter.setOpacity(self.dizzy_mix)
                painter.translate(cx,cy); painter.scale(1,1.3)
                painter.rotate(direction*(now-self.dizzy_start)*160+index*35)
                spiral=QPainterPath()
                for step in range(121):
                    t=step/120; angle=direction*t*math.pi*4
                    radius=2+29*t
                    point=QPointF(math.cos(angle)*radius,math.sin(angle)*radius)
                    if step==0: spiral.moveTo(point)
                    else: spiral.lineTo(point)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor('#414141'),5.5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
                painter.drawPath(spiral); painter.restore()
            painter.restore()
            painter.restore()
            if self.sleep_mix>0.01:
                painter.save(); painter.setOpacity(self.sleep_mix); painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor('#fafafa'),5.5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                lid=QPainterPath(); lid.moveTo(cx-31,cy+6); lid.quadTo(cx,cy+25,cx+31,cy+6)
                painter.drawPath(lid); painter.restore()
        smile_mix=max(self.happy_mix,0.65*self.dance_mix)
        if smile_mix>0.01:
            painter.save(); painter.setOpacity(smile_mix); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor('#fafafa'),7,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
            smile=QPainterPath(); smile.moveTo(-34,72); smile.cubicTo(-15,97,25,97,43,72)
            painter.drawPath(smile); painter.restore()
        if self.sleepy_mix>0.01 and emotion<0.1:
            painter.save(); painter.setOpacity(self.sleepy_mix); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor('#ddd'),5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
            painter.drawEllipse(QRectF(-5,64,18,24)); painter.restore()
        if self.confused_mix>0.01:
            painter.save(); painter.setOpacity(self.confused_mix); painter.translate(0,2*math.sin(now*3))
            painter.setPen(QPen(QColor('#fafafa'),7,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap)); painter.setBrush(Qt.BrushStyle.NoBrush)
            question=QPainterPath(); question.moveTo(86,-146); question.cubicTo(86,-173,123,-173,123,-149)
            question.cubicTo(123,-132,105,-135,105,-117); painter.drawPath(question)
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QColor('#fafafa')); painter.drawEllipse(QPointF(105,-102),4,4); painter.restore()
        painter.restore()
