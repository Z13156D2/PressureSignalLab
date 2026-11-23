import random
import time
import struct


def generate_sensor_data_packet():
    """
    生成符合协议格式的数据包
    格式：SOT-(data1, data2, ...datan)-(xoffset,yoffset)-EOT
    """
    # 定义起始和结束标志位
    SOT = 0xAAA000AA  # 起始标志
    EOT = 0xFFFF00FF  # 结束标志

    # 随机选择左侧或右侧传感器
    is_left_sensor = random.choice([True, False])

    # 设置坐标偏移位
    if is_left_sensor:
        xoffset = 0  # 左侧传感器x偏移为0
    else:
        xoffset = 20  # 右侧传感器x偏移为20
    yoffset = 0  # 纵坐标偏移固定为0

    # 生成随机压力数据（假设有10个数据点，每个数据点范围0-4095）
    num_data_points = 10
    sensor_data = [random.randint(0, 4095) for _ in range(num_data_points)]

    # 构建数据包
    data_packet = []

    # 添加起始标志位SOT（4字节）
    data_packet.extend(struct.pack('>I', SOT))

    # 添加传感器数据（每个数据点2字节，大端序）
    for data in sensor_data:
        data_packet.extend(struct.pack('>H', data))

    # 添加坐标偏移位（每个偏移2字节，大端序）
    data_packet.extend(struct.pack('>H', xoffset))
    data_packet.extend(struct.pack('>H', yoffset))

    # 添加结束标志位EOT（4字节）
    data_packet.extend(struct.pack('>I', EOT))

    return bytes(data_packet), sensor_data, is_left_sensor


def format_packet_for_display(packet_bytes):
    """将数据包格式化为可读的十六进制字符串"""
    hex_str = packet_bytes.hex().upper()
    # 每2个字符（1字节）加一个空格
    formatted = ' '.join(hex_str[i:i + 2] for i in range(0, len(hex_str), 2))
    return formatted


def continuous_data_generation(interval=2):
    """
    连续生成并打印数据包
    interval: 生成间隔（秒）
    """
    packet_count = 0

    # print("开始连续生成链式压力传感器数据包...")
    # print("数据格式: SOT-(data1, data2, ...datan)-(xoffset,yoffset)-EOT")
    # print("SOT = AA A0 00 AA, EOT = FF FF 00 FF")
    # print("=" * 80)

    try:
        while True:
            packet_count += 1
            packet_bytes, sensor_data, is_left_sensor = generate_sensor_data_packet()
            formatted_packet = format_packet_for_display(packet_bytes)

            # 打印数据包信息
            # print(f"\n数据包 #{packet_count}")
            # print(f"传感器: {'左侧' if is_left_sensor else '右侧'}链式压力传感器")
            # print(f"xoffset: {0 if is_left_sensor else 20}, yoffset: 0")
            # print(f"数据点: {sensor_data}")
            print(f"完整数据包: {formatted_packet}")

            # 高亮显示关键部分
            packet_hex = formatted_packet.split()
            sot_index = 0
            data_start = 4  # SOT占4字节
            data_end = data_start + len(sensor_data) * 2  # 每个数据点2字节
            offset_start = data_end
            offset_end = offset_start + 4  # xoffset和yoffset各占2字节
            eot_start = offset_end

            # print("解析说明:")
            # print(f"  SOT(起始标志): {' '.join(packet_hex[sot_index:sot_index + 4])}")
            # print(f"  压力数据({len(sensor_data)}个点): {' '.join(packet_hex[data_start:data_end])}")
            # print(f"  偏移位(xoffset,yoffset): {' '.join(packet_hex[offset_start:offset_end])}")
            # print(f"  EOT(结束标志): {' '.join(packet_hex[eot_start:eot_start + 4])}")
            # print("-" * 80)

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n数据生成已停止。共生成 {packet_count} 个数据包。")


if __name__ == "__main__":
    # 设置生成间隔（秒）
    GENERATION_INTERVAL = 3

    # print("链式压力传感器数据包生成器")
    # print("=" * 50)
    # print("协议格式: SOT-(data1, data2, ...datan)-(xoffset,yoffset)-EOT")
    # print("SOT: 0XAAA000AA, EOT: 0XFFFF00FF")
    # print("左侧传感器: xoffset=0, yoffset=0")
    # print("右侧传感器: xoffset=20, yoffset=0")
    # print("=" * 50)


    # 生成单个数据包示例
    print("\n生成单个数据包示例:")
    sample_packet, sample_data, sample_sensor = generate_sensor_data_packet()
    sample_formatted = format_packet_for_display(sample_packet)
    # print(f"示例数据包: {sample_formatted}")
    # print(f"传感器: {'左侧' if sample_sensor else '右侧'}")
    # print(f"数据点: {sample_data}")

    # 开始连续生成
    input("\n按Enter键开始连续生成数据包，按Ctrl+C停止...")
    continuous_data_generation(GENERATION_INTERVAL)