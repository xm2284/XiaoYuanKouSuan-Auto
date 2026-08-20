# -*- coding: utf-8 -*-
"""
小猿口算自动答题 - 可视化界面版
用法: python gui_auto.py
功能: 开始答题 / 停止，日志实时显示截图、OCR 识别、比较结果和画符号过程
"""
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import scrolledtext

import xiaoyuan_auto as auto  # 复用已校准好的截图/识别/画图函数


class StdoutToQueue:
    """把 print 输出重定向到日志队列，同时回显到控制台"""

    def __init__(self, q, console=None):
        self.q = q
        self.console = console  # 原始 stdout，用于同时显示在控制台

    def write(self, text):
        if text.strip():
            self.q.put(text)
            if self.console is not None:
                self.console.write(text)
                self.console.flush()

    def flush(self):
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.stop_flag = threading.Event()
        self.log_q = queue.Queue()
        self.worker_thread = None
        self._old_stdout = sys.stdout

        root.title('小猿口算自动答题')
        root.geometry('560x540')

        tk.Label(root, text='小猿口算自动答题（比较大小）',
                 font=('Microsoft YaHei', 14, 'bold')).pack(pady=10)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        self.start_btn = tk.Button(btn_frame, text='开始答题', width=12,
                                   command=self.start, bg='#4CAF50', fg='white',
                                   font=('Microsoft YaHei', 11))
        self.start_btn.pack(side='left', padx=10)
        self.stop_btn = tk.Button(btn_frame, text='停止', width=12,
                                  command=self.stop, state='disabled',
                                  bg='#f44336', fg='white',
                                  font=('Microsoft YaHei', 11))
        self.stop_btn.pack(side='left', padx=10)

        self.status = tk.Label(root, text='未开始', fg='gray')
        self.status.pack(pady=5)

        self.log_box = scrolledtext.ScrolledText(root, height=20,
                                                 state='disabled',
                                                 font=('Consolas', 10))
        self.log_box.pack(fill='both', expand=True, padx=10, pady=10)

        root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.after(100, self.poll_log)

    def log(self, msg):
        self.log_q.put(msg)

    def poll_log(self):
        """定期把日志队列里的内容刷到界面"""
        try:
            while True:
                msg = self.log_q.get_nowait()
                self.log_box.configure(state='normal')
                self.log_box.insert('end', msg + '\n')
                self.log_box.see('end')
                self.log_box.configure(state='disabled')
        except queue.Empty:
            pass
        self.root.after(100, self.poll_log)

    @staticmethod
    def check_device():
        r = subprocess.run([auto.ADB_PATH, 'devices'],
                           capture_output=True, text=True)
        return [line for line in r.stdout.splitlines() if '\tdevice' in line]

    def start(self):
        devices = self.check_device()
        if not devices:
            self.log('未检测到已连接的手机（请先连好 USB 调试）')
            return
        self.log('检测到手机: ' + devices[0].split('\t')[0])
        self.stop_flag.clear()
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status.config(text='运行中…', fg='green')
        # 把模块里的 print 重定向到日志框
        self._old_stdout = sys.stdout
        sys.stdout = StdoutToQueue(self.log_q, console=self._old_stdout)
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()

    def worker(self):
        """后台循环：截图 -> 识别 -> 比较 -> 画符号"""
        self.log('开始自动答题（比较大小），点"停止"结束')
        while not self.stop_flag.is_set():
            try:
                img = auto.take_screenshot()
                if img is None:
                    self.log('截图失败，请检查手机连接')
                    time.sleep(1)
                    continue
                numbers = auto.recognize_numbers(img)
                answer = auto.calculate_comparison(numbers)
                if answer is not None:
                    auto.input_answer(answer)
                    time.sleep(0.3)
                else:
                    time.sleep(0.4)
            except Exception as e:
                self.log(f'出错: {e}')
                time.sleep(0.5)
        self.log('已停止')

    def stop(self):
        self.stop_flag.set()
        sys.stdout = self._old_stdout
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status.config(text='已停止', fg='gray')

    def on_close(self):
        self.stop_flag.set()
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
