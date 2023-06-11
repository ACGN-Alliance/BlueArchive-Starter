from subprocess import Popen, PIPE


class Adb:
    adb_path = "./platform-tools/adb.exe"

    def __init__(self, serial=None):
        pass

    @classmethod
    def have_device(cls) -> bool:
        return len(cls.get_device_list()) != 0

    @classmethod
    def get_device_list(cls) -> list:
        cmd = [cls.adb_path, 'devices', '-l']
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        devices = []
        for line in stdout.splitlines():
            line = line.decode('utf-8')
            if line.find("product") != -1:
                devices.append((line.split()[0].strip(), line.split()[1].strip()))

        return devices

    def command(self, *args):
        cmd = [self.adb_path]
        cmd.extend(args)
        return Popen(cmd, stdout=PIPE, stderr=PIPE)

    def shell(self, *args):
        cmd = [self.adb_path]
        cmd.extend(['shell'])
        cmd.extend(args)
        return Popen(cmd, stdout=PIPE, stderr=PIPE)

    def getprop(self, prop):
        p = self.shell('getprop', prop)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        return stdout.strip()

    def setprop(self, prop, value):
        p = self.shell('setprop', prop, value)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        return stdout.strip()

    def push(self, src, dst):
        p = self.command('push', src, dst)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)

    def kill_server(self):
        p = self.command('kill-server')
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)

    def __del__(self):
        self.kill_server()


if __name__ == '__main__':
    adb = Adb()
    print(adb.get_device_list())