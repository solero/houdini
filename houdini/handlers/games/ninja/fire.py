from houdini import IWaddle


class CardJitsuFireLogic(IWaddle):

    room_id = 997

    def __init__(self, waddle):
        super().__init__(waddle)


class FireSenseiLogic(CardJitsuFireLogic):

    def __init__(self, waddle):
        super().__init__(waddle)
