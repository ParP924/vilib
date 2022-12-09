import cv2
import numpy as np
import os
from tflite_runtime.interpreter import Interpreter

gesture_list = ["paper","scissor","rock"]
ges_num_list = [i for i in range(3)]
ges_dict = dict(zip(ges_num_list,gesture_list))
gesture_model_path = "/opt/vilib/3bak_ges_200_dr0.2.tflite"
interpreter_2 = tflite.Interpreter(model_path=gesture_model_path)
interpreter_2.allocate_tensors()

# gesture_obj_parameter
detect_obj_parameter['gesture_x'] = 320
detect_obj_parameter['gesture_y'] = 240
detect_obj_parameter['gesture_w'] = 0
detect_obj_parameter['gesture_h'] = 0
detect_obj_parameter['gesture_t'] = 'None'      # 手势文本  gesture_list = ["paper","scissor","rock"]
detect_obj_parameter['gesture_acc'] = 0

# 返回检测到的手势的坐标，大小，类型，准确度
@staticmethod
def gesture_detect_object(obj_parameter):
    if obj_parameter == 'x':
        return int(Vilib.detect_obj_parameter['gesture_x']/214.0)-1
    elif obj_parameter == 'y':
        return -1*(int(Vilib.detect_obj_parameter['gesture_y']/160.2)-1) #max_size_object_coordinate_y
    elif obj_parameter == 'width':
        return Vilib.detect_obj_parameter['gesture_w']   #objects_max_width
    elif obj_parameter == 'height':
        return Vilib.detect_obj_parameter['gesture_h']   #objects_max_height
    elif obj_parameter == 'type':      
        return Vilib.detect_obj_parameter['gesture_t']   #objects_type
    elif obj_parameter == 'accuracy':      
        return Vilib.detect_obj_parameter['gesture_acc']   #objects_type
    return 'none'

# 手势检测开关
@staticmethod
def gesture_detect_switch(flag=False):
    Vilib.detect_obj_parameter['gs_flag']  = flag


# 手势检测开关
@staticmethod
def gesture_calibrate_switch(flag=False):
    Vilib.detect_obj_parameter['calibrate_flag']  = flag


img = Vilib.gesture_calibrate(img)
img = Vilib.gesture_recognition(img)

# 手势校准接口
@staticmethod
def gesture_calibrate(img):
    if Vilib.detect_obj_parameter['calibrate_flag'] == True:
        cv2.imwrite('/opt/vilib/cali.jpg', img[190:290,270:370])
        cv2.rectangle(img,(270,190),(370,290),(255,255,255),2)

    return img

### 手势识别的流程和上面交通标志一致
@staticmethod
def gesture_predict(input_img,x,y,w,h):

    x1 = int(x)
    x2 = int(x + w)
    y1 = int(y)
    y2 = int(y + h)

    if x1 <= 0:
        x1 = 0
    elif x2 >= 640:
        x2 = 640
    if y1 <= 0:
        y1 = 0
    elif y2 >= 640:
        y2 = 640


    new_img = input_img[y1:y2,x1:x2]
    new_img = (new_img / 255.0)
    new_img = (new_img - 0.5) * 2.0

    resize_img = cv2.resize(new_img, (96,96), interpolation=cv2.INTER_LINEAR)
    flatten_img = np.reshape(resize_img, (96,96,3))
    im5 = np.expand_dims(flatten_img,axis = 0)

# Perform the actual detection by running the model with the image as input
    image_np_expanded = im5.astype('float32') # 类型也要满足要求

    interpreter_2.set_tensor(input_details_2[0]['index'],image_np_expanded)
    interpreter_2.invoke()
    output_data_2 = interpreter_2.get_tensor(output_details_2[0]['index'])

#     # 出来的结果去掉没用的维度   np.where(result==np.max(result)))[0][0]
    result = np.squeeze(output_data_2)
    result_accuracy =  round(np.max(result),2)
    ges_class = np.where(result==np.max(result))[0][0]


    return result_accuracy,ges_class

# 手掌肤色的区域检测，把图像的区域给手势识别接口做手势识别
@staticmethod
def gesture_recognition(img):
    if Vilib.detect_obj_parameter['gs_flag'] == True:

###肤色部分

        target_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        # 首先对样本图像计算2D直方图
        roi_hsv_hist = cv2.calcHist([Vilib.roi_hsv], [0, 1], None, [180, 256], [0, 180, 0, 255])
        # 对得到的样本2D直方图进行归一化
        # 这样可以方便显示，归一化后的直方图就变成0-255之间的数了
        # cv2.NORM_MINMAX表示对数组所有值进行转换，线性映射到最大最小值之间
        cv2.normalize(roi_hsv_hist, roi_hsv_hist, 0, 255, cv2.NORM_MINMAX)
        # 对待检测图像进行反向投影
        # 最后一个参数为尺度参数
        dst = cv2.calcBackProject([target_hsv], [0, 1], roi_hsv_hist, [0, 180, 0, 256], 1)
        # 构建一个圆形卷积核，用于对图像进行平滑，连接分散的像素
        disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dst = cv2.filter2D(dst, -1, disc,dst)
        ret, thresh = cv2.threshold(dst, 1, 255, 0)
        dilate = cv2.dilate(thresh, Vilib.kernel_5, iterations=3)
            # 注意由于原图是三通道BGR图像，因此在进行位运算之前，先要把thresh转成三通道
        # thresh = cv2.merge((dilate, dilate, dilate))
            # 对原图与二值化后的阈值图像进行位运算，得到结果
        # res = cv2.bitwise_and(img, thresh)
        # ycrcb=cv2.cvtColor(img,cv2.COLOR_BGR2YCR_CB)
        # cr_skin = cv2.inRange(ycrcb, (85,124,121), (111,131,128))
        # open_img = cv2.morphologyEx(cr_skin, cv2.MORPH_OPEN,Vilib.kernel_5,iterations=1)

        contours, hierarchy = findContours(dilate)
        ges_num = len(contours)
        is_ges = False
        if ges_num > 0:
            contours = sorted(contours,key = Vilib.cnt_area, reverse=True)
            # for i in range(0,len(contours)):    #遍历所有的轮廓
            x,y,w,h = cv2.boundingRect(contours[0])      #将轮廓分解为识别对象的左上角坐标和宽、高
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
            faces = Vilib.face_cascade.detectMultiScale(gray[y:y+h,x:x+w], 1.3, 2)
        # print(len(faces))
            face_len = len(faces)

            # 在图像上画上矩形（图片、左上角坐标、右下角坐标、颜色、线条宽度）
            if w >= 60 and h >= 60 and face_len == 0:
                # acc_val,ges_type = Vilib.gesture_predict(img,x-2.2*w,y-2.8*h,4.4*w,5.6*h) 
                acc_val,ges_type = Vilib.gesture_predict(img,x-0.1*w,y-0.2*h,1.1*w,1.2*h) 

                acc_val = round(acc_val*100,3)
                if acc_val >= 75:
                    # print(x,y,w,h)
                    cv2.rectangle(img,(int(x-0.1*w),int(y-0.2*h)),(int(x+1.1*w), int(y+1.2*h)),(0,125,0),2, cv2.LINE_AA)
                    cv2.rectangle(img,(0,0),(125,27),(204,209,72),-1, cv2.LINE_AA)
                    cv2.putText(img,ges_dict[ges_type]+': '+str(acc_val) + '%',(0,17),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2)  ##(0,97,240)

                    Vilib.detect_obj_parameter['gesture_x'] = int(x + w/2)
                    Vilib.detect_obj_parameter['gesture_y'] = int(y + h/2)
                    Vilib.detect_obj_parameter['gesture_w'] = w
                    Vilib.detect_obj_parameter['gesture_h'] = h
                    Vilib.detect_obj_parameter['gesture_t'] = ges_dict[ges_type]
                    Vilib.detect_obj_parameter['gesture_acc'] = acc_val
                    is_ges = True
        
        if is_ges == False:  
            Vilib.detect_obj_parameter['gesture_x'] = 320
            Vilib.detect_obj_parameter['gesture_y'] = 240
            Vilib.detect_obj_parameter['gesture_w'] = 0
            Vilib.detect_obj_parameter['gesture_h'] = 0
            Vilib.detect_obj_parameter['gesture_t'] = 'none'
            Vilib.detect_obj_parameter['gesture_acc'] = 0

    return img