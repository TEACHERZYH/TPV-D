# TPV-D 实训达成评价与人机协同复核系统 (TPV-D Educational Assessment Platform)


>
> 📖 **完整详尽的技术规格与业务实现说明文档**：请参见同目录下的 [实验平台说明文档.md](./实验平台说明文档.md)。

---

## 一、系统架构与工程目录结构

系统严格按照论文第三节（系统架构与数据流）进行工程化微服务解耦实现，整体目录结构如下：

```text
tpvd_platform/
├── README.md                           # 工程说明与快速运行指南
├── 实验平台说明文档.md                   # 深度技术规格与业务实现说明文档（含接口规约）
├── run_demo.py                         # 一键功能演示与自动化集成测试脚本
├── scripts/                            # 【Part 1】数据分析与解调算法脚本集
│   ├── sensor_calibration.py           # 传感器信号调理与最小二乘拟合非线性度计算
│   ├── adc_dsp_analyzer.py             # ADC交替采样性能分析 (ENOB/SNR) 与定点IIR滤波仿真
│   ├── wireless_protocol_parser.py     # 自定义无线传感器报文解调、CRC-16校验与ARQ信道统计
│   ├── automated_evaluator.py          # T维度自动化测试评测与量化打分引擎
│   └── demo_data_generator.py          # 真实工况模拟数据样本生成工具
├── platform_core/                      # 【Part 2】平台核心算法与数据处理引擎
│   ├── models.py                       # 平台核心数据模型 (Student, ScoreRecord, CLO)
│   ├── score_calculator.py             # 课程目标达成度计算引擎 (论文公式 1 和公式 2)
│   ├── discrepancy_detector.py         # 差异分析与异常倒挂筛查引擎 (论文公式 3 和公式 4)
│   ├── database.py                     # 平台内存与 JSON 混合数据库管理服务
│   └── seed_data.py                    # 预置论文 95 名学生实证全息数据集
├── web_app/                            # 【Part 3】Web 交互界面与 REST API 服务
│   ├── app.py                          # 基于 FastAPI 构建的 Web 服务主程序
│   └── templates/                      # 现代化响应式前端模板
│       ├── base.html                   # 全局基础模板与导航栏
│       ├── dashboard.html              # 班级达成度雷达图与异常倒挂大屏
│       ├── teacher.html                # 教师人机复核工作台 (优先复核队列)
│       ├── student.html                # 学生个体成长画像与诊断报告
│       └── review.html                 # 深度复核仲裁与变式任务下发页
└── data/                               # 【Part 4】数据持久化与基准样本库
    ├── tpvd_database.json              # 平台全量数据持久化文件
    └── test_samples/                   # 预生成的工况测试数据工件 (CSV/BIN/JSON)
```

---

## 二、核心技术特性与论文公式对标

| 模块类别 | 对应文件 | 核心技术点与论文公式映射 |
| :--- | :--- | :--- |
| **信号分析与解调算法** | `sensor_calibration.py` | 最小二乘拟合与端点非线性度计算（$\delta_L < 1.5\%$） |
| | `adc_dsp_analyzer.py` | 汉宁窗 FFT 动态性能分析（ENOB $\ge 11.2$ bits）与 Q15 定点滤波（时延 $< 2.0$ ms） |
| | `wireless_protocol_parser.py` | 大端前导码帧同步、CRC-16-CCITT 校验与停等 ARQ 信道统计（丢包率 $< 2.0\%$） |
| | `automated_evaluator.py` | T1~T5 量化评分引擎，自动化生成 $T$ 维度得分 |
| **平台核心评价引擎** | `score_calculator.py` | **公式 (1)** 个体达成度 $S_i(c) = \sum w_{j,c} S_{i,j}$ 与 **公式 (2)** 班级综合达成度 $A_c$ |
| | `discrepancy_detector.py` | **公式 (3)** 差异度 $D_i = T_i - V_{I,i}$ 且 $R_i = \mathbb{I}(T_i \ge 85 \land V_{I,i} < 60)$<br>**公式 (4)** 工时减少率 $L = 76.8\%$ |
| | `seed_data.py` | 真实还原论文中 95 名学生实证全息数据（14 名预警、8 名抽检、21 名认定过度借力） |
| **Web 协同工作台** | `web_app/` | FastAPI + Jinja2 响应式看板、优先复核队列、仲裁调分与变式下发闭环 |

---

## 三、快速开始与使用指南

### 1. 运行一键集成验证测试
在工程根目录下执行以下命令，即可自动化执行全套算法与数据验证：
```bash
python3 tpvd_platform/run_demo.py
```

### 2. 单独运行信号分析与解调脚本
```bash
# 1. 运行传感器标定分析并输出拟合结果
python3 tpvd_platform/scripts/sensor_calibration.py

# 2. 运行 ADC 采样与定点 DSP 滤波分析
python3 tpvd_platform/scripts/adc_dsp_analyzer.py

# 3. 运行无线自定义协议编解码与 ARQ 信道丢包仿真
python3 tpvd_platform/scripts/wireless_protocol_parser.py

# 4. 执行 T 维度自动化测试评测套件
python3 tpvd_platform/scripts/automated_evaluator.py
```

### 3. 启动 Web 辅助评价平台
```bash
python3 tpvd_platform/web_app/app.py
```
平台将在 `http://localhost:8000` 启动，浏览器访问即可体验：
- `/` 或 `/dashboard`：系统全景看板（课程目标达成度雷达图、异常倒挂散点图、工时节省数据）；
- `/teacher`：教师优先复核工作台（展示高危倒挂预警及优先处理队列）；
- `/student/EI032`：学生个人端视图（查看能力诊断报告、四维得分明细及薄弱项提升建议）；
- `/review/EI032`：人机仲裁详情页（对比 $T$ 与 $V_I$，录入仲裁结论并一键下发变式任务）；
- `/docs`：Swagger UI 交互式 RESTful 接口在线调试文档。
