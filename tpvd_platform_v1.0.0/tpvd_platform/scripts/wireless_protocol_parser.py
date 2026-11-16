#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wireless_protocol_parser.py
无线传感器网络自定义协议解调、CRC-16校验与ARQ信道统计脚本

功能：
1. 封装与解析工业监测终端自定义数据链路层二进制帧：
   [Preamble(2B): 0xAA 0x55] + [Control(2B): SeqNum + Type] + [Len(1B)] + [Payload(N B)] + [CRC-16(2B)]
2. 计算并验证 CRC-16-CCITT 校验码（网络大端传输，可检测小端倒置暗病）
3. 模拟实际多径无线丢包信道，执行停等 ARQ 重传机制
4. 统计物理丢包率、ARQ 修复后实际丢包率、端到端时延分布与有效吞吐率
"""

import struct
import random
import time
import json
import numpy as np

PREAMBLE_MAGIC = b'\xAA\x55'

# 帧类型定义
FRAME_TYPE_DATA = 0x01
FRAME_TYPE_ACK  = 0x02
FRAME_TYPE_NACK = 0x03

def calculate_crc16_ccitt(data: bytes, poly=0x1021, init_val=0xFFFF) -> int:
    """
    计算 CRC-16-CCITT 校验码
    多项式 G(x) = x^16 + x^12 + x^5 + 1 (0x1021)
    """
    crc = init_val
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

def pack_sensor_frame(seq_num: int, rms_val: float, peak_val: float, freq_peak: float, raw_samples_slice: list) -> bytes:
    """
    将传感器特征值与时域切片打包为符合任务书规范的二进制无线报文
    """
    # 载荷结构: RMS(4B float) + Peak(4B float) + Freq(4B float) + 4个样本点(4*2B int16) = 20 Bytes
    samples_bytes = struct.pack(f'>{len(raw_samples_slice)}h', *raw_samples_slice)
    payload = struct.pack('>fff', rms_val, peak_val, freq_peak) + samples_bytes
    
    length = len(payload)
    if length > 128:
        raise ValueError("载荷超出最大物理帧长 128 字节限制")
        
    ctrl_field = struct.pack('>BB', seq_num % 256, FRAME_TYPE_DATA)
    header = PREAMBLE_MAGIC + ctrl_field + struct.pack('>B', length)
    
    # 待校验数据段: Control + Length + Payload
    data_to_crc = ctrl_field + struct.pack('>B', length) + payload
    crc_val = calculate_crc16_ccitt(data_to_crc)
    
    # 网络大端发送: >H
    crc_bytes = struct.pack('>H', crc_val)
    
    frame = header + payload + crc_bytes
    return frame

def unpack_sensor_frame(raw_bytes: bytes, enforce_big_endian_crc=True):
    """
    解析接收到的二进制帧并执行 CRC 校验
    
    返回:
        tuple: (is_valid, parsed_dict, error_msg)
    """
    if len(raw_bytes) < 7:
        return False, None, "帧长度过短（小于最小头校验开销 7 字节）"
        
    # 1. 前导码匹配
    if raw_bytes[:2] != PREAMBLE_MAGIC:
        return False, None, f"前导同步码错位: 期望 0xAA55, 实际 {raw_bytes[:2].hex()}"
        
    seq_num = raw_bytes[2]
    frame_type = raw_bytes[3]
    length = raw_bytes[4]
    
    expected_total_len = 5 + length + 2
    if len(raw_bytes) != expected_total_len:
        return False, None, f"帧长不匹配: 报头声明载荷 {length}B (总长{expected_total_len}B), 实际接收 {len(raw_bytes)}B"
        
    payload = raw_bytes[5:5 + length]
    received_crc = raw_bytes[5 + length:5 + length + 2]
    
    # 2. 计算本地 CRC
    data_to_crc = raw_bytes[2:5 + length]
    calc_crc = calculate_crc16_ccitt(data_to_crc)
    
    if enforce_big_endian_crc:
        expected_crc_int = struct.unpack('>H', received_crc)[0]
    else:
        # 小端模式（排查 AI 大小端暗病时使用）
        expected_crc_int = struct.unpack('<H', received_crc)[0]
        
    if calc_crc != expected_crc_int:
        return False, None, f"CRC-16 校验失败: 期望 0x{calc_crc:04X}, 收到 0x{expected_crc_int:04X}"
        
    # 3. 解析载荷特征数据
    if length >= 12:
        rms, peak, freq = struct.unpack('>fff', payload[:12])
        slice_samples = []
        sample_bytes = payload[12:]
        if len(sample_bytes) >= 2:
            count = len(sample_bytes) // 2
            slice_samples = list(struct.unpack(f'>{count}h', sample_bytes[:count*2]))
    else:
        rms, peak, freq, slice_samples = 0.0, 0.0, 0.0, []
        
    parsed_info = {
        "seq_num": seq_num,
        "frame_type": frame_type,
        "payload_len": length,
        "rms_g": round(rms, 4),
        "peak_g": round(peak, 4),
        "dominant_freq_hz": round(freq, 2),
        "samples_slice": slice_samples,
        "crc_hex": f"0x{calc_crc:04X}"
    }
    
    return True, parsed_info, None

def simulate_wireless_arq_transmission(total_frames=1000, physical_loss_rate=0.08, max_retries=3, ack_timeout_ms=30):
    """
    模拟多径衰落信道下的停等 ARQ 通信链路并统计性能指标
    """
    transmitted_count = 0
    total_physical_attempts = 0
    successful_deliveries = 0
    final_lost_frames = 0
    latencies = []
    
    for seq in range(total_frames):
        transmitted_count += 1
        delivered = False
        attempts = 0
        
        # 组装模拟报文
        frame_bytes = pack_sensor_frame(
            seq_num=seq,
            rms_val=0.45 + random.uniform(-0.02, 0.02),
            peak_val=1.28 + random.uniform(-0.05, 0.05),
            freq_peak=800.0 + random.uniform(-2.0, 2.0),
            raw_samples_slice=[random.randint(-1500, 1500) for _ in range(4)]
        )
        
        while attempts <= max_retries:
            attempts += 1
            total_physical_attempts += 1
            
            # 模拟物理信道丢包概率
            is_lost = (random.random() < physical_loss_rate)
            
            if not is_lost:
                # 接收端成功解包
                is_valid, parsed, err = unpack_sensor_frame(frame_bytes)
                if is_valid:
                    delivered = True
                    # 计算端到端时延: 传输时间 + 重传等待
                    latency = 8.5 + (attempts - 1) * ack_timeout_ms + random.uniform(1.0, 4.0)
                    latencies.append(latency)
                    successful_deliveries += 1
                    break
                    
        if not delivered:
            final_lost_frames += 1
            
    # 计算统计指标
    final_loss_rate_percent = (final_lost_frames / total_frames) * 100.0
    raw_loss_rate_percent = ((total_physical_attempts - successful_deliveries) / total_physical_attempts) * 100.0
    avg_latency_ms = float(np.mean(latencies)) if latencies else 0.0
    p95_latency_ms = float(np.percentile(latencies, 95)) if latencies else 0.0
    effective_throughput_kbps = (successful_deliveries * 27 * 8) / (np.sum(latencies) / 1000.0) / 1000.0 if latencies else 0.0
    
    report = {
        "total_source_frames": total_frames,
        "total_air_attempts": total_physical_attempts,
        "successful_deliveries": successful_deliveries,
        "final_lost_frames": final_lost_frames,
        "raw_channel_loss_rate_percent": round(raw_loss_rate_percent, 2),
        "post_arq_final_loss_rate_percent": round(final_loss_rate_percent, 3),
        "avg_end_to_end_latency_ms": round(avg_latency_ms, 2),
        "p95_latency_ms": round(p95_latency_ms, 2),
        "effective_throughput_kbps": round(effective_throughput_kbps, 2),
        "spec_loss_threshold_percent": 2.0,
        "spec_latency_threshold_ms": 50.0,
        "is_passed_loss": bool(final_loss_rate_percent < 2.0),
        "is_passed_latency": bool(avg_latency_ms < 50.0)
    }
    
    return report

if __name__ == "__main__":
    print("=== 单帧编解码与 CRC-16 校验演示 ===")
    demo_samples = [1200, 1450, -800, -1100]
    frame = pack_sensor_frame(seq_num=42, rms_val=0.482, peak_val=1.35, freq_peak=798.5, raw_samples_slice=demo_samples)
    print(f"生成的二进制帧 ({len(frame)} 字节): {frame.hex(' ').upper()}")
    
    valid, info, err = unpack_sensor_frame(frame)
    print(f"解析结果: valid={valid}")
    print(json.dumps(info, indent=2))
    
    print("\n=== 1000 帧无线 ARQ 衰落信道统计分析 ===")
    stats = simulate_wireless_arq_transmission(total_frames=1000, physical_loss_rate=0.06, max_retries=3)
    print(json.dumps(stats, indent=2))
