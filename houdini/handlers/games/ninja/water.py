from houdini import IWaddle


class CardJitsuWaterLogic(IWaddle):

    room_id = 995

    def __init__(self, waddle):
        super().__init__(waddle)


class WaterSenseiLogic(CardJitsuWaterLogic):

    def __init__(self, waddle):
        super().__init__(waddle)
