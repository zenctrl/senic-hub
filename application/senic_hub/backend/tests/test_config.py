import os
from senic_hub.backend.config import crypto_settings


def test_settings_without_secret_creates_key(tmpdir):
    keyfile = os.path.join(tmpdir.strpath, 'secret.key')
    datefile = os.path.join(tmpdir.strpath, 'blubber')
    assert not os.path.exists(keyfile)
    crypto_settings(
        {'__file__': 'testing.ini'},
        crypto_settings_keyfile=keyfile,
        crypto_settings_datafile=datefile,
    )
    assert os.path.exists(keyfile)
