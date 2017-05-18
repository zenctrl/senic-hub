from math import ceil


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

STATION1 = \
    "         " \
    "     *   " \
    "    **   " \
    "   * *   " \
    "     *   " \
    "     *   " \
    "     *   " \
    "     *   " \
    "         "

STATION2 = \
    "         " \
    "   ***   " \
    "      *  " \
    "      *  " \
    "   ***   " \
    "  *      " \
    "  *      " \
    "   ***   " \
    "         "

STATION3 = \
    "         " \
    "   ***   " \
    "      *  " \
    "      *  " \
    "    **   " \
    "      *  " \
    "      *  " \
    "   ***   " \
    "         "


def progress_bar(progress):
    """
    Generates a light bar matrix to display volume / brightness level.

    :param progress: value between 0..1
    """
    dots = list(" " * 81)
    num_dots = ceil(round(progress, 3) * 9)
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
