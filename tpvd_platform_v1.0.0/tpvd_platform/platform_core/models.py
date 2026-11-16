# -*- coding: utf-8 -*-
"""
models.py
平台核心数据模型定义
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional

@dataclass
class Student:
    student_id: str         # 学号，如 EI032
    name: str               # 姓名
    group_id: str           # 实训小组，如 Group_03
    role_name: str          # 承担角色，如 算法与DSP工程师
    git_branch: str         # 负责分支，如 feature/dsp-filter
    commit_sha: str         # 最新提交哈希，如 e4b8a21f

@dataclass
class CourseLearningOutcome:
    clo_id: str             # 目标代号，如 CT1
    name: str               # 目标名称，如 故障分析与定位能力
    weight: float           # 权重占比
    target_threshold: float # 认证基准线，默认 0.70
    actual_attainment: float = 0.0 # 实际达成度

@dataclass
class ScoreRecord:
    student_id: str
    t_score: float          # T 维度: 任务达成得分 (0~100)
    p_score: float          # P 维度: 设计权衡得分 (0~100, 依据 0~3 级量规换算)
    v_i_score: float        # V-I 维度: 独立表现考核得分 (0~100)
    v_ai_score: float       # V-AI 维度: 人机协同批判考核得分 (0~100)
    
    # 差异与复核状态
    d_diff: float = 0.0     # 偏离度 D_i = T - V_I
    r_flag: int = 0         # 规则标记 R_i = I(T >= 85 and V_I < 60)
    is_random_sample: bool = False # 是否被随机抽样
    needs_review: bool = False     # 是否进入人工复核队列
    flag_reason: str = ""   # 预警原因说明
    
    # 复核与变式再测结果
    review_status: str = "PENDING"  # PENDING, AGREED, PASSED_WITHOUT_ACTION, REMEDIATION_REQUIRED
    variant_task_assigned: bool = False
    retest_passed: Optional[bool] = None
    
    # 课程目标分项标准分 (式 1 计算结果)
    clo_scores: Dict[str, float] = field(default_factory=dict)
    
    def calculate_discrepancy(self, tau_t=85.0, tau_v=60.0):
        self.d_diff = round(self.t_score - self.v_i_score, 1)
        if self.t_score >= tau_t and self.v_i_score < tau_v:
            self.r_flag = 1
            self.needs_review = True
            self.flag_reason = f"表现倒挂高疑(T={self.t_score:.0f}优秀, V-I={self.v_i_score:.0f}未达标, 偏离度D={self.d_diff:.0f})"
        elif self.is_random_sample:
            self.needs_review = True
            self.flag_reason = "常规质量随机抽检(固定比例抽样)"
        else:
            self.r_flag = 0
            if not self.needs_review:
                self.flag_reason = "各项指标正常，证据链自洽"

@dataclass
class PlatformMetrics:
    total_students: int
    rule_flagged_count: int
    random_sample_count: int
    total_reviewed_count: int
    workload_reduction_percent: float
    review_agreement_rate_percent: float
    retest_pass_rate_percent: float
    actual_review_time_min: int
    baseline_estimated_time_min: int
    clo_attainments: Dict[str, float]
