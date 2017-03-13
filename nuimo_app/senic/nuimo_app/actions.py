class Action:
    def __init__(self, domain, service, entity_ids, led_matrix_config, **kw):
        self.domain = domain
        self.service = service
        self.entity_ids = entity_ids
        self.led_matrix_config = led_matrix_config
        self.extra_args = kw

        self.service_call_results = {x: None for x in self.entity_ids}  # entity_id: Bool/None

    def is_complete(self):
        """Returns True if action was executed for all entities."""
        return all(x is not None for x in self.service_call_results.values())

    def is_successful(self):
        """Returns True if all entities were successfuly updated."""
        return all(self.service_call_results.values())

    def entity_updated(self, entity_id, success):
        self.service_call_results[entity_id] = success
