class Output(object):
    called = None

    def __init__(self, *args):
        Output.called = args
