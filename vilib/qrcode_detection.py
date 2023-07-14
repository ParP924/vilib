import cv2
from pyzbar import pyzbar

# QR_code
qrcode_obj_parameter = {}
qrcode_obj_parameter['qr_data'] = "None"
qrcode_obj_parameter['qr_x'] = 320
qrcode_obj_parameter['qr_y'] = 240
qrcode_obj_parameter['qr_w'] = 0
qrcode_obj_parameter['qr_h'] = 0

def qrcode_detect(img):
    barcodes = pyzbar.decode(img)
    # 循环检测到的条形码
    if len(barcodes) > 0:
        for barcode in barcodes:
            # 提取条形码的边界框的位置
            # 画出图像中条形码的边界框
            (x, y, w, h) = barcode.rect
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # 条形码数据为字节对象，所以如果我们想在输出图像上
            # 画出来，就需要先将它转换成字符串
            barcodeData = barcode.data.decode("utf-8")
            # barcodeType = barcode.type

            # 绘出图像上条形码的数据和条形码类型
            # text = "{} ({})".format(barcodeData, barcodeType)
            text = "{}".format(barcodeData)
            if len(text) > 0:
                qrcode_obj_parameter['qr_data'] = text
                qrcode_obj_parameter['qr_h'] = h
                qrcode_obj_parameter['qr_w'] = w
                qrcode_obj_parameter['qr_x'] = x 
                qrcode_obj_parameter['qr_y'] = y
            # print("Vilib.qr_date:%s"%Vilib.qr_date)
            cv2.putText(img, text, (x - 20, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 0, 255), 2)
    else:
        qrcode_obj_parameter['qr_data'] = "None"
        qrcode_obj_parameter['qr_x'] = 320
        qrcode_obj_parameter['qr_y'] = 240
        qrcode_obj_parameter['qr_w'] = 0
        qrcode_obj_parameter['qr_h'] = 0
    return img
