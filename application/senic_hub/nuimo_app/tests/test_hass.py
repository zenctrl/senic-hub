from unittest import TestCase
from unittest.mock import MagicMock

from senic_hub.nuimo_app.hass import HAListener


class TestHAListener(TestCase):
    def test_find_state_entity_state(self):
        connection = MagicMock()
        listener = HAListener("ws://localhost:8123", connection)

        states = [
            {"entity_id": "eid1"},
            {"entity_id": "eid2"},
        ]
        self.assertEqual(listener.find_entity_state(states, "eid2"), {"entity_id": "eid2"})
        self.assertEqual(listener.find_entity_state(states, "eid4"), None)
