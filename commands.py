import subprocess


class Commands():
    """ Base Commands Class """

    def __init__(self, command):
        self.command = command
        self.data = None
        self.status = "Init"

        if self.command == "admin":
            self.admin()

        elif self.command == "speedtest":
            self.speedtest()

        elif self.command == "two":
            self.two()

        else:
            self.unknown()

    def admin(self):
        self.data = "Admined"
        self.status = "Finished"

    def speedtest(self):
        self.data = "Oned"
        self.status = "Finished"

    def two(self):
        self.data = "Twoed"
        self.status = "Finished"

    def unknown(self):
        self.data = "Unknown command"
        self.status = "Finished"


def exec_command(*args, timeout=120):
    """ Execute command and return returncode, stdout, stderr """

    try:
        result = subprocess.Popen(*args,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True)
        output = result.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        return ("No response from executed command after %f sec" % timeout)
    except Exception:
        raise
    else:
        return (result.returncode, output[0], output[1])


def check_inet_speed():
    """ Check Internet connection speed  """
    pass
