from collections import defaultdict
from .config import *

def create_subjects(self):
    self.add_statement("\n-- ==================== SUBJECTS ====================")
    
    subject_rows = []
    
    # Get first department as default for general subjects
    default_dept_id = self.data['departments'][0]['department_id']
    
    # General subjects
    for line in self.spec_data.get('general_subjects', []):
        parts = [p.strip() for p in line.split('|')]
        subj_name, subj_code, credits, theory, practice = parts
        
        subject_id = self.generate_uuid()
        
        self.data['subjects'].append({
            'subject_id': subject_id,
            'subject_code': subj_code,
            'subject_name': subj_name,
            'credits': int(credits),
            'theory_hours': int(theory),
            'practice_hours': int(practice),
            'is_general': True
        })
        
        # FIXED: Changed 'status' to 'subject_status'
        subject_rows.append([subject_id, subj_name, subj_code, int(credits), int(theory), int(practice), 
                        True, default_dept_id, 'active'])
    
    # Department subjects
    for line in self.spec_data.get('department_subjects', []):
        parts = [p.strip() for p in line.split('|')]
        dept_name, subj_name, subj_code, credits, theory, practice = parts
        
        # Find department
        dept = next((d for d in self.data['departments'] if d['department_name'] == dept_name), None)
        if not dept:
            continue
        
        subject_id = self.generate_uuid()
        
        self.data['subjects'].append({
            'subject_id': subject_id,
            'subject_code': subj_code,
            'subject_name': subj_name,
            'credits': int(credits),
            'theory_hours': int(theory),
            'practice_hours': int(practice),
            'is_general': False,
            'department_id': dept['department_id']
        })
        
        # FIXED: Changed 'status' to 'subject_status'
        subject_rows.append([subject_id, subj_name, subj_code, int(credits), int(theory), int(practice), 
                        False, dept['department_id'], 'active'])
    
    # FIXED: Changed 'status' to 'subject_status'
    self.bulk_insert('subject', ['subject_id', 'subject_name', 'subject_code', 'credits', 'theory_hours', 
                                'practice_hours', 'is_general', 'department_id', 'subject_status'], subject_rows)

def create_curriculum_details(self):
    """
    UPDATED: curriculum_detail now links department -> subject -> semester
    NOT class -> subject -> semester
    """
    self.add_statement("\n-- ==================== CURRICULUM DETAILS ====================")
    
    curriculum_rows = []
    
    # Group subjects by department
    subjects_by_dept = defaultdict(list)
    for subject in self.data['subjects']:
        dept_id = subject.get('department_id')
        if dept_id:
            subjects_by_dept[dept_id].append(subject)
    
    # For each department, distribute subjects across semesters
    for dept_id, subjects in subjects_by_dept.items():
        # Get semesters (use recent years)
        recent_semesters = [s for s in self.data['semesters'] 
                        if s['start_year'] >= 2023]
        
        if not recent_semesters:
            continue
        
        # Distribute subjects across semesters (roughly 5-6 per semester)
        subjects_per_semester = 6
        semester_index = 0
        
        for i, subject in enumerate(subjects):
            if semester_index >= len(recent_semesters):
                semester_index = 0  # Wrap around
            
            semester = recent_semesters[semester_index]
            
            curriculum_detail_id = self.generate_uuid()
            curriculum_rows.append([
                curriculum_detail_id,
                dept_id,
                subject['subject_id'],
                semester['semester_id']
            ])
            
            # Move to next semester after distributing subjects
            if (i + 1) % subjects_per_semester == 0:
                semester_index += 1
    
    self.add_statement(f"-- Total curriculum details: {len(curriculum_rows)}")
    
    self.bulk_insert('curriculum_detail',
                    ['curriculum_detail_id', 'department_id', 'subject_id', 'semester_id'],
                    curriculum_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_subjects = create_subjects
SQLDataGenerator.create_curriculum_details = create_curriculum_details