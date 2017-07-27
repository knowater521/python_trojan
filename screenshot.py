# coding: utf-8
import os
import time
from task import send_pic_task
import commands


def screen_shot(file_name='screen_shot', file_type='png'):
    """
    本程序未实现指定图片存储的路径，用户自行实现该扩展功能
    借助os.path.join函数
    """
    print u'3秒过后第一次截图', file_name, file_type
    time.sleep(3)
    # 调用外部程序
    # 调用scrot截屏产生的临时文件名和类型和服务器端的不能完全一致，因为这个临时
    # 文件会被删除，那么运行后找不到图片，原因就是send_pic_task在
    # 本地运行是非常快的，服务端建立了一个文件，然后os.remove立马删除，就无法看到效果

    ret = commands.getstatusoutput("scrot " + file_name + 'tmp.' + file_type)
    if ret[0] != 0:
        print u"图片类型不支持，请换用png jpg等常用格式"
        return
    # 读取图像的二进制文件，进行网络传输
    with open(file_name + 'tmp.' + file_type, "rb") as fp:
        send_pic_task(fp.read(), file_name, file_type)
    # 这里执行os.remove将scrot产生的临时文件删除, 不能留下痕迹
    os.remove(file_name + 'tmp.' + file_type)
    print u'发送屏幕截图完成'


if __name__ == '__main__':
    screen_shot("shot")
