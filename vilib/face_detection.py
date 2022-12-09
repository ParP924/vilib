import cv2


'''Define parameters for face detection object'''
# Default model path
face_model_path = '/opt/vilib/haarcascade_frontalface_default.xml'

face_obj_parameter = {}
face_obj_parameter['human_x'] = 320  # Maximum face block center x-axis coordinate
face_obj_parameter['human_y'] = 240  # Maximum face block center y-axis coordinate
face_obj_parameter['human_w'] = 0  # Maximum face block pixel width
face_obj_parameter['human_h'] = 0  # Maximum face pixel height
face_obj_parameter['human_n'] = 0  # Number of faces detected


def get_face_obj_parameter(parameter):
    '''
    Returns the coordinates, size, and number of human_face

    :param parameter: Parameter to be returned, could be: "x", "y", "width", "height", "number"
    :type name: str
    :returns: The coordinates, size, and number of human_face, or all of them.
    :rtype: int or dict
    '''
    if parameter == 'x':
        return int(face_obj_parameter['human_x']/214.0)-1   # max_size_object_coordinate_x
    elif parameter == 'y':
        return -1*(int(face_obj_parameter['human_y']/160.2)-1)  # max_size_object_coordinate_y
    elif parameter == 'width':
        return face_obj_parameter['human_w']   # objects_max_width
    elif parameter == 'height':
        return face_obj_parameter['human_h']   # objects_max_height
    elif parameter == 'number':      
        return face_obj_parameter['human_n']   # objects_count
    elif parameter == 'all':
        return dict.copy(face_obj_parameter)
    return None


def set_face_detection_model(model_path):
    '''
    Set face detection model path

    :param model_path: The path of face haar-cascade XML classifier file
    :type model_path: str
    '''
    global face_model_path
    face_model_path = model_path

def face_detect(img, width, height, rectangle_color=(255, 0, 0)):
    '''
    Face detection with opencv

    :param img: The detected image data
    :type img: list
    :param width: The width of the image data
    :type width: int
    :param height: The height of the image data
    :type height: int
    :param rectangle_color: The color (BGR, tuple) of rectangle. Eg: (255, 0, 0).
    :type color_name: tuple
    :returns: The image returned after detection.
    :rtype: Binary list
    '''
    # Reduce image for faster recognition 
    zoom = 2
    width_zoom = int(width / zoom)
    height_zoom = int(height / zoom)
    resize_img = cv2.resize(img, (width_zoom, height_zoom), interpolation=cv2.INTER_LINEAR)
    
    # Converting the image to grayscale
    gray_img = cv2.cvtColor(resize_img, cv2.COLOR_BGR2GRAY) 

    # Loading the haar-cascade XML classifier file
    face_cascade = cv2.CascadeClassifier(face_model_path)

    # Applying the face detection method on the grayscale image
    faces = face_cascade.detectMultiScale(gray_img, scaleFactor=1.3, minNeighbors=2)
    
    face_obj_parameter['human_n'] = len(faces)

    # Iterating over all detected faces
    if face_obj_parameter['human_n'] > 0:
        max_area = 0
        for (x,y,w,h) in faces:
            x = x * zoom
            y = y * zoom
            w = w * zoom
            h = h * zoom
            # Draw rectangle around the face
            cv2.rectangle(img, (x, y), (x+w, y+h), rectangle_color, 2)
            
            # Save the attribute of the largest color block
            object_area = w * h
            if object_area > max_area: 
                max_area = object_area
                face_obj_parameter['human_x'] = int(x + w/2)
                face_obj_parameter['human_y'] = int(y + h/2)
                face_obj_parameter['human_w'] = w
                face_obj_parameter['human_h'] = h
    else:
        face_obj_parameter['human_x'] = width/2
        face_obj_parameter['human_y'] = height/2
        face_obj_parameter['human_w'] = 0
        face_obj_parameter['human_h'] = 0
        face_obj_parameter['human_n'] = 0
        
    return img

# Test
def test():
    print("face detection ...")

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    while cap.isOpened():
        success,frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        # frame = cv2.flip(frame, -1) # Flip camera vertically

        out_img = face_detect(frame, 640, 480)

        cv2.imshow('Face detecting ...', out_img)

        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break
        # if cv2.waitKey(1) & 0xff == 27: # press 'ESC' to quit
        #     break
        # if cv2.getWindowProperty('Face detecting ...', 1) < 0:
        #     break

        key = cv2.waitKey(10) & 0xff
        print(key)


    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test()


