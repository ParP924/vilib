#!/bin/bash

# Core dependencies
sudo apt-get install -y build-essential
sudo apt-get install -y git python3-pip python3-setuptools python3-smbus
sudo apt-get install -y pkg-config zip unzip
pip3 install meson
sudo apt-get install -y libyaml-dev python3-yaml python3-ply python3-jinja2

# Recommended for IPA module signing
sudo apt-get install -y libssl-dev openssl libdw-dev

# Optional for gstreamer
sudo apt-get install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev

# For Python bindings
sudo apt-get install -y libpython3-dev pybind11-dev libdrm-dev

# Optional for cam
sudo apt-get install -y libevent-dev libdrm-dev

# Optional for qcam
sudo apt-get install -y libtiff-dev qtbase5-dev qttools5-dev-tools

# Clone libcamera repository
git clone https://git.libcamera.org/libcamera/libcamera.git 

# Build libcamera
cd libcamera
meson setup -Dpipelines=all -Dipas=all -Dv4l2=true -Dgstreamer=enabled -Dtest=false -Dlc-compliance=disabled -Dcam=enabled -Dqcam=enabled -Ddocumentation=disabled -Dpycamera=enabled build
cd build
ninja

# Install libcamera
sudo ninja install

# Clean up
#cd ../..
#rm -rf libcamera

# Add libcamera to the python path
echo "export PYTHONPATH=$PYTHONPATH:/usr/local/lib/aarch64-linux-gnu/python3.10/site-packages" >> ~/.bashrc

echo "Libcamera has been built and installed successfully."

# Build nad install kms++
# Dependencies
sudo apt-get install -y libopenblas-dev libavformat-dev libavfilter-dev libavdevice-dev libcap-dev libfmt-dev

# Build and Install
git clone https://github.com/tomba/kmsxx.git
cd kmsxx
meson setup build
ninja -C build

# Add the kms++ to the python path
# Get the path of the kms++ library
kmsxx_path=$(pwd)
echo "export PYTHONPATH=$PYTHONPATH:$kmsxx_path/build/py" >> ~/.bashrc
