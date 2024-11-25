import socket
import os
from typing import Set
import time

SERVER_IP = '127.0.0.1'  # 改为服务器的IP地址
SERVER_PORT = 54321      # 改为与服务器相同的端口
BUFFER_SIZE = 8192
SENT_FOLDERS: Set[str] = set()  # 用于记录已发送的文件夹

def send_data(client_socket, data: bytes):
    """发送长度前缀的数据，前8个字节为数据长度（大端）"""
    data_length = len(data)
    length_bytes = data_length.to_bytes(8, byteorder='big')
    print(f"发送数据长度前缀: {length_bytes}")
    client_socket.sendall(length_bytes)
    print(f"发送数据内容: {data}")
    client_socket.sendall(data)

def send_int(client_socket, value: int):
    """发送8字节的大端整数"""
    int_bytes = value.to_bytes(8, byteorder='big')
    print(f"发送整数值: {value}, 字节: {int_bytes}")
    client_socket.sendall(int_bytes)

def send_folder_info(client_socket, folder_path: str):
    try:
        # 发送文件夹名称
        folder_name = os.path.basename(folder_path)
        print(f"发送文件夹名称: {folder_name}")
        send_data(client_socket, folder_name.encode('utf-8'))

        # 发送文件夹中的图片数量（8字节整数）
        image_files = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.png'))]
        num_images = len(image_files)
        print(f"发送文件数量: {num_images}")
        send_int(client_socket, num_images)

        for image_file in image_files:
            file_path = os.path.join(folder_path, image_file)
            send_file(client_socket, file_path)

        print(f"文件夹 {folder_name} 发送完成")
        return True

    except Exception as e:
        print(f"发送文件夹信息时出错: {e}")
        return False

def send_file(client_socket, file_path):
    try:
        # 发送文件名
        file_name = os.path.basename(file_path)
        print(f"发送文件名: {file_name}")
        send_data(client_socket, file_name.encode('utf-8'))

        # 发送文件大小（8字节整数）
        file_size = os.path.getsize(file_path)
        print(f"发送文件大小: {file_size}")
        send_int(client_socket, file_size)

        # 发送文件内容
        with open(file_path, 'rb') as file:
            total_sent = 0
            while True:
                chunk = file.read(BUFFER_SIZE)
                if not chunk:
                    break
                client_socket.sendall(chunk)
                total_sent += len(chunk)
                print(f"发送文件数据: {len(chunk)} 字节，已发送 {total_sent}/{file_size} 字节")
        print(f"文件发送完成: {file_path}")
    except Exception as e:
        print(f"发送文件时出错: {e}")

def check_new_folders(root_dir: str) -> list:
    """检查根目录下的新文件夹（未发送的文件夹）"""
    all_folders = [os.path.join(root_dir, d) for d in os.listdir(root_dir)
                   if os.path.isdir(os.path.join(root_dir, d))]
    return [f for f in all_folders if f not in SENT_FOLDERS]

def client_program(root_dir: str, camera_ip: str):
    while True:
        try:
            # 检查新文件夹
            new_folders = check_new_folders(root_dir)
            if not new_folders:
                print("等待新文件夹...")
                time.sleep(5)  # 每5秒检查一次
                continue

            # 建立与服务器的连接
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect((SERVER_IP, SERVER_PORT))
                print(f"已连接到服务器 {SERVER_IP}:{SERVER_PORT}")

                # 1. 发送固定字符串标识
                print("发送固定字符串 'str'")
                send_data(client_socket, 'str'.encode('utf-8'))

                # 2. 发送相机IP
                print(f"发送相机IP: {camera_ip}")
                send_data(client_socket, camera_ip.encode('utf-8'))

                # 3. 发送文件夹数量（8字节整数）
                num_folders = len(new_folders)
                print(f"发送文件夹数量: {num_folders}")
                send_int(client_socket, num_folders)

                # 4. 发送每个文件夹的信息
                for folder in new_folders:
                    print(f"开始发送文件夹: {folder}")
                    success = send_folder_info(client_socket, folder)
                    if success:
                        SENT_FOLDERS.add(folder)  # 添加到已发送集合

            except Exception as e:
                print(f"通信时发生错误: {e}")
            finally:
                client_socket.close()
                print("已关闭与服务器的连接")

        except Exception as e:
            print(f"客户端运行出错: {e}")
        finally:
            time.sleep(5)  # 等待5秒再检查

if __name__ == "__main__":
    ROOT_DIR = "C:/Users/19395/Desktop/123"  # 替换为您的根目录路径
    CAMERA_IP = "192.168.1.100"  # 替换为实际的相机IP
    client_program(ROOT_DIR, CAMERA_IP)
