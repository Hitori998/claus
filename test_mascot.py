import unittest
from PySide6.QtCore import QPointF
from mascot import Mascot, blink_openness, clamp_position, eye_path


class MascotTests(unittest.TestCase):
    def test_blink_closes_and_reopens_smoothly(self):
        self.assertEqual(blink_openness(-1),1)
        self.assertLess(blink_openness(0.09),0.06)
        self.assertAlmostEqual(blink_openness(0.18),1)

    def test_drag_position_is_limited_to_the_chosen_monitor(self):
        self.assertEqual(clamp_position((2000,1100),(0,0,1920,1080),(128,120)),(1792,960))
        self.assertEqual(clamp_position((-2000,-5),(-1920,0,0,1080),(128,120)),(-1920,0))

    def test_drag_expression_has_the_flat_upper_lid_from_reference(self):
        normal=eye_path(0,0,1,0); sleepy=eye_path(0,0,1,1)
        self.assertTrue(normal.contains(QPointF(0,-40)))
        self.assertFalse(sleepy.contains(QPointF(0,-40)))
        self.assertTrue(sleepy.contains(QPointF(0,30)))
        self.assertLess(sleepy.boundingRect().height(),normal.boundingRect().height()*0.6)

    def test_drag_expression_animates_in_and_releases_smoothly(self):
        mascot=Mascot(0); mascot.next_squint=999
        mascot.set_dragging(True,0); mascot.update(0.1)
        self.assertGreater(mascot.drag_mix,0); self.assertLess(mascot.drag_mix,1)
        mascot.update(1); self.assertGreater(mascot.drag_mix,0.9)
        mascot.set_dragging(False,1); mascot.update(3)
        self.assertLess(mascot.drag_mix,0.1)


if __name__ == '__main__': unittest.main()
