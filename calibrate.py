# -*- coding: utf-8 -*-
"""
校准脚本：截取手机屏幕 -> 保存 -> OCR 识别出所有文字及其位置
用法: python calibrate.py
输出每行格式: 文字   x=左   y=上   w=宽   h=高
"""
import subprocess
import shutil

import cv2
import pytesseract

ADB_PATH = r'D:\platform-tools\adb.exe'
TESSERACT_PATH = r'D:\Program Files\Tesseract-OCR\tesseract.exe'
SAVE_PATH = r'D:\platform-tools\screen.png'          # ASCII 路径，供 cv2 读取
WORKSPACE_COPY = r'e:\学习课外技术知识\cv图像处理\auto-xiaoyuankousuan\screen.png'  # 工作区副本，供人查看

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def take_screenshot():
    """通过 subprocess 截屏，避免 PowerShell 重定向损坏二进制"""
    result = subprocess.run([ADB_PATH, 'exec-out', 'screencap', '-p'],
                            capture_output=True)
    data = result.stdout
    if data[:4] != b'\x89PNG':
        print('截图失败，请检查手机连接')
        return None
    with open(SAVE_PATH, 'wb') as f:
        f.write(data)
    shutil.copy(SAVE_PATH, WORKSPACE_COPY)
    return data


def main():
    take_screenshot()
    img = cv2.imread(SAVE_PATH)
    if img is None:
        print('图片读取失败')
        return
    print('截图尺寸:', img.shape[1], 'x', img.shape[0])
    d = pytesseract.image_to_data(img, config='--psm 6',
                                  output_type=pytesseract.Output.DICT)
    print('识别到的文字及位置（x=左边界, y=上边界, w=宽, h=高）:')
    for word, x, y, w, h in zip(d['text'], d['left'], d['top'],
                                d['width'], d['height']):
        if word.strip():
            print(f'  {word!r:12s} x={x:<5d} y={y:<5d} w={w:<4d} h={h}')


if __name__ == '__main__':
    main()
