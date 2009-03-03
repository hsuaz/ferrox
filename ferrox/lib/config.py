class Config:
    def __init__(self):
        self.config = {}

    def readdb(self, dbo):
        data = dbo.get_all()
        for row in data:
            self.config[row.section, row.name] = row.value
        return self

    def get(self, *args):
        if len(args) == 1:
            section = 'global'
            name    = args[0]
        else:
            section = args[0]
            name    = args[1]
        try:
            value = self.config[section, name]
        except KeyError:
            return None
        return value

    def set(self, *args):
        if len(args) == 2:
            section = 'global'
            name    = args[0]
            value   = args[1]
        else:
            section = args[0]
            name    = args[1]
            value   = args[2]
        self.config[section, name] = value
        return self
