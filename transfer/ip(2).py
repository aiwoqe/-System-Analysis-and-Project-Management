import socket
import threading
import os
import datetime

# 配置服务器
SERVER_IP = '0.0.0.0'
SERVER_PORT = 54321
BUFFER_SIZE = 8192
CACHE_DIR = './appcache'

# 初始化存储目录
os.makedirs(CACHE_DIR, exist_ok=True)


# 日志记录
def log_connection(client_address):
    ip, _ = client_address
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] 客户端 {ip} 已连接\n"
    print(log_message)
    with open('./server.log', 'a', encoding='utf-8') as log_file:
        log_file.write(log_message)


# 处理文件接收
def receive_file(client_socket, client_ip):
    try:
        # 创建保存文件的文件夹
        client_dir = os.path.join(CACHE_DIR, client_ip)
        os.makedirs(client_dir, exist_ok=True)

        # 接收文件名长度并解码
        file_name_length = int(client_socket.recv(1024).decode('utf-8'))  # 获取文件名长度
        file_name = client_socket.recv(file_name_length).decode('utf-8')  # 接收文件名,不能是BUFFER_SIZE大小，否则缓冲区会遗留

        file_path = os.path.join(client_dir, file_name)  # 使用客户端传来的文件名保存文件

        with open(file_path, 'wb') as file:
            total_bytes_received = 0
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:  # 如果接收到的内容为空，表示文件接收完毕
                    break
                file.write(data)
                total_bytes_received += len(data)
                print(f"接收中: {total_bytes_received} 字节", end="\r")

        print(f"\n文件接收完成: {file_path}, 总大小: {total_bytes_received} 字节")
    except Exception as e:
        print(f"接收文件时出错: {e}")


# 发送文件到客户端
def send_file(client_socket, client_ip):
    client_dir = os.path.join(CACHE_DIR, client_ip)
    file_to_send = os.path.join(client_dir, 'yolov8n.onnx')  # 示例文件

    # 如果不存在，创建示例文件
    if not os.path.exists(file_to_send):
        with open(file_to_send, 'w', encoding='utf-8') as file:
            file.write("这是服务器发送的测试文件。")

    # 发送文件名的长度
    file_name = os.path.basename(file_to_send)
    client_socket.send(str(len(file_name)).encode('utf-8'))  # 发送文件名长度
    client_socket.send(file_name.encode('utf-8'))  # 发送文件名

    # 发送文件内容
    with open(file_to_send, 'rb') as file:
        while (chunk := file.read(BUFFER_SIZE)):
            client_socket.send(chunk)

    print(f"已向客户端 {client_ip} 发送文件: {file_name}")


# 处理单个客户端
def handle_client(client_socket, client_address):
    client_ip, _ = client_address
    log_connection(client_address)

    try:
        # 接收文件
        receive_file(client_socket, client_ip)
        #  +识别类型1234：图片名称
        #  相机ip+时间戳：文件夹划分图片文件夹
        #         俩字段：图片和训练类型，每个类型对应一个训练函数
        # 发送文件
        send_file(client_socket, client_ip)
    except Exception as e:
        print(f"处理客户端 {client_ip} 时发生错误: {e}")
    finally:
        client_socket.close()
        print(f"客户端 {client_ip} 已断开连接")


# 主线程监听连接
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    print(f"服务器启动，监听端口 {SERVER_PORT}...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n服务器主动停止")
    finally:
        server_socket.close()
        print("服务器已关闭")


if __name__ == "__main__":
    start_server()
