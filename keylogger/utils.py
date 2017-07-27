# coding: utf-8


def __produce_mapping():
    """
       evdev产生的码 对应的字符
    """
    code_dict = {
        1: 'ESC', 2: '1', 3: '2', 4: '3', 5: '4', 6: '5', 7: '6', 8: '7', 9: '8',
        10: '9', 11: '0', 14: 'backspace', 15: 'tab', 16: 'q', 17: 'w', 18: 'e',
        19: 'r', 20: 't', 21: 'y', 22: 'u', 23: 'i', 24: 'o', 25: 'p', 26: '[',
        27: ']', 28: 'enter', 29: 'ctrl', 30: 'a', 31: 's', 32: 'd', 33: 'f', 34: 'g',
        35: 'h', 36: 'j', 37: 'k', 38: 'l', 39: ';', 40: "'", 41: '`', 42: 'shift',
        43: '\\', 44: 'z', 45: 'x', 46: 'c', 47: 'v', 48: 'b', 49: 'n', 50: 'm', 51: ',',
        52: '.', 53: '/', 54: 'shift', 56: 'alt', 57: 'space', 58: 'capslock', 59: 'F1',
        60: 'F2', 61: 'F3', 62: 'F4', 63: 'F5', 64: 'F6', 65: 'F7', 66: 'F8', 67: 'F9',
        68: 'F10', 69: 'numlock', 70: 'scrollock', 87: 'F11', 88: 'F12', 97: 'ctrl', 99: 'sys_Rq',
        100: 'alt', 102: 'home', 104: 'PageUp', 105: 'Left', 106: 'Right', 107: 'End',
        108: 'Down', 109: 'PageDown', 111: 'del', 125: 'Win', 126: 'Win', 127: 'compose'
    }

    def wrapper(code):
        return code_dict[code]
    return wrapper


def __produce_special_character():
    """
       需要特殊处理的字符
       #TODO
       剩下的特殊字符的处理请用户自行完成作为练习
    """
    SPECIAL_CHARACTERS = {
        ",": "<",
        ".": ">",
        ";": ":",
        "'": '"',
        "[": "{",
        "]": "}",
        "-": "_",
        "=": "+",
    }

    def wrapper(code, shift_status=True):
        """ 如果是特殊字符， 并且shift键被按了, 需要进行转化"""
        if code in SPECIAL_CHARACTERS and shift_status:
            return SPECIAL_CHARACTERS[code]
        return code


# 使用闭包避免使用全局变量
word_ctoa = __produce_mapping()
special_character_handler = __produce_special_character()

del __produce_mapping
del __produce_special_character
