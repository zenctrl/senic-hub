from unittest import TestCase

from senic_hub.nuimo_app import matrices


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


class MatrixTests(TestCase):
    def test_matrix_with_index(self):
        self.assertEqual(matrices.matrix_with_index(matrices.LIGHT_BULB, 0), LIGHT_BULB1)
        self.assertEqual(matrices.matrix_with_index(matrices.LIGHT_BULB, 1), LIGHT_BULB2)
        self.assertEqual(matrices.matrix_with_index(matrices.LIGHT_BULB, 2), LIGHT_BULB3)
