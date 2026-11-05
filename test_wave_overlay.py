import unittest
import ctypes
from ctypes import wintypes
from unittest.mock import patch
from PySide6.QtCore import Qt, QPointF, QEvent
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication
from listening_overlay import ListeningOverlay, REFERENCE, cross_path, motion_frame


class WaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.app=QApplication.instance() or QApplication([])

    def test_original_wave_frames_and_cross_geometry_are_preserved(self):
        self.assertEqual(len(REFERENCE['motion']),98)
        self.assertEqual(motion_frame(0),REFERENCE['motion'][0])
        self.assertEqual(len(motion_frame(1.25)),23)
        self.assertAlmostEqual(cross_path().boundingRect().width(),31.106,places=2)

    def test_configurable_sizes_and_vertical_position_preserve_mascot_location(self):
        overlay=ListeningOverlay(); overlay.restore_position(100,100)
        try:
            overlay.configure(150,125,0,False); overlay.display('',mode='waiting')
            self.assertEqual(overlay.size().toTuple(),(192,180))
            self.assertEqual((overlay.x(),overlay.y()),(100,100))
            overlay.display('',mode='listening'); area=overlay.screen().availableGeometry()
            self.assertEqual(overlay.size().toTuple(),(650,158))
            self.assertEqual(overlay.y(),area.top())
            overlay.configure(150,125,100,False)
            self.assertEqual(overlay.y()+overlay.height(),area.y()+area.height())
            overlay.display('',mode='waiting')
            self.assertEqual((overlay.x(),overlay.y()),(100,100))
        finally: overlay.hide(); overlay.animation.stop(); overlay.deleteLater()

    def test_transparent_wave_has_no_panel_or_gif_background(self):
        overlay=ListeningOverlay()
        try:
            overlay.configure(100,100,50,False); overlay.display('',mode='listening')
            self.assertEqual(overlay.grab().toImage().pixelColor(30,20).alpha(),255)
            overlay.configure(100,100,50,True)
            self.assertEqual(overlay.grab().toImage().pixelColor(30,20).alpha(),0)
        finally: overlay.hide(); overlay.animation.stop(); overlay.deleteLater()

    def test_animation_resources_and_click_through_window_are_valid(self):
        overlay=ListeningOverlay()
        self.assertTrue(overlay.movie.isValid())
        self.assertFalse(overlay.windowFlags() & Qt.WindowType.WindowTransparentForInput)
        self.assertTrue(overlay.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus)
        overlay.set_wake_phrase('computador'); self.assertEqual(overlay.wake_phrase,'computador')
        overlay.animation.stop(); overlay.deleteLater()

    def test_hidden_mascot_still_allows_wave_and_keeps_position(self):
        overlay=ListeningOverlay(); overlay.restore_position(100,100)
        overlay.set_mascot_hidden(True); overlay.display('',mode='waiting')
        self.assertFalse(overlay.isVisible())
        overlay.display('',mode='listening')
        self.assertTrue(overlay.isVisible())
        self.assertTrue(overlay.windowFlags() & Qt.WindowType.WindowTransparentForInput)
        overlay.display('',mode='waiting'); self.assertFalse(overlay.isVisible())
        self.assertEqual((overlay.x(),overlay.y()),(100,100))
        overlay.set_mascot_hidden(False); self.assertTrue(overlay.isVisible())
        overlay.hide(); overlay.animation.stop(); overlay.deleteLater()

    def test_windows_replaces_mascot_silhouette_with_full_wave_region(self):
        from PySide6.QtTest import QTest
        user32=ctypes.WinDLL('user32'); gdi32=ctypes.WinDLL('gdi32')
        user32.GetWindowRgn.argtypes=[wintypes.HWND,wintypes.HANDLE]
        gdi32.CreateRectRgn.restype=wintypes.HANDLE
        gdi32.GetRgnBox.argtypes=[wintypes.HANDLE,ctypes.POINTER(wintypes.RECT)]
        gdi32.DeleteObject.argtypes=[wintypes.HANDLE]
        overlay=ListeningOverlay()
        try:
            for mode,percent in [('waiting',100),('listening',150),('processing',150),('done',150),('waiting',200),('listening',50)]:
                overlay.configure(percent,percent,97,False)
                overlay.display('',mode=mode); QTest.qWait(40)
                region=gdi32.CreateRectRgn(0,0,0,0); box=wintypes.RECT()
                try:
                    result=user32.GetWindowRgn(int(overlay.winId()),region)
                    gdi32.GetRgnBox(region,ctypes.byref(box))
                finally: gdi32.DeleteObject(region)
                if mode=='waiting':
                    self.assertGreater(result,0)
                    self.assertLess(box.right-box.left,overlay.width())
                elif result:
                    self.assertEqual((box.left,box.top,box.right,box.bottom),(0,0,overlay.width(),overlay.height()),mode)
        finally:
            overlay.hide(); overlay.animation.stop(); overlay.deleteLater()

    def test_drag_saves_position_and_click_opens_menu(self):
        overlay=ListeningOverlay(); overlay.restore_position(100,100); overlay.display('',mode='waiting')
        saved=[]; overlay.position_changed.connect(lambda x,y:saved.append((x,y)))
        def event(kind,local,global_pos,button,buttons):
            return QMouseEvent(kind,QPointF(*local),QPointF(*global_pos),button,buttons,Qt.KeyboardModifier.NoModifier)
        left=Qt.MouseButton.LeftButton; none=Qt.MouseButton.NoButton
        with patch.object(overlay,'open_menu') as menu:
            overlay.mousePressEvent(event(QEvent.Type.MouseButtonPress,(64,60),(164,160),left,left))
            overlay.mouseMoveEvent(event(QEvent.Type.MouseMove,(64,60),(364,310),none,left))
            self.assertTrue(overlay.mascot.dragging)
            overlay.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease,(64,60),(364,310),left,none))
            self.assertEqual(saved,[(300,250)]); menu.assert_not_called()
            overlay.mousePressEvent(event(QEvent.Type.MouseButtonPress,(64,60),(364,310),left,left))
            overlay.mouseReleaseEvent(event(QEvent.Type.MouseButtonRelease,(64,60),(364,310),left,none))
            menu.assert_called_once()
        before=(overlay.x(),overlay.y()); overlay.animate()
        self.assertEqual((overlay.x(),overlay.y()),before)
        overlay.hide(); overlay.animation.stop(); overlay.deleteLater()


if __name__ == '__main__': unittest.main()
