LIGHT_OFF = \
    "         " \
    "         " \
    "         " \
    "    *    " \
    "   ***   " \
    "    *    " \
    "         " \
    "         " \
    "         "

LIGHT_ON = \
    "    *    " \
    " *     * " \
    "         " \
    "    *    " \
    "*  ***  *" \
    "    *    " \
    "         " \
    " *     * " \
    "    *    "

LIGHT_BULB = \
    "   ***   "  \
    "  *   *  "  \
    "  *   *  "  \
    "  * * *  "  \
    "  * * *  "  \
    "  * * *  "  \
    "   ***   "  \
    "   ***   "  \
    "         "

PAUSE = \
    "         " \
    "  ## ##  " \
    "  ## ##  " \
    "  ## ##  " \
    "  ## ##  " \
    "  ## ##  " \
    "  ## ##  " \
    "  ## ##  " \
    "         "

PLAY = \
    "         " \
    "   #     " \
    "   ##    " \
    "   ###   " \
    "   ####  " \
    "   ###   " \
    "   ##    " \
    "   #     " \
    "         "

MUSIC_NOTE = \
    "  #####  " \
    "  #####  " \
    "  #   #  " \
    "  #   #  " \
    "  #   #  " \
    " ##  ##  " \
    "### ###  " \
    " #   #   " \
    "         "

SHUFFLE = \
    "         " \
    "         " \
    " ##   ## " \
    "   # #   " \
    "    #    " \
    "   # #   " \
    " ##   ## " \
    "         " \
    "         "

ERROR = \
    "         " \
    "         " \
    "  *   *  " \
    "   * *   " \
    "    *    " \
    "   * *   " \
    "  *   *  " \
    "         " \
    "         "

NEXT_SONG = \
    "         " \
    "         " \
    "   #  #  " \
    "   ## #  " \
    "   ####  " \
    "   ## #  " \
    "   #  #  " \
    "         " \
    "         "

PREVIOUS_SONG = \
    "         " \
    "         " \
    "  #  #   " \
    "  # ##   " \
    "  ####   " \
    "  # ##   " \
    "  #  #   " \
    "         " \
    "         "

POWER_OFF = \
    "         " \
    "         " \
    "   ###   " \
    "  #   #  " \
    "  #   #  " \
    "  #   #  " \
    "   ###   " \
    "         " \
    "         "


LETTER_W = \
    "         " \
    " #     # " \
    " #     # " \
    " #     # " \
    " #     # " \
    " #  #  # " \
    " #  #  # " \
    "  ## ##  " \
    "         "


def light_bar(max_value, value):
    """
    Generates a light bar matrix to display volume / brightness level.

    """
    dots = list(" " * 81)
    num_dots = int(value / max_value * 9)
    while num_dots > 0:
        dots[81 - ((num_dots - 1) * 9 + 5)] = "*"
        num_dots -= 1

    return "".join(dots)


def matrix_with_index(matrix, index):
    """
    Adds index of the component in the component list to the top right
    corner of the component matrix.

    """
    dots = list(matrix)

    while index >= 0:
        dots[index * 9 + 8] = '*'
        index -= 1

    return "".join(dots)
