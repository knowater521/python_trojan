# coding: utf-8
import socket
import json
import time
"""
定义网路任务
"""

SERVER_CONFIG = {
    "IP": "127.0.0.1",
    "PORT": 8888,
}


class NetworkClient(object):
    def __init__(self, config):
        self.server_ip = config['IP']
        self.server_port = config['PORT']
        # 建立一个tcp的链接
        self.sock = socket.socket()
        self.sock.connect((self.server_ip, self.server_port))

    def send_data(self, data):
        # 发送数据
        ret = self.sock.sendall(data)
        assert ret != -1

    def destroy(self):
        try:
            self.sock.close()
        except Exception as e:
            print e


class BasicNetworkTask(object):
    def __init__(self, server_instance, content):
        # 每一个网络任务都要关联到一哥tcp的服务上
        self.server = server_instance
        self.content = content

    def run(self):
        self.server.send_data(self.content)


class NetworkTaskManager(object):

    def __init__(self, server_instance, file_type, file_name):
        self.server_instance = server_instance
        self.file_type = file_type
        self.file_name = file_name
        # 发送消息头， 在这里是为了发送文件名和文件类型
        self.send_message_header()

    def send_message_header(self):
        header_message = {
            "file_name": self.file_name,
            "file_type": self.file_type
        }
        # 建立一个任务，然后发送相应的内容
        task = BasicNetworkTask(self.server_instance, json.dumps(header_message))
        task.run()

    def send_content(self, content):
        task = BasicNetworkTask(self.server_instance, content)
        task.run()
        return "success"

    def send_stop_message(self):

        # 建立一个任务，然后发送相应的内容,告诉数据已经发送完毕
        content = "\r\nover\r\n"
        task = BasicNetworkTask(self.server_instance, content)
        task.run()
        # 记得释放这个tcp的链接
        self.server_instance.destroy()


def send_pic_task(content, file_name='screenshot', file_type='png'):
    # 因为发送内容图片内容一次就可以发送完成，所以进行了一次封装，
    # 外部调用时传入图片内容，文件名和文件类型即可
    server = NetworkClient({"IP": "127.0.0.1", 'PORT': 8889})
    obj = NetworkTaskManager(server, file_type=file_type, file_name=file_name)
    # 在这里进行sleep，是为了解决 `tcp粘包` 问题。
    # tcp 粘包问题 更多请参考 http://blog.csdn.net/zhangxinrun/article/details/6721495
    time.sleep(1)
    obj.send_content(content)
    obj.send_stop_message()
