from subprocess import Popen, PIPE
import platform as pf

class Adb:
    # 平台判断
    if pf.system() == 'Windows':
        adb_path = "./platform-tools/adb.exe"
    else:
        adb_path = "./platform-tools/adb"

    def __init__(self, serial=None):
        if serial:
            self.serial = serial

    @classmethod
    def have_device(cls) -> bool:
        """
        是否存在已连接设备

        :return:
        """
        return len(cls.get_device_list()) != 0

    @classmethod
    def get_device_list(cls, *args, all: bool = False) -> list:
        """
        获取设备列表
        :return: tuple(序列号, 状态, 连接)
        """
        cmd = [cls.adb_path, 'devices', '-l']
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        devices = []
        for line in stdout.splitlines():
            line = line.decode('utf-8')
            if line.find("product") != -1:
                if all:
                    devices.append((
                        line.split()[0].strip(),
                        line.split()[1].strip(),
                        line.split()[2].strip(),
                        line.split()[3].strip(),
                        line.split()[4].strip())
                    )
                else:
                    devices.append((line.split()[0].strip(), line.split()[1].strip(), line.split()[2].strip()))

        return devices

    @classmethod
    def if_device_online(cls, serial) -> bool:
        """
        判断设备是否在线

        :param serial:
        :return:
        """
        cmd = [cls.adb_path, '-s', serial, 'get-state']
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        return stdout.strip() == b'device'

    def verify_device(self) -> bool:
        """
        验证当前设备是否与本线程设备一致

        :return:
        """
        return self.get_device_id() == self.device_id

    def command(self, *args):
        if self.verify_device():
            raise Exception("未检测到设备")
        cmd = [self.adb_path]
        cmd.extend(args)
        return Popen(cmd, stdout=PIPE, stderr=PIPE)

    def get_command_output(self, *args):
        cmd = [self.adb_path]
        cmd.extend(args)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        return stdout.strip().decode("utf-8")

    def shell(self, *args):
        if self.verify_device():
            raise Exception("未检测到设备")
        cmd = [self.adb_path]
        cmd.extend(['shell'])
        cmd.extend(args)
        return Popen(cmd, stdout=PIPE, stderr=PIPE)

    def connect(self, ip):
        p = self.command('connect', ip)
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        return stdout.decode("utf-8").strip()

    def auto_connect(self):
        if self.have_device():
            return
        for ip in self.get_device_list():
            self.connect(ip[0])
            if self.have_device():
                return

    def get_screen_size(self) -> tuple:
        p = self.shell('wm', 'size')
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        size = stdout.decode("utf-8").strip().split()[2].split('x')
        return int(size[0]), int(size[1])

    @property
    def screen_size(self):
        return self.get_screen_size()

    def get_device_id(self):
        p = self.command('get-serialno')
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)
        return stdout.decode("utf-8").strip()

    @property
    def device_id(self):
        return self.get_device_id()

    def kill_server(self):
        p = self.command('kill-server')
        stdout, stderr = p.communicate()
        if p.returncode != 0:
            raise Exception(stderr)

    def __del__(self):
        self.kill_server()