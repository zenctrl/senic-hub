from unittest import TestCase

from senic.nuimo_app import icons


LIGHT_BULB1 = \
    "   ***  *"  \
    "  *   *  "  \
    "  *   *  "  \
    "  * * *  "  \
    "  * * *  "  \
    "  * * *  "  \
    "   ***   "  \
    "   ***   "  \
    "         "

LIGHT_BULB2 = \
    "   ***  *"  \
    "  *   * *"  \
    "  *   *  "  \
    "  * * *  "  \
    "  * * *  "  \
    "  * * *  "  \
    "   ***   "  \
    "   ***   "  \
    "         "

LIGHT_BULB3 = \
    "   ***  *"  \
    "  *   * *"  \
    "  *   * *"  \
    "  * * *  "  \
    "  * * *  "  \
    "  * * *  "  \
    "   ***   "  \
    "   ***   "  \
    "         "


class IconTests(TestCase):
    def test_icon_with_index(self):
        self.assertEqual(icons.icon_with_index(icons.LIGHT_BULB, 0), LIGHT_BULB1)
        self.assertEqual(icons.icon_with_index(icons.LIGHT_BULB, 1), LIGHT_BULB2)
        self.assertEqual(icons.icon_with_index(icons.LIGHT_BULB, 2), LIGHT_BULB3)
