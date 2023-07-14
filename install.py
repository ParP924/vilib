#!/usr/bin/env python3
from distutils.log import warn
import os, sys
import time
import threading

# version
# =================================================================
sys.path.append('./vilib')
user_name = os.getlogin()
from version import __version__
print("Start installing vilib %s for user %s"%(__version__ ,user_name))

# define color print
# =================================================================
def warn(msg, end='\n', file=sys.stdout, flush=False):
    print(f'\033[0;33m{msg}\033[0m', end=end, file=file, flush=flush)

def error(msg, end='\n', file=sys.stdout, flush=False):
    print(f'\033[0;31m{msg}\033[0m', end=end, file=file, flush=flush)

# run_command
# =================================================================
def run_command(cmd=""):
    import subprocess
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = p.stdout.read().decode('utf-8')
    status = p.poll()
    return status, result

# check if run as root
# =================================================================
if os.geteuid() != 0:
    warn("Script must be run as root. Try \"sudo python3 install.py\".")
    sys.exit(1)

# check machine_type
# =================================================================
'''
# import platform
# machine_type = platform.machine() 
latest bullseye uses a 64-bit kernel
This method is no longer applicable, the latest raspbian will uses 64-bit kernel 
(kernel 6.1.x) by default, "uname -m" shows "aarch64", 
but the system is still 32-bit.
'''
# platform architecture
status, machine_type = run_command("uname -m")
machine_type = machine_type.replace('\n', '')
if status != 0:
    machine_type = "unknown"
if machine_type == "unknown" or machine_type not in ["armv7l", "aarch64"]:
    error(f"Platform [{machine_type}] is not supported.")
    sys.exit(1)

# system bit
status, os_bit = run_command("getconf LONG_BIT")
if status != 0:
    machine_type = "unknown"
os_bit = int(os_bit)

if os_bit == 32:
    machine_type = "armv7l"
elif os_bit == 64:
    machine_type = "aarch64"
    warn(f"The vilib {__version__} only supports 32-bit systems, please change to Please \"64bit\" branch.")
    print(f"Try:\n  git fetch && git checkout 64bit ")
    sys.exit(1)

# global variables defined
# =================================================================
errors = []

avaiable_options = ['-h', '--help', '--no-dep']

usage = '''
Usage:
    sudo python3 install.py [option]

Options:
               --no-dep    Do not download dependencies
    -h         --help      Show this help text and exit
'''

# utils
# =================================================================
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
    _thread.daemon = True
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

def check_python_version():
    import sys
    major = sys.version_info.major
    minor = sys.version_info.minor
    micro = sys.version_info.micro
    return major, minor, micro

# print system and hardware information
# =================================================================
rpi_model = check_rpi_model()
python_version = check_python_version()
raspbain_version = check_raspbain_version()

print(f"Python version: {python_version[0]}.{python_version[1]}.{python_version[2]}")
print(f"Raspbian version: {raspbain_version}")
print(f"System platform: {machine_type} ({os_bit}bit)")
print("")

# Dependencies list installed with apt
# =================================================================
APT_INSTALL_LIST = [ 
    # install python3-picamera : https://picamera.readthedocs.io/en/release-1.13/install.html
    "python3-picamera",
    # install python3-opencv: https://docs.opencv.org/4.x/d2/de6/tutorial_py_setup_in_ubuntu.html
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
    "libzbar0",
]

if raspbain_version == "10":
    APT_INSTALL_LIST.append("libopenexr23")
elif raspbain_version == "11":
    APT_INSTALL_LIST.append("libopenexr25")

# Dependencies list installed with pip3
# =================================================================
PIP_INSTALL_LIST = [
    "Flask",
    "imutils",
    "pyzbar", # pyzbar:one-dimensional barcodes and QR codes
    "pyzbar[scripts]",
    "readchar", # will update setuptools to the latest version
    'protobuf>=3.20.0', # mediapipe need 
]

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
# =================================================================
def install():
    options = []
    if len(sys.argv) > 1:
        options = sys.argv[1:]
        for opt in options:
            if opt not in avaiable_options:
                print("Option {} is not found.".format(opt))
                print(usage)
                sys.exit(0)
        if "-h" in options or "--help" in options:
            print(usage)
            sys.exit(0)

    if "--no-dep" not in options:
        # install dependencies with apt
        print("apt install dependency:")
        do(msg="dpkg configure",
            cmd='dpkg --configure -a')  
        do(msg="update apt-get",
            cmd='apt-get update -y')
        for dep in APT_INSTALL_LIST:
            do(msg=f"install {dep}",
                cmd=f'apt-get install {dep} -y')
        # install dependencies with pip
        print("pip3 install dependency:")
        for dep in PIP_INSTALL_LIST:
            if dep.endswith('.whl'):
                dep_name = dep.split("/")[-1]
            else:
                dep_name = dep
            do(msg=f"install {dep_name}",
                cmd=f'pip3 install {dep}')

    print("Create workspace")
    if not os.path.exists('/opt'):
        os.mkdir('/opt')
        run_command('chmod 774 /opt')
        run_command(f'chown -R {user_name}:{user_name} /opt')
    do(msg="create dir",
        cmd='mkdir -p /opt/vilib'
        + ' && chmod 774 /opt/vilib'
        + f' && chown -R {user_name}:{user_name} /opt/vilib'
        )
    do(msg="copy workspace",
        cmd='cp -r ./workspace/* /opt/vilib/'
        + ' && chmod 774 /opt/vilib/*'
        + f' && chown -R {user_name}:{user_name} /opt/vilib/*'
        )
    print("Install vilib python package")
    do(msg="run setup file",
        cmd='python3 setup.py install')
    do(msg="cleanup",
        cmd='rm -rf vilib.egg-info')

    # check errors
    if len(errors) == 0:
        print("Finished")
    else:
        print("\n\nError happened in install process:")
        for error in errors:
            print(error)
        print("Try to fix it yourself, or contact service@sunfounder.com with this message")


if __name__ == "__main__":
    try:
        install()
    except KeyboardInterrupt:
        print("\n\nCanceled.")
    finally:
        sys.stdout.write(' \033[1D')
        sys.stdout.write('\033[?25h') # cursor visible 
        sys.stdout.flush()