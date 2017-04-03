from unittest import TestCase

from senic_hub.nuimo_app.hass import HomeAssistant


class TestHomeAssistant(TestCase):
    def test_find_state_entity_state(self):
        ha = HomeAssistant("ws://test")

        states = [
            {"entity_id": "eid1"},
            {"entity_id": "eid2"},
        ]
        self.assertEqual(ha.find_entity_state(states, "eid2"), {"entity_id": "eid2"})
        self.assertEqual(ha.find_entity_state(states, "eid4"), None)
