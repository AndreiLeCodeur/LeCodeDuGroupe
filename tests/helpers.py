import copy


class ScriptedInput():
    def __init__(self, keys):
        self.keys = iter(keys)
        self.reads = 0

    def read_key(self):
        self.reads+=1
        try:
            return next(self.keys)
        except StopIteration:
            raise AssertionError("Input script exhausted")


class RecordingRenderer():
    """Fake renderer: keeps every state it receives, never opens a window."""
    def __init__(self):
        self.states = []
        self.started = False
        self.closed = False

    def start(self):
        self.started = True

    def update_render(self, json_state):
        # deepcopy: the engine reuses some objects (extras...), we want a snapshot
        self.states.append(copy.deepcopy(json_state))

    def close(self):
        self.closed = True
