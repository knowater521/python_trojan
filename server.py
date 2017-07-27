# coding:utf-8
"""  简单的接受数据的server """
import socket
import json
import sys

argv = sys.argv
if not (len(argv) == 3 and argv[1] == '-p' and (argv[2] == '8888' or argv[2] == '8889')):
    print """usage : 
        python server -p 8888 | python server -p 8889 """
    sys.exit(-1)

# 从命令行中获取port端口号
port = sys.argv[2]
# 开启ip和端口
ip_port = ('127.0.0.1', int(port))
# 生成一个句柄
sk = socket.socket()
# 绑定ip端口
sk.bind(ip_port)
# 最多连接数
sk.listen(5)
# 开启死循环

def header_handler(mesg):
    dict_obj = json.loads(mesg)
    file_name = dict_obj.get("file_name")
    file_type = dict_obj.get("file_type")
    fp = open(file_name + "." + file_type, "wb")
    return fp


conn, addr = sk.accept()
header_message = conn.recv(1024)
file_fp = header_handler(str(header_message))
print u'接受键盘消息'
while True:
    # 获取客户端请求数据
    client_data = conn.recv(1024*10)
    if len(client_data) == 0:
        break
    if bytes('\r\nover\r\n') in client_data:
        break
    file_fp.write(client_data)
# 关闭链接
print "over"
file_fp.close()
conn.close()
