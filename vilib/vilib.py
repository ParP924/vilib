#!/usr/bin/env python3

# whther print welcome message
import os
from .version import __version__
# os.environ['VILIB_WELCOME'] = 'True'
if 'VILIB_WELCOME' in os.environ and os.environ['VILIB_WELCOME'] not in  ['False', '0']:
    from pkg_resources import require
    picamera_version = require('picamera')[0].version
    print(f'vilib {__version__} launching ...')
    print(f'picamera {picamera_version}')


from picamera.array import PiRGBArray
from picamera import PiCamera
from PIL import Image, ImageDraw, ImageFont

import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

import time
import datetime
import threading
from multiprocessing import Process, Manager

from flask import Flask, render_template, Response

from .utils import *

# user and user home directory
# =================================================================
user = os.popen("echo ${SUDO_USER:-$(who -m | awk '{ print $1 }')}").readline().strip()
user_home = os.popen(f'getent passwd {user} | cut -d: -f 6').readline().strip()
# print(f"user: {user}")
# print(f"user_home: {user_home}")


# utils
# =================================================================
def findContours(img):
    _tuple = cv2.findContours(img, cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)      
    # compatible with opencv3.x and openc4.x
    if len(_tuple) == 3:
        _, contours, hierarchy = _tuple
    else:
        contours, hierarchy = _tuple
    return contours, hierarchy

# flask
# =================================================================
os.environ['FLASK_ENV'] =  'development'
app = Flask(__name__)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def get_frame():
    # return cv2.imencode('.jpg', Vilib.img_array[0])[1].tobytes()
    return cv2.imencode('.jpg', Vilib.img)[1].tobytes()

def get_qrcode_pictrue():
    # return cv2.imencode('.jpg', Vilib.img_array[1])[1].tobytes()
    return cv2.imencode('.jpg', Vilib.img)[1].tobytes()

def get_png_frame():
    # return cv2.imencode('.png', Vilib.img_array[0])[1].tobytes()
    return cv2.imencode('.jpg', Vilib.img)[1].tobytes()


def gen():
    """Video streaming generator function."""
    while True:  
        # start_time = time.time()
        frame = get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)
        # end_time = time.time() - start_time
        # print('flask fps:%s'%int(1/end_time))

@app.route('/mjpg')   ## video
def video_feed():
    # from camera import Camera
    """Video streaming route. Put this in the src attribute of an img tag."""
    response = Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame') 
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route('/mjpg.jpg')  # jpg
def video_feed_jpg():
    # from camera import Camera
    """Video streaming route. Put this in the src attribute of an img tag."""
    response = Response(get_frame(), mimetype="image/jpeg")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route('/mjpg.png')  # png
def video_feed_png():
    # from camera import Camera
    """Video streaming route. Put this in the src attribute of an img tag."""
    response = Response(get_png_frame(), mimetype="image/png")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def web_camera_start():
    try:
        app.run(host='0.0.0.0', port=9000, threaded=True, debug=False)
    except Exception as e:
        print(e)

# Vilib
# =================================================================
class Vilib(object): 

    flask_thread = None
    imshow_thread = None
    camera_thread = None
    imshow_process = None

    camera_vflip = False
    camera_hflip = False
    camera_run = False

    # img_array = Manager().list(range(2))
    img = Manager().list(range(1))


    Windows_Name = "picamera"
    imshow_flag = False
    web_display_flag = False

    start_time = 0

    draw_fps = False
    fps_origin = (10, 20)
    fps_size = 0.6
    fps_color = (255, 255, 255)

    detect_obj_parameter = {}
    color_detect_color = None
    face_detect_sw = False

    
    @staticmethod
    def camera():
        # init picamera
        camera = PiCamera()
        # https://picamera.readthedocs.io/en/latest/quickstart.html
        # https://github.com/waveform80/picamera.git

        camera.resolution = (640, 480)
        camera.image_effect = "none"
        camera.framerate = 30
        camera.rotation = 0
        camera.brightness = 50    #(0 to 100)
        camera.sharpness = 0      #(-100 to 100)
        camera.contrast = 0       #(-100 to 100)
        camera.saturation = 0     #(-100 to 100)
        camera.iso = 0            #(automatic)(100 to 800)
        camera.exposure_compensation = 0   #(-25 to 25)
        camera.exposure_mode = 'auto'
        camera.meter_mode = 'average'
        camera.awb_mode = 'auto'
        camera.hflip = Vilib.camera_hflip
        camera.vflip = Vilib.camera_vflip
        camera.crop = (0.0, 0.0, 1.0, 1.0)

        rawCapture = PiRGBArray(camera, size=camera.resolution)
        
        # # https://stackoverflow.com/questions/36447605/picamera-on-vnc-display
        # # preview overrides whatever is currently visible on the display
        # camera.start_preview(resolution=(640, 480))

        # Camera warm-up time
        # time.sleep(2)

        try:
            start_time = time.time()
            while True:
                for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                    # ----------- extract image data ----------------
                    # img = frame.array
                    Vilib.img = frame.array

                    # ----------- image gains and effects ----------------


                    # ----------- image detection and recognition ----------------
                    Vilib.img = Vilib.color_detect_func(Vilib.img)
                    Vilib.img = Vilib.face_detect_func(Vilib.img)


                    # ----------- calculate fps and draw fps ----------------
                    # calculate fps
                    elapsed_time = time.time() - start_time
                    fps = round(1.0/elapsed_time, 1)
                    # print(f"elapsed_time: {elapsed_time}, fps: {fps}")
                    # reset start_time
                    start_time = time.time()
                    # draw fps
                    if Vilib.draw_fps:
                        cv2.putText(
                                # img, # image
                                Vilib.img,
                                f"FPS: {fps}", # text
                                Vilib.fps_origin, # origin
                                cv2.FONT_HERSHEY_SIMPLEX, # font
                                Vilib.fps_size, # font_scale
                                Vilib.fps_color, # font_color
                                1, # thickness
                                cv2.LINE_AA, # line_type: LINE_8 (default), LINE_4, LINE_AA
                            )

                    # ----------- display on desktop ----------------
                    try:
                        # cv2.imshow(Vilib.Windows_Name, Vilib.img_array[0])
                        cv2.imshow(Vilib.Windows_Name, Vilib.img)
                        cv2.waitKey(1)
                        if cv2.getWindowProperty(Vilib.Windows_Name, cv2.WND_PROP_VISIBLE) == 0:
                            cv2.destroyWindow(Vilib.Windows_Name)
                    except Exception as e: 
                        print(f"imshow failed:\n  {e}")
                        break

                    # ----------- web display ----------------
                    if Vilib.web_display_flag == True:
                        if Vilib.flask_thread == None or Vilib.flask_thread.is_alive() == False:
                            print('Starting network video streaming ...')
                            wlan0,eth0 = getIP()
                            if wlan0 != None:
                                ip = wlan0     
                            else:
                                ip = eth0
                            print(f'\nRunning on: http://{ip}:9000/mjpg\n')
                            Vilib.flask_thread = threading.Thread(name='flask_thread',target=web_camera_start)
                            Vilib.flask_thread.daemon = True
                            Vilib.flask_thread.start()
                    # else:
                        # if flask_thread != None and flask_thread.is_alive():
                        #     flask_thread.join(timeout=0.2)

                    # ----------- copy img ----------------
                    # Vilib.img_array[0] = img
                    # ----------- truncate ----------------
                    rawCapture.truncate(0)

        except KeyboardInterrupt as e:
            print(e)
            pass
        finally:
            print('camera close')
            camera.close()
            cv2.destroyAllWindows()
            # if Vilib.flask_thread != None and Vilib.flask_thread.is_alive():
            #     Vilib.flask_thread.join(timeout=0.2)

    @staticmethod
    def camera_start(vflip=False, hflip=False):
        Vilib.camera_hflip = hflip       
        Vilib.camera_vflip = vflip
        Vilib.camera_run = True
        Vilib.camera_thread = threading.Thread(target=Vilib.camera, name="vilib")
        Vilib.camera_thread.start()

    @staticmethod
    def display(local=True, web=True):
        Vilib.draw_fps
        # cheack camera thread is_alive
        if Vilib.camera_thread != None and Vilib.camera_thread.is_alive():
            # check gui
            if local == True:
                if 'DISPLAY' in os.environ.keys():
                    Vilib.imshow_flag = True  
                    print("Imgshow start ...")
                else:
                    Vilib.imshow_flag = False 
                    print("Local display failed, because there is no gui.") 
            # web video
            if web == True:
                Vilib.web_display_flag = True 
        else:
            print('Error: Please execute < camera_start() > first.')

    @staticmethod
    def show_fps(color=None, fps_size=None, fps_origin=None):
        if color is not None:
            Vilib.fps_color = color
        if fps_size is not None:
            Vilib.fps_size = fps_size
        if fps_origin is not None:
            Vilib.fps_origin = fps_origin

        Vilib.draw_fps = True

    @staticmethod
    def hide_fps():
        Vilib.draw_fps = False

    # color detection
    # =================================================================
    @staticmethod 
    def color_detect(color="red"):
        '''
        
        :param color: could be red, green, blue, yellow , orange, purple
        '''
        Vilib.color_detect_color = color
        from .color_detection import color_detect_work, get_color_obj_parameter
        Vilib.color_detect_work = color_detect_work
        Vilib.get_color_obj_parameter = get_color_obj_parameter
        Vilib.detect_obj_parameter['color_x'] = Vilib.get_color_obj_parameter('x')
        Vilib.detect_obj_parameter['color_y'] = Vilib.get_color_obj_parameter('y')
        Vilib.detect_obj_parameter['color_w'] = Vilib.get_color_obj_parameter('w')
        Vilib.detect_obj_parameter['color_h'] = Vilib.get_color_obj_parameter('h')
        Vilib.detect_obj_parameter['color_n'] = Vilib.get_color_obj_parameter('n')

    @staticmethod
    def color_detect_func(img):
        if Vilib.color_detect_color is not None:
            img = Vilib.color_detect_work(img, 640, 480, Vilib.color_detect_color)
            Vilib.detect_obj_parameter['color_x'] = Vilib.get_color_obj_parameter('x')
            Vilib.detect_obj_parameter['color_y'] = Vilib.get_color_obj_parameter('y')
            Vilib.detect_obj_parameter['color_w'] = Vilib.get_color_obj_parameter('w')
            Vilib.detect_obj_parameter['color_h'] = Vilib.get_color_obj_parameter('h')
            Vilib.detect_obj_parameter['color_n'] = Vilib.get_color_obj_parameter('n')
        return img

    @staticmethod
    def close_color_detection():
        Vilib.color_detect_color = None

    # face detection
    # =================================================================
    @staticmethod   
    def face_detect_switch(flag=False):
        Vilib.face_detect_sw = flag
        if Vilib.face_detect_sw:
            from .face_detection import face_detect, set_face_detection_model, get_face_obj_parameter
            Vilib.face_detect_work = face_detect
            Vilib.set_face_detection_model = set_face_detection_model
            Vilib.get_face_obj_parameter = get_face_obj_parameter
            Vilib.detect_obj_parameter['human_x'] = Vilib.get_face_obj_parameter('x')
            Vilib.detect_obj_parameter['human_y'] = Vilib.get_face_obj_parameter('y')
            Vilib.detect_obj_parameter['human_w'] = Vilib.get_face_obj_parameter('w')
            Vilib.detect_obj_parameter['human_h'] = Vilib.get_face_obj_parameter('h')
            Vilib.detect_obj_parameter['human_n'] = Vilib.get_face_obj_parameter('n')

    @staticmethod
    def face_detect_func(img):
        if Vilib.face_detect_sw:
            img = Vilib.face_detect_work(img, 640, 480)
            Vilib.detect_obj_parameter['human_x'] = Vilib.get_face_obj_parameter('x')
            Vilib.detect_obj_parameter['human_y'] = Vilib.get_face_obj_parameter('y')
            Vilib.detect_obj_parameter['human_w'] = Vilib.get_face_obj_parameter('w')
            Vilib.detect_obj_parameter['human_h'] = Vilib.get_face_obj_parameter('h')
            Vilib.detect_obj_parameter['human_n'] = Vilib.get_face_obj_parameter('n')
        return img

