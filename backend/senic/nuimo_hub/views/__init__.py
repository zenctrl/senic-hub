import colander


class ResourceBase(object):

    def __init__(self, context, request):
        self.request = request
        self.context = context


class NonableMapping(colander.Mapping):

    def deserialize(self, node, cstruct):
        if cstruct is colander.null or cstruct is None:
            return colander.null
        else:
            return cstruct
