import ctypes
import unittest
import tempfile
from pathlib import Path
from desktop_engine import gpu_command, paste_allowed
from desktop_windows import INPUT


class DesktopTests(unittest.TestCase):
    def test_appearance_dialog_saves_and_restores_sizes_height_and_transparency(self):
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QApplication
        from appearance import AppearanceDialog, apply_saved_appearance
        from listening_overlay import ListeningOverlay
        app=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            settings=QSettings(str(Path(directory)/'settings.ini'),QSettings.Format.IniFormat)
            overlay=ListeningOverlay(); dialog=AppearanceDialog(settings,overlay)
            try:
                dialog.controls['mascot_size'].setValue(170); dialog.controls['wave_size'].setValue(80)
                dialog.controls['wave_height'].setValue(25); dialog.transparent.setChecked(True)
                dialog.toggle_preview(True); self.assertTrue(dialog.preview.isVisible())
                self.assertEqual(dialog.preview.size().toTuple(),(416,101))
                restored=ListeningOverlay()
                try:
                    apply_saved_appearance(QSettings(settings.fileName(),QSettings.Format.IniFormat),restored)
                    self.assertEqual(restored.mascot_size(),(218,204))
                    self.assertEqual((restored.wave_percent,restored.wave_height,restored.transparent_wave),(80,25,True))
                finally: restored.animation.stop(); restored.deleteLater()
            finally:
                dialog.reject(); overlay.animation.stop(); overlay.deleteLater(); dialog.deleteLater()

    def test_tray_restores_hidden_mascot_and_saves_preferences(self):
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QApplication, QMainWindow, QCheckBox, QSystemTrayIcon
        from desktop import Escuta
        from listening_overlay import ListeningOverlay
        app=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            window=Escuta.__new__(Escuta); QMainWindow.__init__(window)
            window.settings=QSettings(str(Path(directory)/'settings.ini'),QSettings.Format.IniFormat)
            window.overlay=ListeningOverlay(); window.voice_enabled=QCheckBox(); window.build_tray()
            window.overlay.display('',mode='waiting'); window.mascot_action.setChecked(False)
            self.assertFalse(window.overlay.isVisible())
            self.assertFalse(window.settings.value('mascot_visible',type=bool))
            window.tray_activated(QSystemTrayIcon.ActivationReason.Trigger)
            self.assertTrue(window.overlay.isVisible())
            self.assertTrue(window.settings.value('mascot_visible',type=bool))
            window.save_mascot_position(240,180)
            reopened=QSettings(window.settings.fileName(),QSettings.Format.IniFormat)
            self.assertEqual((reopened.value('mascot_x',type=int),reopened.value('mascot_y',type=int)),(240,180))
            window.overlay.hide(); window.overlay.animation.stop(); window.tray.hide()
            window.overlay.deleteLater(); window.deleteLater()

    def test_paste_requires_the_original_target_to_still_be_active(self):
        self.assertTrue(paste_allowed(123, 123, True))
        self.assertFalse(paste_allowed(123, 456, True))
        self.assertFalse(paste_allowed(0, 0, True))
        self.assertFalse(paste_allowed(123, 123, False))

    def test_gpu_command_uses_explicit_portuguese_and_local_model(self):
        args = gpu_command(Path('audio com espaços.wav'), Path('resultado'), 'pt', 'nomes')
        self.assertIn('audio com espaços.wav', args)
        self.assertEqual(args[args.index('-l') + 1], 'pt')
        self.assertNotIn('-ng', args)
        self.assertEqual(args[args.index('--prompt') + 1], 'nomes')

    def test_windows_input_layout_matches_64_bit_sendinput(self):
        self.assertEqual(ctypes.sizeof(INPUT), 40)


if __name__ == '__main__':
    unittest.main()
