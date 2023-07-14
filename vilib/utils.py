import os

# utils
# =================================================================
def run_command(cmd):
    import subprocess
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('utf-8')
    status = p.poll()
    return status, result

def getIP():
    wlan0 = os.popen("ifconfig wlan0 |awk '/inet/'|awk 'NR==1 {print $2}'").readline().strip('\n')
    eth0 = os.popen("ifconfig eth0 |awk '/inet/'|awk 'NR==1 {print $2}'").readline().strip('\n')

    if wlan0 == '':
        wlan0 = None
    if eth0 == '':
        eth0 = None

    return wlan0,eth0

def check_machine_type():
    import platform
    machine_type = platform.machine()
    if machine_type == "armv7l":
        return 32, machine_type
    elif machine_type == "aarch64":
        return 64, machine_type
    else:
        raise ValueError(f"[{machine_type}] not supported")