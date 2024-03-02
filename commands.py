class Commands():
    """
    Base Commands Class
    """
    def __init__(self, command):
        self.command = command
        self.data = None
        self.status = "Init"

        if self.command == "admin":
            self.admin()

        elif self.command == "one":
            self.one()

        elif self.command == "two":
            self.two()

        else:
            self.unknown()

    def admin(self):
        self.data = "Admined"
        self.status = "Finished"

    def one(self):
        self.data = "Oned"
        self.status = "Finished"

    def two(self):
        self.data = "Twoed"
        self.status = "Finished"

    def unknown(self):
        self.data = "Unknown command"
        self.status = "Finished"
