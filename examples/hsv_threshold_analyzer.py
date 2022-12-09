import numpy as np
import cv2

# define default HSV threshold
H_lower = 102
S_lower = 50
V_lower = 50

H_upper = 125
S_upper = 255
V_upper = 255

# define a 5*5 kernel
kernel_5 = np.ones((5, 5),np.uint8)

def trackbar_callback(*arg):
    pass

# Test
def main():
    global H_lower, S_lower, V_lower
    global H_upper, S_upper, V_upper
    print("hsv_threshold_analyzer")

    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    
    # Configuration adjustment window
    hsv_adjust_win = "HSV Threshold Analyzer"
    cv2.namedWindow(hsv_adjust_win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(hsv_adjust_win, 320, 360)
    cv2.moveWindow(hsv_adjust_win, 20, 60)

    cv2.createTrackbar("H_lower", hsv_adjust_win, H_lower, 255, trackbar_callback)
    cv2.createTrackbar("S_lower", hsv_adjust_win, S_lower, 255, trackbar_callback)
    cv2.createTrackbar("V_lower", hsv_adjust_win, V_lower, 255, trackbar_callback)

    cv2.createTrackbar("H_upper", hsv_adjust_win, H_upper, 255, trackbar_callback)
    cv2.createTrackbar("S_upper", hsv_adjust_win, S_upper, 255, trackbar_callback)
    cv2.createTrackbar("V_upper", hsv_adjust_win, V_upper, 255, trackbar_callback)

    # Configuration original image window
    original_img_win = 'original img' 
    cv2.namedWindow(original_img_win, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(original_img_win, 480, 360)
    cv2.moveWindow(original_img_win, 350, 60)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        # frame = cv2.flip(frame, 0) # Flip camera horizontally 
        # frame = cv2.flip(frame, 1) # Flip camera vertically
        # frame = cv2.flip(frame, -1) # Flip camera vertically & horizontally
        
        hsv_img = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        H_lower = cv2.getTrackbarPos("H_lower", hsv_adjust_win)
        S_lower = cv2.getTrackbarPos("S_lower", hsv_adjust_win)
        V_lower = cv2.getTrackbarPos("V_lower", hsv_adjust_win)

        H_upper = cv2.getTrackbarPos("H_upper", hsv_adjust_win)
        S_upper = cv2.getTrackbarPos("S_upper", hsv_adjust_win)
        V_upper = cv2.getTrackbarPos("V_upper", hsv_adjust_win)


        mask_img = cv2.inRange(hsv_img, (H_lower, S_lower, V_lower), (H_upper, S_upper, V_upper))
        # opening the image (erosion followed by dilation), to remove the image noise
        open_img = cv2.morphologyEx(mask_img, cv2.MORPH_OPEN, kernel_5, iterations=1)  

        cv2.imshow(original_img_win, frame)
        cv2.imshow(hsv_adjust_win, open_img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break   
        if cv2.waitKey(1) & 0xff == 27: # press 'ESC' to quit
            break
        if cv2.getWindowProperty(hsv_adjust_win, 1) < 0 or \
            cv2.getWindowProperty(original_img_win, 1) < 0:
            print('HSV_lower: %s, %s, %s \n HSV_upper: %s, %s, %s'
                %(H_lower, S_lower, V_lower)

                )
            break   

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()