"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""


class LedStrip():

    def __init__(self, strip):
        self.strip = strip

    def get(self, data):
        try:
            self.strip.turn_on(data)
        except Exception as e:
            return {'message': str(e)}, 400
        return {'message': 'scheduled'}

    def post(self, data):
        return {'message': 'unimplemted'}


class LedStripTest():

    def __init__(self, strip):
        self.strip = strip

    def post(self, data):
        # In case of just test strip
        try:
            self.strip.test(**data)
            return {'message': 'success'}
        except Exception as e:
            return {'message': str(e)}, 400

    def put(self, data):
        self.post(data)
