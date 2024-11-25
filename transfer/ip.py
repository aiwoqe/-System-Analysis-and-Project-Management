import socket
import os

SERVER_IP = '0.0.0.0'  # 替换为服务器的IP地址
SERVER_PORT = 12345
BUFFER_SIZE = 8192


def send_file(client_socket, file_path):
    try:
        # 发送文件名的长度
        file_name = os.path.basename(file_path)
        client_socket.send(str(len(file_name)).encode('utf-8'))  # 发送文件名长度,不能是BUFFER_SIZE大小，否则缓冲区会遗留
        client_socket.send(file_name.encode('utf-8'))  # 发送文件名

        # 发送文件内容
        with open(file_path, 'rb') as file:
            while chunk := file.read(BUFFER_SIZE):
                client_socket.send(chunk)
                print(f"发送中: {len(chunk)} 字节", end="\r")

        client_socket.shutdown(socket.SHUT_WR)  # 完成后关闭写端
        print(f"\n文件发送完成: {file_path}")
    except Exception as e:
        print(f"发送文件时出错: {e}")


def receive_file(client_socket):
    try:
        # 接收文件名长度并解码
        file_name_length = int(client_socket.recv(1024).decode('utf-8'))  # 获取文件名长度
        file_name = client_socket.recv(file_name_length).decode('utf-8')  # 接收文件名

        # 准备保存文件的路径
        file_path = os.path.join(os.getcwd(), file_name)
        with open(file_path, 'wb') as file:
            total_bytes_received = 0
            while True:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:  # 文件接收完成
                    break
                file.write(data)
                total_bytes_received += len(data)
                print(f"接收中: {total_bytes_received} 字节", end="\r")

        print(f"\n文件接收完成: {file_path}, 总大小: {total_bytes_received} 字节")
    except Exception as e:
        print(f"接收文件时出错: {e}")


def client_program():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))

    try:
        # 上传文件
        file_path = 'roi_1.jpg'  # 替换为你要上传的文件
        send_file(client_socket, file_path)

        # 接收服务器发送的文件
        receive_file(client_socket)
    finally:
        client_socket.close()
        print("客户端已断开连接")


if __name__ == "__main__":
    client_program()
