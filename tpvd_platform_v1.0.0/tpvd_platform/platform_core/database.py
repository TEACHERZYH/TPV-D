# -*- coding: utf-8 -*-
import json
import os
from typing import List, Dict, Optional
try:
    from .models import Student, ScoreRecord, CourseLearningOutcome, PlatformMetrics
    from .score_calculator import calculate_student_clo_score, calculate_cohort_attainment
    from .discrepancy_detector import detect_discrepancies, calculate_platform_efficiency
    from .seed_data import generate_paper_cohort_data
except Exception:
    from models import Student, ScoreRecord, CourseLearningOutcome, PlatformMetrics
    from score_calculator import calculate_student_clo_score, calculate_cohort_attainment
    from discrepancy_detector import detect_discrepancies, calculate_platform_efficiency
    from seed_data import generate_paper_cohort_data

class PlatformDatabase:
    def __init__(self, data_file="tpvd_platform/data/cohort_data.json"):
        self.data_file = data_file
        self.students: Dict[str, Student] = {}
        self.records: Dict[str, ScoreRecord] = {}
        self.clos: Dict[str, CourseLearningOutcome] = {}
        self.load_or_seed()
        
    def load_or_seed(self):
        if os.path.exists(self.data_file):
            try:
                self.load_from_json()
                return
            except Exception as e:
                pass
        generate_paper_cohort_data(self)
        self.save_to_json()
        
    def save_to_json(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.data_file)), exist_ok=True)
        data = {
            "students": {k: v.__dict__ for k, v in self.students.items()},
            "records": {k: v.__dict__ for k, v in self.records.items()},
            "clos": {k: v.__dict__ for k, v in self.clos.items()}
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def load_from_json(self):
        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.students = {k: Student(**v) for k, v in data["students"].items()}
        self.records = {k: ScoreRecord(**v) for k, v in data["records"].items()}
        self.clos = {k: CourseLearningOutcome(**v) for k, v in data["clos"].items()}

    def get_all_records(self) -> List[ScoreRecord]:
        return list(self.records.values())

    def get_record(self, student_id: str) -> Optional[ScoreRecord]:
        return self.records.get(student_id)

    def get_student(self, student_id: str) -> Optional[Student]:
        return self.students.get(student_id)

    def get_review_queue(self, tau_t=85.0, tau_v=60.0):
        review_q, _ = detect_discrepancies(self.get_all_records(), tau_t=tau_t, tau_v=tau_v)
        return review_q

    def get_platform_metrics(self) -> PlatformMetrics:
        review_q, _ = detect_discrepancies(self.get_all_records())
        return calculate_platform_efficiency(self.get_all_records(), review_q)

    def update_review_decision(self, student_id: str, status: str, assign_variant: bool, retest_passed: Optional[bool]):
        record = self.records.get(student_id)
        if record:
            record.review_status = status
            record.variant_task_assigned = assign_variant
            record.retest_passed = retest_passed
            if retest_passed:
                record.v_i_score = 75.0
                record.calculate_discrepancy()
                calculate_student_clo_score(record)
            self.save_to_json()
            return True
        return False
