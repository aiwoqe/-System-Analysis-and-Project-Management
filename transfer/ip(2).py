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

def recv_exact(client_socket, num_bytes):
    """接收准确的num_bytes字节的数据"""
    data = b''
    while len(data) < num_bytes:
        packet = client_socket.recv(num_bytes - len(data))
        if packet is None:
            print("连接已关闭，无法接收更多数据")
            return None
        if not packet:
            # 对方可能已经关闭连接
            print("未接收到任何数据，连接可能已关闭")
            return None
        data += packet
        print(f"收到数据片段: {packet}, 当前已接收长度: {len(data)}")
    return data

def receive_data(client_socket) -> bytes:
    """接收带有长度前缀的数据，前8个字节为数据长度（大端）"""
    try:
        # 接收数据长度（8个字节）
        length_bytes = recv_exact(client_socket, 8)
        print(f"收到长度前缀: {length_bytes}")
        if not length_bytes:
            print("未接收到长度前缀，连接可能已关闭")
            return b''
        data_length = int.from_bytes(length_bytes, byteorder='big')
        print(f"数据长度: {data_length}")
        # 接收实际数据
        data = recv_exact(client_socket, data_length)
        if not data or len(data) != data_length:
            print(f"预期接收 {data_length} 字节，但实际接收了 {len(data) if data else 0} 字节")
            return b''
        print(f"收到数据: {data}")
        return data
    except Exception as e:
        print(f"接收数据时出错: {e}")
        return b''

def receive_int(client_socket) -> int:
    """接收8字节的大端整数"""
    try:
        int_bytes = recv_exact(client_socket, 8)
        print(f"收到整数字节: {int_bytes}")
        if not int_bytes or len(int_bytes) < 8:
            print("接收整数长度不足8字节")
            return -1
        value = int.from_bytes(int_bytes, byteorder='big')
        print(f"整数值: {value}")
        return value
    except Exception as e:
        print(f"接收整数时出错: {e}")
        return -1

def receive_file(client_socket, save_path: str) -> bool:
    """接收单个文件"""
    try:
        # 接收文件名
        file_name_bytes = receive_data(client_socket)
        if not file_name_bytes:
            print("未接收到文件名")
            return False
        file_name = file_name_bytes.decode('utf-8')
        print(f"接收到文件名: {file_name}")

        # 接收文件大小
        file_size = receive_int(client_socket)
        if file_size == -1:
            print("未接收到文件大小")
            return False
        print(f"接收文件: {file_name}, 大小: {file_size} 字节")

        # 接收文件内容
        file_path = os.path.join(save_path, file_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在

        remaining = file_size
        with open(file_path, 'wb') as file:
            while remaining > 0:
                chunk = client_socket.recv(min(BUFFER_SIZE, remaining))
                if not chunk:
                    print("文件数据不完整，连接可能已关闭")
                    break
                file.write(chunk)
                remaining -= len(chunk)
                print(f"接收文件数据: {len(chunk)} 字节，剩余 {remaining} 字节")
        if remaining == 0:
            print(f"文件接收完成: {file_path}")
            return True
        else:
            print(f"文件接收不完整: {file_path}")
            return False
    except Exception as e:
        print(f"接收文件时出错: {e}")
        return False

def handle_client(client_socket, client_address):
    """处理单个客户端连接"""
    client_ip, _ = client_address
    log_connection(client_address)

    try:
        # 1. 接收固定字符串
        print("开始接收固定字符串")
        fixed_str_bytes = receive_data(client_socket)
        if not fixed_str_bytes:
            raise Exception("未接收到固定字符串")
        fixed_str = fixed_str_bytes.decode('utf-8')
        print(f"收到的固定字符串: '{fixed_str}'")
        if fixed_str != 'str':
            raise Exception("固定字符串验证失败")
        print("固定字符串验证成功")

        # 2. 接收相机IP
        print("开始接收相机IP")
        camera_ip_bytes = receive_data(client_socket)
        if not camera_ip_bytes:
            raise Exception("未接收到相机IP")
        camera_ip = camera_ip_bytes.decode('utf-8')
        print(f"接收到相机IP: {camera_ip}")

        # 3. 接收文件夹数量
        print("开始接收文件夹数量")
        num_folders = receive_int(client_socket)
        if num_folders == -1:
            raise Exception("未接收到文件夹数量")
        print(f"预期接收文件夹数量: {num_folders}")

        # 4. 接收每个文件夹的信息
        for folder_index in range(num_folders):
            print(f"开始接收第 {folder_index+1} 个文件夹信息")
            # 接收文件夹名
            folder_name_bytes = receive_data(client_socket)
            if not folder_name_bytes:
                raise Exception("未接收到文件夹名")
            folder_name = folder_name_bytes.decode('utf-8')
            print(f"接收到文件夹名: {folder_name}")

            # 创建保存路径
            save_path = os.path.join(CACHE_DIR, camera_ip, folder_name)
            os.makedirs(save_path, exist_ok=True)

            # 接收文件数量
            file_count = receive_int(client_socket)
            if file_count == -1:
                raise Exception("未接收到文件数量")
            print(f"文件夹 {folder_name} 预期接收文件数量: {file_count}")

            # 接收所有文件
            received_files = 0
            for file_index in range(file_count):
                print(f"开始接收第 {file_index+1} 个文件")
                if receive_file(client_socket, save_path):
                    received_files += 1

            print(f"文件夹 {folder_name} 接收完成，成功接收 {received_files}/{file_count} 个文件")

        # 这里可以添加触发模型训练的代码
        # trigger_model_training(save_path)

    except Exception as e:
        print(f"处理客户端 {client_ip} 时发生错误: {e}")
    finally:
        client_socket.close()
        print(f"客户端 {client_ip} 已断开连接")

def start_server():
    """启动服务器"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    print(f"服务器启动，监听端口 {SERVER_PORT}...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("\n服务器主动停止")
    finally:
        server_socket.close()
        print("服务器已关闭")

if __name__ == "__main__":
    start_server()
