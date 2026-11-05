"""Claus desktop: deliberate hotkey capture, local ASR, focus-checked paste."""
import ctypes
from ctypes import wintypes
import json
import logging
import os
from pathlib import Path
import sys
import time
import uuid
import wave

ROOT = Path(__file__).resolve().parent
(ROOT / '.tmp').mkdir(exist_ok=True)
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                  DO_NOT_TRACK='1', TEMP=str(ROOT / '.tmp'), TMP=str(ROOT / '.tmp'))
logging.basicConfig(filename=ROOT / 'desktop.log', level=logging.INFO, encoding='utf-8')

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QAbstractNativeEventFilter, QTimer, Qt, QThread, Signal, QSettings
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap, QPalette
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QProgressBar,
    QPushButton, QSystemTrayIcon, QVBoxLayout, QWidget, QFrame, QTabWidget, QScrollArea)
from desktop_engine import DictationEngine, GPU_EXE, GPU_MODEL, paste_allowed
from desktop_windows import user32, foreground, modifiers_down, paste_shortcut
from voice_control import WakeListener, SpeechEndpoint, prepare_wake_phrase
from listening_overlay import ListeningOverlay
from appearance import AppearanceDialog, apply_saved_appearance
from music_monitor import MusicMonitor


def app_icon():
    return QIcon(str(ROOT/'assets'/'brand'/'claus.ico'))


def tray_icon():
    # Supply actual raster sizes to the Windows tray instead of an ICO file engine.
    source=QPixmap(str(ROOT/'assets'/'brand'/'claus.png')); icon=QIcon()
    if source.isNull(): return app_icon()
    for size in (16,20,24,32,40,48,64):
        icon.addPixmap(source.scaled(size,size,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    return icon


class Hotkey(QAbstractNativeEventFilter):
    ID = 0xE5C0
    def __init__(self, callback):
        super().__init__(); self.callback = callback
        self.registered = bool(user32.RegisterHotKey(None, self.ID, 0x4003, 0x20))

    def nativeEventFilter(self, event_type, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x0312 and msg.wParam == self.ID:
            QTimer.singleShot(0, self.callback); return True, 0
        return False, 0

    def close(self):
        if self.registered: user32.UnregisterHotKey(None, self.ID)


class Transcriber(QThread):
    text_ready = Signal(str, float)
    error = Signal(str)
    def __init__(self, engine, filename, backend, language, glossary):
        super().__init__(); self.engine = engine; self.filename = filename
        self.backend = backend; self.language = language; self.glossary = glossary

    def run(self):
        start = time.monotonic()
        try:
            text = self.engine.transcribe(self.filename, self.backend, self.language, self.glossary)
            self.text_ready.emit(text, time.monotonic() - start)
        except Exception as exc:
            logging.exception('Falha de transcrição desktop')
            self.error.emit(str(exc))
        finally: self.filename.unlink(missing_ok=True)


class Claus(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle('Claus — Ditado'); self.setWindowIcon(app_icon())
        self.resize(660, 800); self.setMinimumSize(580,650); self.settings = QSettings(str(ROOT / 'desktop-settings.ini'), QSettings.Format.IniFormat)
        try: self.wake_phrase=prepare_wake_phrase(self.settings.value('wake_phrase','computador'))
        except ValueError: self.wake_phrase='computador'
        self.engine = DictationEngine(); self.recording = False; self.processing = False
        self.recorder = None; self.blocks = []; self.level = 0; self.overflow = False
        self.target = 0; self.worker = None; self.start_time = 0
        self.wake_listener = None; self.endpoint = None; self.last_vad = 0; self.closing = False; self.pending_target = None
        self.overlay = ListeningOverlay(); apply_saved_appearance(self.settings,self.overlay)
        self.wave_overlay=ListeningOverlay(); apply_saved_appearance(self.settings,self.wave_overlay)
        self.build_ui(); self.build_tray(); self.refresh_devices()
        self.overlay.set_wake_phrase(self.wake_phrase)
        if self.settings.contains('mascot_x') and self.settings.contains('mascot_y'):
            self.overlay.restore_position(self.settings.value('mascot_x',type=int),self.settings.value('mascot_y',type=int))
        self.overlay.set_mascot_hidden(not self.mascot_action.isChecked())
        self.overlay.position_changed.connect(self.save_mascot_position)
        self.overlay.hide_requested.connect(lambda:self.mascot_action.setChecked(False))
        self.overlay.settings_requested.connect(self.show_settings)
        self.overlay.dictation_requested.connect(self.mascot_dictation)
        self.music_monitor=MusicMonitor(self)
        self.music_monitor.changed.connect(lambda playing:self.overlay.mascot.set_music(playing,time.monotonic()))
        self.music_monitor.error.connect(logging.warning); self.music_monitor.start()
        self.voice_enabled.toggled.connect(self.voice_changed); self.mics.currentIndexChanged.connect(self.voice_changed)
        self.hotkey = Hotkey(self.toggle_hotkey); QApplication.instance().installNativeEventFilter(self.hotkey)
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(100)
        if not self.hotkey.registered:
            self.state.setText('O atalho está em uso por outro aplicativo. Feche-o e reabra o Claus.')
        QApplication.instance().aboutToQuit.connect(self.hotkey.close)
        QTimer.singleShot(600,self.ensure_wake)

    def build_ui(self):
        palette=QPalette()
        for role,color in [(QPalette.ColorRole.Window,'#000000'),(QPalette.ColorRole.WindowText,'#eeeeee'),(QPalette.ColorRole.Base,'#111111'),(QPalette.ColorRole.AlternateBase,'#181818'),(QPalette.ColorRole.Text,'#eeeeee'),(QPalette.ColorRole.Button,'#181818'),(QPalette.ColorRole.ButtonText,'#eeeeee'),(QPalette.ColorRole.Highlight,'#dedede'),(QPalette.ColorRole.HighlightedText,'#000000')]: palette.setColor(role,QColor(color))
        QApplication.instance().setPalette(palette)
        root=QWidget(); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(0,0,0,0)
        content=QWidget(); content.setMaximumWidth(860); outer.addStretch(); outer.addWidget(content,1); outer.addStretch()
        layout=QVBoxLayout(content); layout.setContentsMargins(26,24,26,20); layout.setSpacing(20)
        title_row=QHBoxLayout(); title_row.setSpacing(13)
        logo=QLabel(); logo.setPixmap(app_icon().pixmap(54,54)); title_row.addWidget(logo)
        brand=QVBoxLayout(); brand.setSpacing(1)
        title=QLabel('Claus'); title.setStyleSheet('font-size:27px;font-weight:650;color:#f5f5f5;'); brand.addWidget(title)
        subtitle=QLabel('Sua voz. Seu companheiro.'); subtitle.setObjectName('muted'); brand.addWidget(subtitle)
        title_row.addLayout(brand); title_row.addStretch()
        appearance=QPushButton('Aparência'); appearance.clicked.connect(self.show_appearance); title_row.addWidget(appearance); layout.addLayout(title_row)
        self.pages=QTabWidget(); self.pages.setDocumentMode(True); layout.addWidget(self.pages,1)
        dictation=QWidget(); dictation_layout=QVBoxLayout(dictation); dictation_layout.setContentsMargins(20,24,20,20); dictation_layout.setSpacing(16)
        self.pages.addTab(dictation,'Ditado')
        heading=QLabel('Fale. O Claus escreve.'); heading.setStyleSheet('font:27px Georgia;color:#f0f0f0;'); dictation_layout.addWidget(heading)
        note=QLabel('Clique onde deseja escrever. Chame o Claus, aguarde a onda e fale. Uma pausa conclui o ditado.'); note.setWordWrap(True); note.setObjectName('muted'); dictation_layout.addWidget(note)
        callout=QFrame(); callout.setObjectName('callout'); callout_layout=QVBoxLayout(callout); callout_layout.setContentsMargins(16,13,16,13); callout_layout.setSpacing(5)
        callout_heading=QLabel('Sua chamada por voz'); callout_heading.setObjectName('muted'); callout_layout.addWidget(callout_heading)
        self.callout=QLabel(f'“{self.wake_phrase}”  ·  fale  ·  faça uma pausa'); self.callout.setWordWrap(True); self.callout.setStyleSheet('font-size:16px;font-weight:600;color:#f3f3f3;'); callout_layout.addWidget(self.callout); dictation_layout.addWidget(callout)
        preferences=QWidget(); preferences_layout=QVBoxLayout(preferences); preferences_layout.setContentsMargins(20,24,20,20); preferences_layout.setSpacing(16)
        preferences_heading=QLabel('Seu jeito de ditar.'); preferences_heading.setStyleSheet('font:25px Georgia;color:#eee;'); preferences_layout.addWidget(preferences_heading)
        preference_note=QLabel('Escolha a entrada, a chamada e o reconhecimento. O visual do personagem fica em Aparência.'); preference_note.setWordWrap(True); preference_note.setObjectName('muted'); preferences_layout.addWidget(preference_note)
        form = QFormLayout(); form.setSpacing(10); self.mics = QComboBox(); self.mics.setAccessibleName('Entrada do microfone')
        row = QHBoxLayout(); row.addWidget(self.mics,1); self.refresh = QPushButton('Atualizar'); self.refresh.clicked.connect(self.refresh_devices); row.addWidget(self.refresh)
        form.addRow('Microfone',row)
        self.wake_input=QLineEdit(self.wake_phrase); self.wake_input.setMaxLength(60); self.wake_input.setAccessibleName('Palavra ou frase de ativação')
        self.save_wake=QPushButton('Salvar chamada'); self.save_wake.clicked.connect(self.save_wake_phrase); self.wake_input.returnPressed.connect(self.save_wake_phrase)
        wake_row=QHBoxLayout(); wake_row.addWidget(self.wake_input,1); wake_row.addWidget(self.save_wake); form.addRow('Chamada por voz',wake_row)
        hint=QLabel('Escolha de 1 a 4 palavras em português. Prefira uma chamada incomum.'); hint.setWordWrap(True); hint.setStyleSheet('color:#929292;font-size:10px;'); form.addRow('',hint)
        self.backend = QComboBox(); self.backend.addItem('GPU AMD · Whisper Turbo (Vulkan)', 'gpu'); self.backend.addItem('CPU · Whisper Small (mais leve)', 'small'); self.backend.addItem('CPU · Whisper Turbo (qualidade)', 'turbo')
        self.backend.setAccessibleName('Motor de transcrição'); form.addRow('Motor',self.backend)
        self.language = QComboBox(); self.language.addItem('Português','pt'); self.language.addItem('Detectar idioma','auto'); self.language.addItem('Inglês','en'); self.language.addItem('Espanhol','es'); form.addRow('Idioma', self.language)
        self.pause_choice = QComboBox(); self.pause_choice.addItem('1,2 s · rápida',1.2); self.pause_choice.addItem('1,8 s · natural',1.8); self.pause_choice.addItem('2,8 s · pausas longas',2.8); self.pause_choice.setCurrentIndex(1); form.addRow('Concluir após',self.pause_choice)
        self.glossary = QLineEdit(); self.glossary.setMaxLength(500); self.glossary.setPlaceholderText('Nomes, siglas e termos esperados'); form.addRow('Vocabulário', self.glossary); preferences_layout.addLayout(form)
        chosen = self.backend.findData(self.settings.value('backend','gpu' if GPU_MODEL.is_file() else 'small')); self.backend.setCurrentIndex(max(0,chosen))
        self.glossary.setText(self.settings.value('glossary',''))
        self.auto_paste = QCheckBox('Colar automaticamente na janela original'); self.auto_paste.setChecked(True); preferences_layout.addWidget(self.auto_paste)
        self.voice_enabled = QCheckBox(f'Ativação por voz · ouvir “{self.wake_phrase}” neste computador'); self.voice_enabled.setChecked(self.settings.value('voice_enabled',True,type=bool)); preferences_layout.addWidget(self.voice_enabled)
        preferences_layout.addStretch()
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame); scroll.setWidget(preferences); self.pages.addTab(scroll,'Configurações')
        status=QVBoxLayout(); status.setSpacing(9)
        self.state = QLabel('Preparando o microfone local…'); self.state.setWordWrap(True); self.state.setAccessibleName('Estado do ditado'); status.addWidget(self.state)
        self.meter = QProgressBar(); self.meter.setRange(0,100); self.meter.setTextVisible(False); self.meter.setFixedHeight(5); status.addWidget(self.meter); dictation_layout.addLayout(status)
        buttons = QHBoxLayout(); self.test = QPushButton('Testar ditado aqui'); self.test.setObjectName('primary'); self.test.clicked.connect(lambda: self.toggle(False)); buttons.addWidget(self.test)
        hide = QPushButton('Usar em outros aplicativos'); hide.clicked.connect(self.hide); buttons.addWidget(hide); dictation_layout.addLayout(buttons)
        result_header=QHBoxLayout(); label=QLabel('Último ditado'); label.setStyleSheet('font-weight:600;color:#ccc;'); result_header.addWidget(label); result_header.addStretch()
        copy = QPushButton('Copiar'); copy.clicked.connect(lambda: QApplication.clipboard().setText(self.output.toPlainText())); result_header.addWidget(copy); dictation_layout.addLayout(result_header)
        self.output = QPlainTextEdit(); self.output.setPlaceholderText('Suas palavras aparecem aqui.'); self.output.setAccessibleName('Último ditado'); self.output.setMinimumHeight(120); dictation_layout.addWidget(self.output,1)
        footer = QLabel('Ctrl + Alt + Espaço para ditar · Fechar mantém o Claus na bandeja.'); footer.setWordWrap(True); footer.setObjectName('muted'); footer.setStyleSheet('font-size:11px;'); layout.addWidget(footer)
        self.setStyleSheet('QMainWindow{background:#000000} QWidget{font-family:"Segoe UI";font-size:13px;color:#eeeeee} QComboBox,QLineEdit,QPlainTextEdit{background:#111111;border:1px solid #333333;border-radius:7px;padding:9px;selection-background-color:#eeeeee;selection-color:#000000} QComboBox QAbstractItemView{background:#151515;color:#eeeeee;selection-background-color:#373737} QPushButton{background:#181818;color:#eeeeee;border:1px solid #363636;border-radius:7px;padding:10px 13px} QPushButton:hover{background:#292929} QPushButton#primary{background:#eeeeee;color:#000000;border:0} QPushButton#primary:hover{background:#cccccc} QProgressBar{border:0;background:#252525;border-radius:3px} QProgressBar::chunk{background:#eeeeee;border-radius:3px} QComboBox:disabled,QLineEdit:disabled,QPushButton:disabled{color:#777777;border-color:#252525} QLineEdit:focus,QPlainTextEdit:focus{border:1px solid #aaaaaa} QMenu{background:#111111;color:#eeeeee;border:1px solid #333333} QMenu::item:selected{background:#333333}')
        self.setStyleSheet(self.styleSheet()+'''QLabel#muted{color:#969696}
            QFrame#callout{background:#111;border:1px solid #292929;border-radius:13px}
            QFrame#callout QLabel{background:transparent;border:0}
            QTabWidget::pane{border:1px solid #262626;border-radius:15px;top:-1px;background:#000}
            QTabBar::tab{color:#999;background:transparent;padding:12px 17px;margin-right:6px;border-bottom:2px solid transparent}
            QTabBar::tab:selected{color:#f2f0ea;border-bottom:2px solid #f2f0ea}
            QTabBar::tab:hover{color:#eee}
            QScrollArea,QScrollArea>QWidget>QWidget{background:#000;border:0}
            QScrollBar:vertical{background:#111;width:8px;border-radius:4px}
            QScrollBar::handle:vertical{background:#444;border-radius:4px;min-height:24px}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0}
            QPushButton:focus,QComboBox:focus{border-color:#aaa}
            QPlainTextEdit{border-color:#272727;border-radius:12px;padding:14px}''')

    def build_tray(self):
        self._tray_icon=tray_icon()
        self.tray=QSystemTrayIcon(self); self.tray.setIcon(self._tray_icon); self.tray.setToolTip('Claus · Ctrl+Alt+Espaço')
        menu = QMenu(); menu.addAction('Abrir Claus',self.show_settings)
        self.mascot_action=menu.addAction('Mostrar personagem')
        self.mascot_action.setCheckable(True); self.mascot_action.setChecked(self.settings.value('mascot_visible',True,type=bool))
        self.mascot_action.toggled.connect(self.set_mascot_visible)
        menu.addAction('Ligar / pausar ativação por voz',lambda:self.voice_enabled.setChecked(not self.voice_enabled.isChecked()))
        menu.addSeparator(); menu.addAction('Sair',self.quit_app)
        self.tray.setContextMenu(menu); self.tray.activated.connect(self.tray_activated); self.tray.show()
        QTimer.singleShot(1000,lambda:self.tray.setIcon(self._tray_icon))

    def tray_activated(self,reason):
        if reason==QSystemTrayIcon.ActivationReason.DoubleClick: self.show_settings()
        elif reason==QSystemTrayIcon.ActivationReason.Trigger: self.mascot_action.setChecked(True)

    def set_mascot_visible(self,visible):
        self.settings.setValue('mascot_visible',visible); self.settings.sync()
        self.overlay.set_mascot_hidden(not visible)

    def save_mascot_position(self,x,y):
        self.settings.setValue('mascot_x',x); self.settings.setValue('mascot_y',y); self.settings.sync()

    def mascot_dictation(self,target):
        self.pending_target=target; self.toggle(True)

    def show_settings(self): self.showNormal(); self.raise_(); self.activateWindow()

    def show_appearance(self): AppearanceDialog(self.settings,self.overlay,self,wave_overlay=self.wave_overlay).exec()

    def save_wake_phrase(self):
        if self.recording or self.processing: return
        try:
            phrase=WakeListener.validate_phrase(ROOT/'models'/'vosk-model-small-pt-0.3',self.wake_input.text())
        except Exception as exc:
            self.state.setText(str(exc)); return
        self.wake_phrase=phrase; self.wake_input.setText(phrase)
        self.settings.setValue('wake_phrase',phrase); self.settings.sync()
        self.callout.setText(f'“{phrase}”  ·  fale  ·  faça uma pausa')
        self.voice_enabled.setText(f'Ativação por voz · ouvir “{phrase}” neste computador')
        self.overlay.set_wake_phrase(phrase); self.voice_changed()
        if not self.voice_enabled.isChecked(): self.state.setText(f'Chamada “{phrase}” salva. Ativação por voz pausada.')

    def stop_wake(self):
        if self.wake_listener and self.wake_listener.isRunning():
            self.wake_listener.stop(); return self.wake_listener.wait(1500)
        return True

    def voice_changed(self,*args):
        self.settings.setValue('voice_enabled',self.voice_enabled.isChecked()); self.settings.sync()
        self.stop_wake()
        if not self.recording and not self.processing:
            self.wave_overlay.hide()
            if not self.voice_enabled.isChecked(): self.overlay.hide()
            self.state.setText('Ativação por voz pausada.' if not self.voice_enabled.isChecked() else 'Preparando chamada local…')
            QTimer.singleShot(400,self.ensure_wake)

    def ensure_wake(self):
        if self.closing or self.recording or self.processing: return
        if not self.voice_enabled.isChecked(): self.overlay.hide(); self.wave_overlay.hide(); return
        if self.wake_listener and self.wake_listener.isRunning():
            if self.wake_listener.stopping.is_set(): QTimer.singleShot(200,self.ensure_wake)
            return
        if self.worker and self.worker.isRunning(): QTimer.singleShot(200,self.ensure_wake); return
        try:
            device=self.mics.currentData(); rate=int(sd.query_devices(device,'input')['default_samplerate'])
            path=ROOT/'models'/'vosk-model-small-pt-0.3'
            if not path.is_dir(): raise RuntimeError('Modelo local de chamada ausente.')
            self.wake_listener=WakeListener(path,device,rate,(self.wake_phrase,))
            self.wake_listener.detected.connect(self.voice_wakeup)
            self.wake_listener.ready.connect(self.wake_ready)
            self.wake_listener.error.connect(self.wake_failed)
            self.wake_listener.start()
        except Exception as exc: self.wake_failed(str(exc))

    def wake_ready(self):
        if self.recording or self.processing or not self.voice_enabled.isChecked(): return
        self.state.setText(f'Diga “{self.wake_phrase}”, aguarde a animação e comece a falar.')
        self.overlay.mascot.set_busy(False,time.monotonic())
        self.wave_overlay.hide(); self.overlay.display('Microfone local · aguardando chamada',mode='waiting')

    def wake_failed(self,message):
        logging.error(message); self.voice_enabled.setChecked(False); self.state.setText(message)

    def voice_wakeup(self):
        if self.recording or self.processing or not self.voice_enabled.isChecked(): return
        self.pending_target=foreground(); self.toggle(True)

    def refresh_devices(self):
        if self.recording or self.processing: return
        try:
            devices = sd.query_devices(); apis = sd.query_hostapis(); self.mics.clear(); self.mics.addItem('Padrão do Windows',None)
            inputs = [(i,d) for i,d in enumerate(devices) if d['max_input_channels']>0]
            wasapi = [(i,d) for i,d in inputs if 'WASAPI' in apis[d['hostapi']]['name']]
            for index, device in wasapi or inputs:
                self.mics.addItem(device['name'], index)
                if device['name'] == self.settings.value('microphone',''): self.mics.setCurrentIndex(self.mics.count()-1)
        except Exception as exc: self.state.setText(f'Não foi possível listar microfones: {exc}')

    def toggle_hotkey(self): self.toggle(True)

    def toggle(self, from_hotkey):
        if self.processing: return
        if self.recording: self.stop(); return
        if self.worker is not None and self.worker.isRunning(): return
        if self.pending_target is None: self.pending_target = foreground() if from_hotkey else 0
        if not self.stop_wake(): QTimer.singleShot(150,lambda:self.toggle(from_hotkey)); return
        self.target = self.pending_target; self.pending_target = None
        if self.target == int(self.winId()): self.target = 0
        try:
            device = self.mics.currentData(); info = sd.query_devices(device,'input'); self.sample_rate = int(info['default_samplerate'])
            sd.check_input_settings(device=device, channels=1, samplerate=self.sample_rate, dtype='float32')
            self.blocks = []; self.overflow = False; self.level = 0
            self.recorder = sd.InputStream(device=device, samplerate=self.sample_rate, channels=1, dtype='float32', blocksize=round(self.sample_rate*0.05), callback=self.audio_callback)
            self.recorder.start(); self.recording = True; self.start_time = time.monotonic(); self.set_controls(False)
            self.endpoint=SpeechEndpoint(self.start_time,float(self.pause_choice.currentData())); self.last_vad=0
            self.overlay.mascot.set_busy(True,time.monotonic())
            self.wave_overlay.wave_screen=None
            self.wave_overlay.display('Pode falar · uma pausa conclui o ditado',mode='listening')
            if self.overlay.isVisible(): self.overlay.raise_()
            self.test.setText('Concluir agora'); self.state.setText('Ouvindo. Faça uma pausa para concluir automaticamente.')
            self.settings.setValue('backend', self.backend.currentData()); self.settings.setValue('glossary',self.glossary.text())
            self.settings.setValue('microphone',self.mics.currentText()); self.settings.sync()
        except Exception as exc:
            if self.recorder: self.recorder.close(); self.recorder = None
            self.state.setText(f'Não foi possível ativar o microfone: {exc}'); logging.exception('Captura não iniciou')
            QTimer.singleShot(1000,self.ensure_wake)

    def audio_callback(self, data, frames, time_info, flags):
        self.blocks.append(data.copy()); self.level = min(100,int(np.sqrt(np.mean(data*data))*800))
        if flags.input_overflow: self.overflow = True

    def tick(self):
        self.meter.setValue(self.level if self.recording else 0)
        if self.recording:
            now=time.monotonic(); elapsed = int(now-self.start_time)
            self.wave_overlay.set_level(self.level/100); self.wave_overlay.display('',mode='listening')
            if now-self.last_vad >= 0.2 and self.blocks:
                self.last_vad=now
                try:
                    from faster_whisper.vad import get_speech_timestamps, VadOptions
                    tail=np.concatenate(self.blocks[-20:],axis=0).ravel()
                    tail=np.interp(np.arange(0,len(tail),self.sample_rate/16000),np.arange(len(tail)),tail).astype(np.float32)
                    speech=get_speech_timestamps(tail,VadOptions(min_speech_duration_ms=100,min_silence_duration_ms=120,speech_pad_ms=0))
                    recent=any(segment['end']>=len(tail)-2400 for segment in speech)
                    reason=self.endpoint.update(time.monotonic(),recent)
                    if reason: self.stop(no_speech=reason=='no_speech')
                except Exception:
                    logging.exception('Detecção de pausa falhou'); self.stop()

    def set_controls(self, enabled):
        for widget in (self.mics,self.backend,self.language,self.glossary,self.refresh,self.auto_paste,self.pause_choice,self.voice_enabled,self.wake_input,self.save_wake): widget.setEnabled(enabled)

    def stop(self,no_speech=False):
        self.recording = False; self.recorder.stop(); self.recorder.close(); self.recorder = None; self.level = 0
        if no_speech:
            self.blocks=[]; self.finish_empty(no_speech=True); return
        if not self.blocks: self.finish_empty(); return
        samples = np.concatenate(self.blocks,axis=0); self.blocks=[]
        if len(samples) < self.sample_rate * 0.3: self.finish_empty(); return
        filename = ROOT / '.tmp' / f'dit-{uuid.uuid4().hex}.wav'
        try:
            with wave.open(str(filename),'wb') as file:
                file.setparams((1,2,self.sample_rate,0,'NONE','not compressed')); file.writeframes((np.clip(samples,-1,1)*32767).astype('<i2').tobytes())
        except Exception as exc: filename.unlink(missing_ok=True); self.failed(str(exc)); return
        self.processing=True; self.test.setEnabled(False); self.wave_overlay.display('◈ Reconhecendo sua fala…\nProcessamento local'); self.state.setText('Transcrevendo. A janela original receberá o texto se continuar ativa.')
        self.worker=Transcriber(self.engine,filename,self.backend.currentData(),self.language.currentData(),self.glossary.text())
        self.worker.text_ready.connect(self.recognized); self.worker.error.connect(self.failed); self.worker.start()

    def finish_empty(self,no_speech=False):
        self.overlay.mascot.set_busy(False,time.monotonic())
        self.wave_overlay.hide(); self.set_controls(True); self.test.setText('Testar ditado aqui')
        self.state.setText('Nenhuma fala detectada. Aguardando outra chamada.' if no_speech else 'Gravação muito curta. Fale por mais tempo.')
        if no_speech: self.overlay.mascot.show_confused(time.monotonic())
        QTimer.singleShot(500,self.ensure_wake)

    def recognized(self,text,seconds):
        self.overlay.mascot.set_busy(False,time.monotonic())
        if text.strip(): self.output.setPlainText(text)
        self.processing=False; self.set_controls(True); self.test.setEnabled(True); self.test.setText('Testar ditado aqui')
        self.state.setText(f'Concluído em {seconds:.1f}s.' + (' Houve perda de áudio na captura; confira o texto.' if self.overflow else ''))
        self.wave_overlay.set_level(0); self.wave_overlay.display('Ditado concluído',mode='done')
        QTimer.singleShot(1000,lambda:self.wave_overlay.hide() if not self.recording and not self.processing else None)
        QTimer.singleShot(1000,self.ensure_wake)
        if not text.strip(): self.state.setText('Nenhuma fala detectada. Confira a entrada do microfone.'); return
        if self.target and self.auto_paste.isChecked(): self.deliver(text,0)

    def deliver(self,text,attempt,target=None):
        if target is None: target = self.target
        if modifiers_down() and attempt < 20:
            QTimer.singleShot(50,lambda:self.deliver(text,attempt+1,target)); return
        QApplication.clipboard().setText(text)
        if paste_allowed(target, foreground(), self.auto_paste.isChecked()) and not modifiers_down():
            try: paste_shortcut(); self.state.setText('Texto colado na janela original.'); return
            except Exception as exc: self.state.setText(str(exc)); return
        self.state.setText('O foco mudou. Texto copiado; cole manualmente no destino.'); self.tray.showMessage('Claus','Texto copiado. Cole no campo desejado.',QSystemTrayIcon.MessageIcon.Information,3000)

    def failed(self,message):
        self.overlay.mascot.set_busy(False,time.monotonic())
        self.processing=False; self.recording=False; self.set_controls(True); self.test.setEnabled(True); self.test.setText('Testar ditado aqui'); self.wave_overlay.hide(); self.state.setText(message)
        self.tray.showMessage('Claus',message,QSystemTrayIcon.MessageIcon.Warning,5000)
        QTimer.singleShot(1000,self.ensure_wake)

    def closeEvent(self,event): event.ignore(); self.hide()

    def quit_app(self):
        if self.processing or (self.worker and self.worker.isRunning()):
            self.tray.showMessage('Claus','Aguarde o reconhecimento terminar antes de sair.'); return
        self.closing=True
        if not self.stop_wake(): QTimer.singleShot(300,self.quit_app); return
        self.music_monitor.requestInterruption()
        if not self.music_monitor.wait(2000): QTimer.singleShot(300,self.quit_app); return
        if self.recorder: self.recorder.stop(); self.recorder.close()
        self.overlay.close(); self.wave_overlay.close(); self.tray.hide(); QApplication.quit()


# Compatibility for existing integrations importing the original class name.
Escuta = Claus


if __name__ == '__main__':
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    instance_mutex = kernel.CreateMutexW(None,False,'Local\\ClausDitadoDesktop')
    if ctypes.get_last_error() == 183:
        user32.FindWindowW.argtypes = [wintypes.LPCWSTR,wintypes.LPCWSTR]
        user32.FindWindowW.restype = wintypes.HWND
        existing = user32.FindWindowW(None,'Claus — Ditado')
        if existing: user32.ShowWindow(existing,9); user32.SetForegroundWindow(existing)
        sys.exit(0)
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Claus.Ditado.Local')
    app = QApplication(sys.argv); app.setApplicationName('Claus'); app.setApplicationVersion('0.2.0'); app.setStyle('Fusion'); app.setQuitOnLastWindowClosed(False); app.setWindowIcon(app_icon())
    window = Claus(); window.show(); sys.exit(app.exec())
