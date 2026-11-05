"""Appearance controls with a microphone-free preview."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QSpinBox, QVBoxLayout
from listening_overlay import ListeningOverlay


def apply_saved_appearance(settings,overlay):
    overlay.configure(settings.value('mascot_size',100,type=int),settings.value('wave_size',100,type=int),
                      settings.value('wave_height',97,type=int),settings.value('wave_transparent',False,type=bool))


class AppearanceDialog(QDialog):
    def __init__(self,settings,overlay,parent=None,wave_overlay=None):
        super().__init__(parent); self.setWindowTitle('Claus — Aparência'); self.setMinimumWidth(440)
        self.settings=settings; self.overlay=overlay; self.preview=ListeningOverlay(); self.preview.set_level(0.65)
        self.wave_overlay=wave_overlay
        layout=QVBoxLayout(self); layout.setContentsMargins(24,22,24,22); layout.setSpacing(16)
        title=QLabel('Do seu tamanho. No seu lugar.'); title.setStyleSheet('font:23px Georgia;color:#eee'); layout.addWidget(title)
        form=QFormLayout(); form.setSpacing(14); self.controls={}
        for label,key,minimum,maximum,default in [('Tamanho do personagem','mascot_size',50,250,100),
                                                ('Tamanho da transcrição','wave_size',50,200,100)]:
            control=QSpinBox(); control.setRange(minimum,maximum); control.setSingleStep(10); control.setSuffix(' %')
            control.setValue(settings.value(key,default,type=int)); control.setAccessibleName(label)
            self.controls[key]=control; form.addRow(label,control)
        height=QSlider(Qt.Orientation.Horizontal); height.setRange(0,100)
        height.setValue(settings.value('wave_height',97,type=int)); height.setAccessibleName('Altura da transcrição na tela')
        value=QSpinBox(); value.setRange(0,100); value.setSuffix(' %'); value.setValue(height.value())
        value.setAccessibleName('Altura da transcrição em porcentagem'); height.valueChanged.connect(value.setValue); value.valueChanged.connect(height.setValue)
        row=QHBoxLayout(); row.addWidget(QLabel('Topo')); row.addWidget(height,1); row.addWidget(QLabel('Base')); row.addWidget(value)
        self.controls['wave_height']=height; form.addRow('Altura na tela',row); layout.addLayout(form)
        self.transparent=QCheckBox('Fundo transparente · manter onda e geometria')
        self.transparent.setChecked(settings.value('wave_transparent',False,type=bool)); layout.addWidget(self.transparent)
        note=QLabel('Os ajustes são salvos automaticamente. Arraste o personagem para escolher a posição dele.')
        note.setWordWrap(True); note.setStyleSheet('color:#aaa'); layout.addWidget(note)
        buttons=QHBoxLayout(); self.preview_button=QPushButton('Visualizar na tela'); self.preview_button.setCheckable(True)
        self.preview_button.toggled.connect(self.toggle_preview); buttons.addWidget(self.preview_button)
        close=QPushButton('Concluir'); close.clicked.connect(self.accept); buttons.addWidget(close); layout.addLayout(buttons)
        self.setStyleSheet('QDialog{background:#000} QSpinBox{background:#111;color:#eee;border:1px solid #333;border-radius:6px;padding:8px;min-width:76px} QSlider::groove:horizontal{height:5px;background:#333;border-radius:2px} QSlider::handle:horizontal{width:16px;background:#eee;border-radius:8px;margin:-6px 0}')
        for control in self.controls.values(): control.valueChanged.connect(self.save)
        self.transparent.toggled.connect(self.save)
        apply_saved_appearance(settings,self.preview)

    def save(self):
        for key,control in self.controls.items(): self.settings.setValue(key,control.value())
        self.settings.setValue('wave_transparent',self.transparent.isChecked())
        apply_saved_appearance(self.settings,self.overlay); apply_saved_appearance(self.settings,self.preview)
        if self.wave_overlay is not None: apply_saved_appearance(self.settings,self.wave_overlay)
        if self.overlay.mascot_position is not None:
            self.settings.setValue('mascot_x',self.overlay.mascot_position[0]); self.settings.setValue('mascot_y',self.overlay.mascot_position[1])
        self.settings.sync()

    def toggle_preview(self,enabled):
        if enabled: self.preview.display('',mode='listening')
        else: self.preview.hide()
        self.preview_button.setText('Ocultar prévia' if enabled else 'Visualizar na tela')

    def done(self,result):
        self.preview.hide(); self.preview.animation.stop(); self.preview.deleteLater()
        super().done(result)
