import random
from datetime import datetime
from .config import *

def create_subjects(self):
    """
    Create all subjects from spec (general + specialized)
    CRITICAL: Must set is_general flag and department_id correctly for curriculum_details to work
    """
    self.add_statement("\n-- ==================== SUBJECTS ====================")
    
    subject_rows = []
    
    # Get admin for created_by
    admin_id = self.data['fixed_accounts'].get('admin', {}).get('admin_id')
    
    # =========================================================================
    # GENERAL SUBJECTS (no department, is_general = True)
    # =========================================================================
    general_subjects = self.spec_data.get('general_subjects', [])
    
    self.add_statement(f"-- Creating {len(general_subjects)} general education subjects")
    
    for line in general_subjects:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 5:
            continue
            
        subject_name = parts[0]
        subject_code = parts[1]
        credits = int(parts[2])
        theory_hours = int(parts[3])
        practice_hours = int(parts[4])
        
        subject_id = self.generate_uuid()
        
        # Store in data with is_general = True and NO department_id
        self.data['subjects'].append({
            'subject_id': subject_id,
            'subject_code': subject_code,
            'subject_name': subject_name,
            'credits': credits,
            'theory_hours': theory_hours,
            'practice_hours': practice_hours,
            'is_general': True,  # CRITICAL FLAG
            'department_id': None,  # No department for general subjects
            'fee_per_credit': float(self.course_config.get('fee_per_credit', 600000))
        })
        
        # Find a random department to assign (for database constraint, but not used in logic)
        fallback_dept_id = self.data['departments'][0]['department_id'] if self.data['departments'] else None
        
        subject_rows.append([
            subject_id,
            subject_name,
            subject_code,
            credits,
            theory_hours,
            practice_hours,
            1,  # is_general = True
            fallback_dept_id,  # department_id (required by schema but not logically used)
            None,  # prerequisite_subject_id
            'active',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            None,
            admin_id,
            None,
            0,
            1
        ])

    # If the spec didn't provide enough general subjects, auto-generate a few
    # This ensures every curriculum has a healthy set of general subjects (useful for test students)
    MIN_GENERAL_SUBJECTS = int(self.spec_data.get('min_general_subjects', 8))
    existing_general_count = len([s for s in self.data['subjects'] if s.get('is_general')])
    if existing_general_count < MIN_GENERAL_SUBJECTS:
        needed = MIN_GENERAL_SUBJECTS - existing_general_count
        default_general_names = [
            'Toán đại cương', 'Vật lý đại cương', 'Hóa học đại cương', 'Tiếng Anh',
            'Giáo dục thể chất', 'Kỹ năng học tập', 'Tin học cơ bản', 'Kinh tế học cơ bản',
            'Lịch sử Việt Nam', 'Triết học Mác-Lênin'
        ]
        # Use existing fallback_dept_id for DB constraint but keep is_general True
        for i in range(needed):
            subject_name = default_general_names[i % len(default_general_names)] + (f" {i+1}" if i >= len(default_general_names) else "")
            subject_code = f"GEN{existing_general_count + i + 1:04d}"
            subject_id = self.generate_uuid()

            self.data['subjects'].append({
                'subject_id': subject_id,
                'subject_code': subject_code,
                'subject_name': subject_name,
                'credits': 3,
                'theory_hours': 30,
                'practice_hours': 0,
                'is_general': True,
                'department_id': None,
                'fee_per_credit': float(self.course_config.get('fee_per_credit', 600000))
            })

            subject_rows.append([
                subject_id,
                subject_name,
                subject_code,
                3,
                30,
                0,
                1,
                fallback_dept_id,
                None,
                'active',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                None,
                admin_id,
                None,
                0,
                1
            ])

        self.add_statement(f"-- Auto-generated {needed} general subjects to meet minimum ({MIN_GENERAL_SUBJECTS})")
    
    # =========================================================================
    # SPECIALIZED SUBJECTS (by department, is_general = False)
    # =========================================================================
    department_subjects = self.spec_data.get('department_subjects', [])
    
    self.add_statement(f"-- Creating {len(department_subjects)} specialized subjects")
    
    for line in department_subjects:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 6:
            continue
            
        dept_name = parts[0]
        subject_name = parts[1]
        subject_code = parts[2]
        credits = int(parts[3])
        theory_hours = int(parts[4])
        practice_hours = int(parts[5])
        
        # Find matching department
        dept = next((d for d in self.data['departments'] if d['department_name'] == dept_name), None)
        if not dept:
            self.add_statement(f"-- WARNING: Department '{dept_name}' not found for subject {subject_code}")
            continue
        
        subject_id = self.generate_uuid()
        
        # Store in data with is_general = False and correct department_id
        self.data['subjects'].append({
            'subject_id': subject_id,
            'subject_code': subject_code,
            'subject_name': subject_name,
            'credits': credits,
            'theory_hours': theory_hours,
            'practice_hours': practice_hours,
            'is_general': False,  # CRITICAL FLAG
            'department_id': dept['department_id'],  # CRITICAL - must match curriculum department
            'fee_per_credit': float(self.course_config.get('fee_per_credit', 600000))
        })
        
        subject_rows.append([
            subject_id,
            subject_name,
            subject_code,
            credits,
            theory_hours,
            practice_hours,
            0,  # is_general = False
            dept['department_id'],
            None,  # prerequisite_subject_id
            'active',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            None,
            admin_id,
            None,
            0,
            1
        ])
    
    self.add_statement(f"-- Total subjects created: {len(subject_rows)}")
    self.add_statement(f"--   General: {len(general_subjects)}")
    self.add_statement(f"--   Specialized: {len(department_subjects)}")
    
    if len(subject_rows) == 0:
        raise RuntimeError(
            "CRITICAL ERROR: No subjects created!\n"
            "CHECK: Verify [general_subjects] and [department_subjects] sections exist in spec file"
        )
    
    self.bulk_insert('subject',
                    ['subject_id', 'subject_name', 'subject_code', 'credits',
                     'theory_hours', 'practice_hours', 'is_general', 'department_id',
                     'prerequisite_subject_id', 'subject_status',
                     'created_at', 'updated_at', 'created_by', 'updated_by',
                     'is_deleted', 'is_active'],
                    subject_rows)

# Register function
from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_subjects = create_subjects