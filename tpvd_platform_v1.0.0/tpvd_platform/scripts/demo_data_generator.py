#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_data_generator.py
生成学生实训过程性测试数据样本文件

生成文件：
1. `data/test_samples/sensor_calibration.csv` (微弱信号传感器输入输出标定数据)
2. `data/test_samples/adc_raw_samples.csv` (ADC 20kHz 采集时域波形数据)
3. `data/test_samples/wireless_frames.bin` (无线传感器网络抓包二进制数据流)
4. `data/test_samples/firmware_memory_map.json` (微控制器 Flash/SRAM 内存符号表解析结果)
"""

import numpy as np
import os
import csv
import json
from wireless_protocol_parser import pack_sensor_frame

def generate_all_samples(output_dir="tpvd_platform/data/test_samples"):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 传感器调理标定 CSV
    cal_file = os.path.join(output_dir, "sensor_calibration.csv")
    v_in = np.linspace(50, 2400, 25)
    # 真实运放微弱非线性
    v_out = 0.001002 * v_in + 0.048 + 0.008 * np.sin(v_in / 350.0)
    with open(cal_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Index", "Input_Voltage_mV", "Output_Voltage_V"])
        for idx, (vi, vo) in enumerate(zip(v_in, v_out), start=1):
            writer.writerow([idx, round(vi, 1), round(vo, 4)])
    print(f"已生成标定数据: {cal_file}")

    # 2. ADC 原始采样数据 CSV (2048 点, 20kHz 采样率)
    adc_file = os.path.join(output_dir, "adc_raw_samples.csv")
    fs = 20000.0
    t = np.arange(2048) / fs
    # 800Hz基波 + 50Hz共模干扰 + 6kHz高频噪声 + 白噪声
    adc_raw = (
        0.85 * np.sin(2 * np.pi * 800 * t) +
        0.28 * np.sin(2 * np.pi * 50 * t) +
        0.18 * np.sin(2 * np.pi * 6000 * t) +
        0.04 * np.random.randn(len(t))
    )
    with open(adc_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Sample_Index", "Time_ms", "Voltage_V"])
        for idx, (ti, val) in enumerate(zip(t, adc_raw)):
            writer.writerow([idx, round(ti * 1000, 3), round(val, 5)])
    print(f"已生成 ADC 采样数据: {adc_file}")

    # 3. 无线抓包二进制数据流 .bin
    bin_file = os.path.join(output_dir, "wireless_frames.bin")
    with open(bin_file, 'wb') as f:
        for seq in range(50):
            frame = pack_sensor_frame(
                seq_num=seq,
                rms_val=0.48 + 0.01 * np.sin(seq / 5.0),
                peak_val=1.32 + 0.02 * np.cos(seq / 4.0),
                freq_peak=800.2 + 0.5 * np.sin(seq),
                raw_samples_slice=[int(1000 * np.sin(seq + i)) for i in range(4)]
            )
            f.write(frame)
    print(f"已生成无线二进制数据流: {bin_file}")

    # 4. 微控制器内存占用报告 JSON
    mem_file = os.path.join(output_dir, "firmware_memory_map.json")
    mem_data = {
        "mcu_model": "STM32F407ZGT6",
        "flash_capacity_bytes": 1048576,
        "sram_capacity_bytes": 196608,
        "memory_segments": {
            "Code": 248920,
            "RO_Data": 42104,
            "RW_Data": 3280,
            "ZI_Data": 82540
        },
        "total_flash_used_bytes": 291024,
        "total_flash_used_percent": 27.75,
        "total_sram_used_bytes": 85820,
        "total_sram_used_percent": 43.65,
        "stack_size_bytes": 4096,
        "heap_size_bytes": 8192,
        "is_memory_safe": True
    }
    with open(mem_file, 'w', encoding='utf-8') as f:
        json.dump(mem_data, f, indent=2, ensure_ascii=False)
    print(f"已生成微控制器内存报告: {mem_file}")

if __name__ == "__main__":
    generate_all_samples()
