class Action:
    def __init__(self, domain, service, entity_id, led_matrix_config, **kw):
        self.domain = domain
        self.service = service
        self.entity_id = entity_id
        self.led_matrix_config = led_matrix_config
        self.extra_args = kw
