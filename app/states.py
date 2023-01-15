class State:

    def __init__(self):
        self.LIVE = [True, True]
        self.PAUSE = False
        self.LANGUAGE = "EN"

    def set_state(self, value: bool, LIVE: bool = False, PAUSE: bool = False, index: int = None):
        if LIVE:
            assert index is not None
            self.LIVE[index] = value
        elif PAUSE:
            self.PAUSE = value

    def get_state(self, LIVE: bool = False, PAUSE: bool = False, index: int = None):
        if LIVE:
            assert index is not None
            return self.LIVE[index]
        elif PAUSE:
            return self.PAUSE

    @property
    def language(self):
        return self.LANGUAGE

    def set_language(self, LANG):
        self.LANGUAGE = LANG


state = State()
