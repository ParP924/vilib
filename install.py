#!/usr/bin/env python3
from distutils.log import warn
import os, sys
import platform
import time
import threading
sys.path.append('./vilib')
from version import __version__

errors = []
warns = []

avaiable_options = ['-h', '--help', '--no-dep']

usage = '''
Usage:
    sudo python3 install.py [option]

Options:
               --no-dep    Do not download dependencies
    -h         --help      Show this help text and exit
'''

def run_command(cmd=""):
    import subprocess
    p = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('utf-8')
    status = p.poll()
    return status, result


def check_rpi_model():
    _, result = run_command("cat /proc/device-tree/model |awk '{print $3}'")
    result = result.strip()
    if result == '3':
        return 3
    elif result == '4':
        return 4
    else:
        return None

def check_raspbain_version():
    _, result = run_command("cat /etc/debian_version|awk -F. '{print $1}'")
    return result.strip()

def check_machine_type():
    machine_type = platform.machine()
    if machine_type == "armv7l":
        return 32, machine_type
    elif machine_type == "aarch64":
        return 64, machine_type
    else:
        raise ValueError(f"[{machine_type}] not supported")

def check_python_version():
    import sys
    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro
    return major, minor, micro


rpi_model = check_rpi_model()
python_version = check_python_version()
raspbain_version = check_raspbain_version()
os_bit, machine_type = check_machine_type()


# https://qengineering.eu/install-opencv-4.5-on-raspberry-64-os.html
APT_INSTALL_LIST = [ 
    # install python3-picamera2 : https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
    "python3-picamera2",
    "python3-pyqt5",
    "python3-opengl",
    # install python3-opencv
    "python3-opencv",
    "opencv-data",
    # install ffmpeg
    "ffmpeg", 
    # install mediapipe dependencies
    "libgtk-3-0",
    "libxcb-shm0",
    "libcdio-paranoia-dev", 
    "libsdl2-2.0-0", 
    "libxv1",  
    "libtheora0", 
    "libva-drm2", 
    "libva-x11-2", 
    "libvdpau1", 
    "libharfbuzz0b", 
    "libbluray2", 
    "libatlas-base-dev",
    "libhdf5-103",
    # "libdc1394-22", 
    # "libopenexr23", 
    "libzbar0",
]


PIP_INSTALL_LIST = [
    "Flask",
    "imutils",
    "pyzbar", # pyzbar:one-dimensional barcodes and QR codes
    "pyzbar[scripts]",
    "readchar", # will update setuptools to the latest version
    'protobuf==3.20.0', # mediapipe need 
]


if raspbain_version == "10":
    APT_INSTALL_LIST.append("libopenexr23")
elif raspbain_version == "11":
    APT_INSTALL_LIST.append("libopenexr25")
    

# # https://github.com/tensorflow/tensorflow/blob/v2.5.0/tensorflow/lite/g3doc/guide/python.md#install-tensorflow-lite-for-python
# # select tflite_runtime version
# # https://github.com/google-coral/pycoral/releases/
if python_version[0] == 3:
    if python_version[1] == 7:
        cp = f"cp37-cp37m"
    elif python_version[1] > 7 and python_version[1] <= 10:
        i = python_version[1]
        cp = f"cp3{i}-cp3{i}"
else:
    print('Currently only python 3.7.x, 3.8.x, 3.9.x, 3.10.x are supported.')
    sys.exit(1)
tflite_runtime_link = f"https://github.com/google-coral/pycoral/releases/download/v2.0.0/tflite_runtime-2.5.0.post1-{cp}-linux_{machine_type}.whl"
PIP_INSTALL_LIST.append(tflite_runtime_link)

# main function
def install():

    user_name = os.getlogin()

    options = []
    if len(sys.argv) > 1:
        options = sys.argv[1:]
        for opt in options:
            if opt not in avaiable_options:
                print("Option {} is not found.".format(opt))
                print(usage)
                quit()
        if "-h" in options or "--help" in options:
            print(usage)
            quit()

    print("Start installing vilib %s for user %s"%(__version__ ,user_name))
    print("Python version: %s.%s.%s"%(python_version[0], python_version[1], python_version[2]))
    print("Raspbian version: %s %s"%(raspbain_version, machine_type))
    print("")

    if "--no-dep" not in options:
        print("apt install dependency:")
        do(msg="dpkg configure",
            cmd='sudo dpkg --configure -a')  
        do(msg="update apt-get",
            cmd='sudo apt-get update -y')
        for dep in APT_INSTALL_LIST:
            do(msg="install %s"%dep,
                cmd='sudo apt-get install %s -y'%dep)
        print("pip3 install dependency:")
        for dep in PIP_INSTALL_LIST:
            if dep.endswith('.whl'):
                dep_name = dep.split("/")[-1]
            else:
                dep_name = dep
            do(msg="install %s"%dep_name,
                cmd='sudo pip3 install %s'%dep)

    print("Create workspace")
    if not os.path.exists('/opt'):
        os.mkdir('/opt')
        run_command('sudo chmod 774 /opt')
        run_command('sudo chown -R %s:%s /opt'%(user_name, user_name))
    do(msg="create dir",
        cmd='sudo mkdir -p /opt/vilib'
        + ' && sudo chmod 774 /opt/vilib'
        + ' && sudo chown -R %s:%s /opt/vilib'%(user_name, user_name)
        )
    do(msg="copy workspace",
        cmd='sudo cp -r ./workspace/* /opt/vilib/'
        + ' && sudo chmod 774 /opt/vilib/*'
        + ' && sudo chown -R %s:%s /opt/vilib/*'%(user_name, user_name)
        )
    print("Install vilib python package")
    do(msg="run setup file",
        cmd='sudo python3 setup.py install')
    do(msg="cleanup",
        cmd='sudo rm -rf vilib.egg-info')

    # check errors
    if len(errors) == 0:
        print("Finished")
    else:
        print("\n\nError happened in install process:")
        for error in errors:
            print(error)
        print("Try to fix it yourself, or contact service@sunfounder.com with this message")

    if len(warns) != 0:
        for warn in warns:
            print(warn)


at_work_tip_sw = False
def working_tip():
    char = ['/', '-', '\\', '|']
    i = 0
    global at_work_tip_sw
    while at_work_tip_sw:  
            i = (i+1)%4 
            sys.stdout.write('\033[?25l') # cursor invisible
            sys.stdout.write('%s\033[1D'%char[i])
            sys.stdout.flush()
            time.sleep(0.5)

    sys.stdout.write(' \033[1D')
    sys.stdout.write('\033[?25h') # cursor visible 
    sys.stdout.flush()    
        

def do(msg="", cmd=""):
    print(" - %s... " % (msg), end='', flush=True)
    # at_work_tip start 
    global at_work_tip_sw
    at_work_tip_sw = True
    _thread = threading.Thread(target=working_tip)
    _thread.setDaemon(True)
    _thread.start()
    # process run
    status, result = run_command(cmd)
    # print(status, result)
    # at_work_tip stop
    at_work_tip_sw = False
    while _thread.is_alive():
        time.sleep(0.1)
    # status
    if status == 0 or status == None or result == "":
        print('Done')
    else:
        print('\033[1;35mError\033[0m')
        errors.append("%s error:\n  Status:%s\n  Error:%s" %
                      (msg, status, result))


if __name__ == "__main__":
    try:
        install()
    except KeyboardInterrupt:
        print("Canceled.")
