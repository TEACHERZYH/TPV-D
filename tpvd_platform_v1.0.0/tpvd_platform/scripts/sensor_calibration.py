#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sensor_calibration.py
传感器信号调理与静态非线性度标定分析脚本

功能：
1. 读取传感器输入电压 (Vin) 与调理输出电压 (Vout) 标定测试数据
2. 执行最小二乘法线性回归拟合，获得标定拟合直线与灵敏度系数
3. 计算满量程非线性度误差 (Non-linearity Error, delta_L)
4. 输出标定报告与评估结论（判定是否达到实训非线性度 < 1.5% 指标）
"""

import numpy as np
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def analyze_calibration(v_in, v_out, full_scale_range=2.5):
    """
    分析传感器调理放大器的静态输入输出标定数据
    
    参数:
        v_in: 输入电压数组 (mV 或 V)
        v_out: 输出电压实测值数组 (V)
        full_scale_range: 满量程电压 (V)
        
    返回:
        dict: 包含斜率(增益)、截距(偏置)、最大残差、非线性度误差与达标状态
    """
    v_in = np.array(v_in, dtype=np.float64)
    v_out = np.array(v_out, dtype=np.float64)
    
    if len(v_in) != len(v_out) or len(v_in) < 2:
        raise ValueError("输入与输出数据长度必须一致且至少包含2个采样点")

    # 1. 最小二乘法线性回归拟合: Vout = k * Vin + b
    p = np.polyfit(v_in, v_out, 1)
    k, b = p[0], p[1]
    
    # 2. 拟合预测值与残差计算
    v_fit = np.polyval(p, v_in)
    residuals = v_out - v_fit
    max_residual = np.max(np.abs(residuals))
    
    # 3. 满量程非线性度计算: delta_L = (max|Delta_y| / Y_FS) * 100%
    non_linearity_percent = (max_residual / full_scale_range) * 100.0
    
    # 4. 判断指标达标 (实训要求 < 1.5%)
    passed = bool(non_linearity_percent < 1.5)
    
    # 5. 计算决定系数 R^2
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((v_out - np.mean(v_out)) ** 2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot != 0 else 1.0
    
    result = {
        "sensitivity_gain": float(k),
        "offset_bias_v": float(b),
        "max_residual_v": float(max_residual),
        "non_linearity_percent": float(non_linearity_percent),
        "r_squared": float(r_squared),
        "full_scale_range_v": float(full_scale_range),
        "spec_threshold_percent": 1.5,
        "is_passed": passed,
        "points_count": int(len(v_in))
    }
    
    return result, v_fit

def plot_calibration_curve(v_in, v_out, v_fit, output_image_path):
    """生成并保存标定与残差曲线图"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), gridspec_kw={'height_ratios': [2.5, 1]})
    
    # 主标定图
    ax1.plot(v_in, v_out, 'ro', label='Measured Output (Vout)', markersize=5)
    ax1.plot(v_in, v_fit, 'b-', label='Linear Fit Line', linewidth=1.5)
    ax1.set_title('Sensor Analog Front-End Calibration Curve', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Output Voltage (V)', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='best')
    
    # 残差图
    residuals = np.array(v_out) - np.array(v_fit)
    ax2.stem(v_in, residuals * 1000, linefmt='g-', markerfmt='gd', basefmt='k-')
    ax2.set_xlabel('Input Voltage (mV)', fontsize=10)
    ax2.set_ylabel('Residual (mV)', fontsize=10)
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(output_image_path)), exist_ok=True)
    plt.savefig(output_image_path, dpi=150)
    plt.close()

if __name__ == "__main__":
    # 模拟真实微弱振动信号标定数据 (Vin: 50mV ~ 2400mV, 调理目标为 0.1V ~ 2.45V)
    v_in_test = np.linspace(50, 2400, 24)
    # 真实运放微弱非线性与偏置
    v_out_test = 0.001005 * v_in_test + 0.052 + 0.012 * np.sin(v_in_test / 400.0)
    
    res, v_fit_res = analyze_calibration(v_in_test, v_out_test, full_scale_range=2.5)
    print("=== 传感器标定测试结果 ===")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    
    img_path = "tpvd_platform/data/test_samples/calibration_plot.png"
    plot_calibration_curve(v_in_test, v_out_test, v_fit_res, img_path)
    print(f"标定曲线图已生成保存至: {img_path}")
