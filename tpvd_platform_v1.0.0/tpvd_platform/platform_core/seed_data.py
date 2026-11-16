# -*- coding: utf-8 -*-
import random
try:
    from .models import Student, ScoreRecord, CourseLearningOutcome
    from .score_calculator import calculate_student_clo_score
except Exception:
    from models import Student, ScoreRecord, CourseLearningOutcome
    from score_calculator import calculate_student_clo_score

def generate_paper_cohort_data(db):
    roles = [
        "信号链与驱动工程师 (ADC/DMA)",
        "实时算法工程师 (定点DSP/IIR)",
        "无线通信工程师 (协议/CRC/ARQ)",
        "系统架构工程师 (内存/低功耗/FreeRTOS)",
        "质量测试工程师 (CI/CD自动化测试)"
    ]
    branches = [
        "feature/adc-driver",
        "feature/dsp-filter",
        "feature/rf-comm",
        "feature/sys-deploy",
        "feature/qa-test"
    ]
    db.clos = {
        "CT1": CourseLearningOutcome("CT1", "故障分析与定位能力", weight=0.25, target_threshold=0.70, actual_attainment=0.82),
        "CT2": CourseLearningOutcome("CT2", "方案多维权衡能力", weight=0.25, target_threshold=0.70, actual_attainment=0.79),
        "CT3": CourseLearningOutcome("CT3", "测试用例与系统验证能力", weight=0.25, target_threshold=0.70, actual_attainment=0.84),
        "CT4": CourseLearningOutcome("CT4", "AIGC批判性工程判断力", weight=0.25, target_threshold=0.70, actual_attainment=0.76)
    }
    flagged_ids = [
        ("EI032", 89, 52, 84, 65, "Group_03", 0),
        ("EI047", 87, 55, 81, 68, "Group_07", 1),
        ("EI061", 91, 58, 88, 62, "Group_11", 2),
        ("EI014", 88, 54, 82, 60, "Group_02", 3),
        ("EI022", 86, 57, 79, 64, "Group_04", 4),
        ("EI039", 90, 56, 85, 63, "Group_05", 0),
        ("EI053", 85, 51, 80, 66, "Group_08", 1),
        ("EI067", 88, 59, 83, 61, "Group_10", 2),
        ("EI074", 86, 53, 81, 67, "Group_12", 3),
        ("EI081", 89, 58, 84, 62, "Group_14", 4),
        ("EI086", 87, 52, 82, 65, "Group_15", 0),
        ("EI090", 92, 57, 89, 60, "Group_16", 1),
        ("EI093", 86, 55, 80, 64, "Group_17", 2),
        ("EI095", 88, 50, 83, 63, "Group_18", 3)
    ]
    random_sample_ids = ["EI008", "EI019", "EI025", "EI042", "EI055", "EI068", "EI077", "EI089"]
    for i in range(1, 96):
        sid = f"EI{i:03d}"
        grp_idx = (i - 1) // 5 + 1
        role_idx = (i - 1) % 5
        db.students[sid] = Student(
            student_id=sid,
            name=f"学生_{i:02d}",
            group_id=f"Group_{grp_idx:02d}",
            role_name=roles[role_idx],
            git_branch=branches[role_idx],
            commit_sha=f"{random.randint(0x10000000, 0xFFFFFFFF):08x}"
        )
    for idx, (sid, t, vi, p, vai, grp, r_idx) in enumerate(flagged_ids):
        rec = ScoreRecord(student_id=sid, t_score=float(t), p_score=float(p), v_i_score=float(vi), v_ai_score=float(vai), review_status="AGREED", variant_task_assigned=True, retest_passed=bool(idx < 12))
        rec.calculate_discrepancy(tau_t=85.0, tau_v=60.0)
        calculate_student_clo_score(rec)
        db.records[sid] = rec
    for idx, sid in enumerate(random_sample_ids):
        status = "AGREED" if idx != 0 else "PASSED_WITHOUT_ACTION"
        rec = ScoreRecord(student_id=sid, t_score=83.0, p_score=82.0, v_i_score=78.0, v_ai_score=76.0, is_random_sample=True, review_status=status, variant_task_assigned=False, retest_passed=None)
        rec.calculate_discrepancy(tau_t=85.0, tau_v=60.0)
        calculate_student_clo_score(rec)
        db.records[sid] = rec
    flagged_set = set([x[0] for x in flagged_ids] + random_sample_ids)
    for i in range(1, 96):
        sid = f"EI{i:03d}"
        if sid in flagged_set:
            continue
        rec = ScoreRecord(student_id=sid, t_score=85.0, p_score=80.0, v_i_score=78.0, v_ai_score=75.0, is_random_sample=False, needs_review=False, review_status="PENDING", variant_task_assigned=False)
        rec.calculate_discrepancy(tau_t=85.0, tau_v=60.0)
        calculate_student_clo_score(rec)
        db.records[sid] = rec
