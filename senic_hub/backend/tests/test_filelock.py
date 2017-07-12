from os import remove
from shutil import copyfile
from tempfile import mkstemp

from senic_hub.backend.lockfile import open_locked


def test_file_can_be_locked_and_read(settings):
    file = settings['nuimo_mac_address_filepath']
    with open_locked(file, 'r') as f:
        assert f.readline().strip() == 'AA:BB:CC:DD:EE:FF'


def test_file_can_be_locked_and_read_and_written(settings):
    file = mkstemp()[1]
    copyfile(settings['nuimo_mac_address_filepath'], file)
    try:
        with open_locked(file, 'r+') as f:
            assert f.readline().strip() == 'AA:BB:CC:DD:EE:FF'
            f.seek(0)
            f.truncate()
            f.write("Pablo Picasso: I don't search, I find")

        with open(file, 'r') as f:
            assert f.readline().strip() == "Pablo Picasso: I don't search, I find"
    finally:
        remove(file)
