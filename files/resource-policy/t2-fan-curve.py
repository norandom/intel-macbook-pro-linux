#!/usr/bin/python3
"""Earlier cooling via macsmc sysfs; systemd owns lifetime and emergency cleanup."""
import logging
import os
from pathlib import Path
import signal
import socket
import sys
import time

HWMON = Path('/sys/class/hwmon')
CONTROL = Path('/sys/module/macsmc_hwmon/parameters/fan_control')
RUNTIME = Path('/run/t2-fan-curve')
CURVE = ((70, .40), (75, .55), (80, .75), (85, 1.0))
RELEASE_TEMPERATURE = 65
STEP_HYSTERESIS = 2


def fan_target(temperature, minimum, maximum):
    fraction = 0.0
    for threshold, speed in CURVE:
        if temperature < threshold:
            break
        fraction = speed
    return max(minimum, min(maximum, round(maximum * fraction)))


def write(path, value):
    path.write_text(f'{value}\n')


class Controller:
    def __init__(self, hwmon=HWMON, parameter=CONTROL, runtime=RUNTIME):
        self.hwmon, self.parameter = hwmon, parameter
        self.marker = runtime / 'original-control'
        self.manual = False
        self.level = 0
        self.floors = {}
        self.sensors = []
        matches = [p for p in hwmon.glob('hwmon*')
                   if (p / 'name').read_text().strip() == 'macsmc_hwmon']
        if len(matches) != 1:
            raise RuntimeError('Expected exactly one macsmc_hwmon device')
        self.smc = matches[0]
        self.fans = sorted(self.smc.glob('fan*_target'))
        if not self.fans:
            raise RuntimeError('No macsmc fan targets found')

    def start(self):
        # Refuse to compete with an existing manual fan controller.
        if self.marker.exists():
            self.restore()  # Retry our interrupted cleanup before taking control again.
        if self.parameter.read_text().strip() != 'N':
            raise RuntimeError('Manual fan control already enabled by another controller')
        cpu_sensors = []
        for device in self.hwmon.glob('hwmon*'):
            name = (device / 'name').read_text().strip()
            if name == 'coretemp':
                cpu_sensors.extend(sorted(device.glob('temp*_input')))
            elif name == 'amdgpu':
                for label in device.glob('temp*_label'):
                    if label.read_text().strip() in ('edge', 'junction'):
                        self.sensors.append(label.with_name(label.name.replace('_label', '_input')))
        if not cpu_sensors:
            raise RuntimeError('No Intel CPU temperature sensors found')
        self.sensors.extend(cpu_sensors)
        self.temperature()  # Validate monitoring before changing control ownership.
        self.bounds = {}
        for target in self.fans:
            stem = target.name.removesuffix('_target')
            minimum = int((self.smc / f'{stem}_min').read_text())
            maximum = int((self.smc / f'{stem}_max').read_text())
            if not 0 < minimum < maximum:
                raise RuntimeError(f'Invalid fan bounds: {stem}')
            self.bounds[target] = minimum, maximum
        self.marker.write_text('N\n')
        write(self.parameter, 'Y')

    def temperature(self):
        values = [int(p.read_text()) / 1000 for p in self.sensors]
        if not values or any(not 0 < value <= 130 for value in values):
            raise RuntimeError('Missing or invalid CPU/GPU temperature')
        return max(values)

    def step(self):
        temperature = self.temperature()
        if not self.manual and temperature < CURVE[0][0]:
            return temperature
        if self.manual and temperature <= RELEASE_TEMPERATURE:
            for target in self.fans:
                write(target, 0)  # Driver's documented return to SMC automatic mode.
            self.manual = False
            self.floors.clear()
            return temperature
        if not self.manual:
            # Do not undercut the firmware request when taking control.
            self.floors = {p: int(p.read_text()) for p in self.fans}
            self.manual = True
            self.level = 0
        while self.level + 1 < len(CURVE) and temperature >= CURVE[self.level + 1][0]:
            self.level += 1
        while self.level > 0 and temperature <= CURVE[self.level][0] - STEP_HYSTERESIS:
            self.level -= 1
        for target in self.fans:
            minimum, maximum = self.bounds[target]
            rpm = max(fan_target(CURVE[self.level][0], minimum, maximum), self.floors[target])
            write(target, min(maximum, rpm))
        return temperature

    def restore(self):
        if not self.marker.exists():
            return  # We never acquired control; leave another controller alone.
        if self.marker.read_text().strip() != 'N':
            raise RuntimeError('Invalid original-control state; refusing to disable control')
        errors = []
        if self.parameter.read_text().strip() == 'Y':
            for target in self.fans:
                try:
                    write(target, 0)
                except OSError as error:
                    errors.append(str(error))
            if errors:
                raise RuntimeError('Could not restore every fan to automatic: ' + '; '.join(errors))
            # Only disable writes after all fans are confirmed handed back.
            write(self.parameter, 'N')
        self.marker.unlink()


def notify(message):
    address = os.environ.get('NOTIFY_SOCKET')
    if address:
        if address.startswith('@'):
            address = '\0' + address[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(address)
            sock.sendall(message.encode())


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    controller = Controller()
    if sys.argv[1:] == ['restore']:
        controller.restore()
        return
    if sys.argv[1:]:
        raise RuntimeError('usage: t2-fan-curve [restore]')
    stopping = False

    def stop(_signal, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        controller.start()
        controller.step()
        notify('READY=1')
        logging.info('Earlier cooling active: full fans at 85 C; CPU power policy unchanged')
        while not stopping:
            temperature = controller.step()
            notify(f'WATCHDOG=1\nSTATUS=CPU/GPU maximum {temperature:.1f} C')
            time.sleep(1)
    finally:
        controller.restore()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        logging.exception('Fan policy failed; systemd cleanup will retry SMC handover')
        sys.exit(1)
