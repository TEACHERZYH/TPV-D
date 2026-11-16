# -*- coding: utf-8 -*-
import numpy as np
from typing import List, Dict
try:
    from .models import ScoreRecord, CourseLearningOutcome
except Exception:
    from models import ScoreRecord, CourseLearningOutcome

def calculate_student_clo_score(record: ScoreRecord) -> Dict[str, float]:
    def to_level_score(score_100):
        return (score_100 / 100.0) * 3.0
    
    s_t = to_level_score(record.t_score)
    s_p = to_level_score(record.p_score)
    s_vi = to_level_score(record.v_i_score)
    s_vai = to_level_score(record.v_ai_score)
    
    clo_scores = {}
    
    # CT1
    w_ct1 = [0.5, 0.3, 0.2]
    items_ct1 = [s_vi, s_t, s_p]
    clo_scores["CT1"] = round((100.0 / 3.0) * sum(w * s for w, s in zip(w_ct1, items_ct1)), 2)
    
    # CT2
    w_ct2 = [0.5, 0.3, 0.2]
    items_ct2 = [s_p, s_t, s_vi]
    clo_scores["CT2"] = round((100.0 / 3.0) * sum(w * s for w, s in zip(w_ct2, items_ct2)), 2)
    
    # CT3
    w_ct3 = [0.4, 0.3, 0.3]
    items_ct3 = [s_t, s_t, s_vi]
    clo_scores["CT3"] = round((100.0 / 3.0) * sum(w * s for w, s in zip(w_ct3, items_ct3)), 2)
    
    # CT4
    w_ct4 = [0.6, 0.3, 0.1]
    items_ct4 = [s_vai, s_p, s_t]
    clo_scores["CT4"] = round((100.0 / 3.0) * sum(w * s for w, s in zip(w_ct4, items_ct4)), 2)
    
    record.clo_scores = clo_scores
    return clo_scores

def calculate_cohort_attainment(records: List[ScoreRecord]) -> Dict[str, float]:
    N = len(records)
    if N == 0:
        return {"CT1": 0.0, "CT2": 0.0, "CT3": 0.0, "CT4": 0.0}
    totals = {"CT1": 0.0, "CT2": 0.0, "CT3": 0.0, "CT4": 0.0}
    for r in records:
        if not r.clo_scores:
            calculate_student_clo_score(r)
        for clo_id in totals:
            totals[clo_id] += r.clo_scores.get(clo_id, 0.0)
    return {k: round(v / (100.0 * N), 2) for k, v in totals.items()}
