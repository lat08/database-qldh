import random
from collections import defaultdict
from .config import *

def create_student_enrollments(self):
    """
    UPDATED: Handle draft and official grades based on course_class grade submission status
    - Approved classes: Official grades populated, no drafts
    - Pending classes: Draft grades populated, no official grades yet
    - Draft classes: Some may have draft grades in progress
    """
    self.add_statement("\n-- ==================== STUDENT COURSE ENROLLMENTS (WITH DRAFT GRADES) ====================")
    self.add_statement("-- Approved classes: Official grades | Pending/Draft classes: Draft grades")
    self.add_statement("-- Senior students (2021-2022) complete 100% of curriculum requirements")
    
    enrollment_rows = []
    self.data['enrollments'] = []
    enrolled_combinations = set()
    
    # Group course_classes by (course_id, semester_id)
    course_classes_by_course_semester = defaultdict(list)
    for cc in self.data['course_classes']:
        key = (cc['course_id'], cc['semester_id'])
        course_classes_by_course_semester[key].append(cc)
    
    # Build index: subject_id -> list of courses
    courses_by_subject = defaultdict(list)
    for course in self.data['courses']:
        courses_by_subject[course['subject_id']].append(course)
    
    # Grade ranges
    att_min = 7.0
    att_max = 10.0
    mid_min = 5.0
    mid_max = 9.5
    fin_min = 5.0
    fin_max = 9.5
    
    student_schedules = defaultdict(lambda: defaultdict(list))
    conflict_count = 0
    skipped_count = 0
    forced_enrollment_count = 0
    
    # Track statistics
    students_with_full_curriculum = 0
    total_senior_students = 0
    
    draft_grade_stats = {
        'official_only': 0,      # Approved classes
        'draft_only': 0,          # Pending classes
        'both': 0,                # Should not happen
        'neither': 0              # No grades yet
    }

    for student in self.data['students']:
        class_id = student['class_id']
        cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
        if not cls:
            continue
        
        # NEW: Get curriculum subjects via curriculum_id
        curriculum_id = cls.get('curriculum_id')
        if not curriculum_id:
            self.add_statement(f"-- WARNING: Class {cls.get('class_code')} has no curriculum_id")
            continue
        
        # Get all subjects in this curriculum via curriculum_details
        curriculum_subject_ids = set()
        for cd in self.data.get('curriculum_details', []):
            if cd['curriculum_id'] == curriculum_id:
                curriculum_subject_ids.add(cd['subject_id'])
        
        if not curriculum_subject_ids:
            self.add_statement(f"-- WARNING: No subjects found for curriculum {curriculum_id}")
            continue
        
        is_fixed = student.get('is_fixed', False)
        student_start_year = student['class_start_year']
        
        # Determine if senior
        is_senior = student_start_year <= 2022
        if is_senior:
            total_senior_students += 1
        
        enrolled_subjects_for_student = set()
        
        # =================================================================
        # PHASE 1: NORMAL ENROLLMENT
        # =================================================================
        for course in self.data['courses']:
            if course['subject_id'] not in curriculum_subject_ids:
                continue
            if course['start_year'] < student_start_year:
                continue
            
            # Skip future courses for non-seniors
            if not is_senior:
                if course['start_year'] > 2025:
                    continue
                if course['start_year'] == 2025 and course['semester_type'] == 'summer':
                    continue
            
            key = (course['course_id'], course['semester_id'])
            available_classes = course_classes_by_course_semester.get(key, [])
            if not available_classes:
                continue
            
            # Find conflict-free section
            assigned_course_class = None
            for cc in available_classes:
                enrollment_key = (student['student_id'], cc['course_class_id'])
                if enrollment_key in enrolled_combinations:
                    continue
                
                # Check schedule conflicts
                has_conflict = False
                semester_schedule = student_schedules[student['student_id']][cc['semester_id']]
                
                for day in cc['days']:
                    for existing_schedule in semester_schedule:
                        existing_day, existing_start, existing_end = existing_schedule
                        if day == existing_day:
                            if not (cc['end_period'] < existing_start or cc['start_period'] > existing_end):
                                has_conflict = True
                                conflict_count += 1
                                break
                    if has_conflict:
                        break
                
                if not has_conflict and cc['enrolled_count'] < cc['max_students']:
                    assigned_course_class = cc
                    cc['enrolled_count'] += 1
                    break
            
            if not assigned_course_class:
                if not is_senior:
                    skipped_count += 1
                continue
            
            # Mark as enrolled
            enrollment_key = (student['student_id'], assigned_course_class['course_class_id'])
            enrolled_combinations.add(enrollment_key)
            enrolled_subjects_for_student.add(course['subject_id'])
            
            # Add to schedule
            for day in assigned_course_class['days']:
                student_schedules[student['student_id']][assigned_course_class['semester_id']].append((
                    day,
                    assigned_course_class['start_period'],
                    assigned_course_class['end_period']
                ))
            
            enrollment_id = self.generate_uuid()
            
            # Determine grade placement based on course_class grade_submission_status
            grade_status = assigned_course_class.get('grade_submission_status', 'draft')
            
            is_past = (course['start_year'] < 2025) or \
                     (course['start_year'] == 2025 and course['semester_type'] == 'spring')
            is_current = (course['start_year'] == 2025 and course['semester_type'] == 'fall')
            
            # Initialize grade columns
            attendance = None
            midterm = None
            final = None
            attendance_draft = None
            midterm_draft = None
            final_draft = None
            status = 'registered'
            
            if grade_status == 'approved':
                # Grades are official - populate official columns only
                if is_past or (is_senior and not is_current):
                    # Completed courses with passing grades
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(max(mid_min, 5.5), mid_max), 2)
                    final = round(random.uniform(max(fin_min, 6.0), fin_max), 2)
                    status = 'completed'
                    draft_grade_stats['official_only'] += 1
                elif is_current:
                    # Current approved - has midterm
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(mid_min, mid_max), 2)
                    final = None
                    status = 'registered'
                    draft_grade_stats['official_only'] += 1
            
            elif grade_status == 'pending':
                # Grades submitted but not approved - populate draft columns only
                if is_current:
                    rand = random.random()
                    if rand < 0.85:
                        # Most have drafts ready for approval
                        attendance_draft = round(random.uniform(att_min, att_max), 2)
                        midterm_draft = round(random.uniform(mid_min, mid_max), 2)
                        final_draft = None
                        draft_grade_stats['draft_only'] += 1
                    else:
                        # Some still incomplete
                        attendance_draft = round(random.uniform(att_min, att_max), 2)
                        midterm_draft = None
                        final_draft = None
                        draft_grade_stats['draft_only'] += 1
                    status = 'registered'
            
            elif grade_status == 'draft':
                # Still working on grades - draft columns
                if is_current and not is_fixed:
                    rand = random.random()
                    if rand < 0.40:
                        # Some progress on drafts
                        attendance_draft = round(random.uniform(att_min, att_max), 2)
                        midterm_draft = round(random.uniform(mid_min, mid_max), 2)
                        final_draft = None
                        draft_grade_stats['draft_only'] += 1
                    elif rand < 0.70:
                        # Partial progress
                        attendance_draft = round(random.uniform(att_min, att_max), 2)
                        midterm_draft = None
                        final_draft = None
                        draft_grade_stats['draft_only'] += 1
                    else:
                        # No grades entered yet
                        draft_grade_stats['neither'] += 1
                    status = 'registered'
                elif is_current and is_fixed:
                    # Fixed student always has draft grades
                    attendance_draft = round(random.uniform(7.5, 9.5), 2)
                    midterm_draft = round(random.uniform(6.5, 9.0), 2)
                    final_draft = None
                    draft_grade_stats['draft_only'] += 1
                    status = 'registered'
                elif is_past:
                    # Past courses should have been approved already
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(max(mid_min, 5.5), mid_max), 2)
                    final = round(random.uniform(max(fin_min, 6.0), fin_max), 2)
                    status = 'completed'
                    draft_grade_stats['official_only'] += 1
            
            enrollment_rows.append([
                enrollment_id,
                student['student_id'],
                assigned_course_class['course_class_id'],
                course['semester_start'],
                status,
                None, None,  # cancellation_date, cancellation_reason
                attendance, midterm, final,
                attendance_draft, midterm_draft, final_draft
            ])
            
            self.data['enrollments'].append({
                'enrollment_id': enrollment_id,
                'student_id': student['student_id'],
                'course_class_id': assigned_course_class['course_class_id'],
                'course_id': course['course_id'],
                'semester_id': course['semester_id'],
                'credits': course['credits'],
                'enrollment_date': course['semester_start'],
                'status': status
            })
        
        # =================================================================
        # PHASE 2: FORCE-ENROLL SENIORS IN MISSING SUBJECTS
        # =================================================================
        if is_senior:
            missing_subjects = curriculum_subject_ids - enrolled_subjects_for_student
            
            if not missing_subjects:
                students_with_full_curriculum += 1
            
            for subject_id in missing_subjects:
                available_courses = courses_by_subject.get(subject_id, [])
                if not available_courses:
                    self.add_statement(f"-- WARNING: No courses available for subject {subject_id}")
                    continue
                
                available_courses.sort(key=lambda c: (
                    c['start_year'],
                    {'fall': 1, 'spring': 2, 'summer': 3}[c['semester_type']]
                ))
                
                enrolled_in_missing = False
                for course in available_courses:
                    key = (course['course_id'], course['semester_id'])
                    available_classes = course_classes_by_course_semester.get(key, [])
                    if not available_classes:
                        continue
                    
                    for cc in available_classes:
                        enrollment_key = (student['student_id'], cc['course_class_id'])
                        if enrollment_key in enrolled_combinations:
                            continue
                        
                        # FORCE ENROLL
                        enrolled_combinations.add(enrollment_key)
                        enrolled_subjects_for_student.add(subject_id)
                        forced_enrollment_count += 1
                        
                        enrollment_id = self.generate_uuid()
                        
                        # All forced enrollments are completed with official grades
                        attendance = round(random.uniform(7.0, 9.5), 2)
                        midterm = round(random.uniform(5.5, 8.5), 2)
                        final = round(random.uniform(6.0, 9.0), 2)
                        status = 'completed'
                        
                        enrollment_rows.append([
                            enrollment_id,
                            student['student_id'],
                            cc['course_class_id'],
                            course['semester_start'],
                            status,
                            None, None,
                            attendance, midterm, final,
                            None, None, None  # No draft grades for completed
                        ])
                        
                        self.data['enrollments'].append({
                            'enrollment_id': enrollment_id,
                            'student_id': student['student_id'],
                            'course_class_id': cc['course_class_id'],
                            'course_id': course['course_id'],
                            'semester_id': course['semester_id'],
                            'credits': course['credits'],
                            'enrollment_date': course['semester_start'],
                            'status': status
                        })
                        
                        draft_grade_stats['official_only'] += 1
                        enrolled_in_missing = True
                        break
                    
                    if enrolled_in_missing:
                        break
                
                if not enrolled_in_missing:
                    self.add_statement(f"-- ERROR: Could not enroll senior {student['student_code']} in subject {subject_id}")
            
            # Final check
            if not (curriculum_subject_ids - enrolled_subjects_for_student):
                students_with_full_curriculum += 1

    # Statistics
    self.add_statement(f"\n-- ========================================")
    self.add_statement(f"-- ENROLLMENT SUMMARY")
    self.add_statement(f"-- ========================================")
    self.add_statement(f"-- Total enrollments: {len(enrollment_rows)}")
    self.add_statement(f"-- Normal enrollments: {len(enrollment_rows) - forced_enrollment_count}")
    self.add_statement(f"-- Forced enrollments (seniors): {forced_enrollment_count}")
    self.add_statement(f"-- Schedule conflicts detected: {conflict_count}")
    self.add_statement(f"-- Skipped (non-seniors): {skipped_count}")
    self.add_statement(f"-- ")
    self.add_statement(f"-- GRADE DISTRIBUTION:")
    self.add_statement(f"-- Official grades only (approved): {draft_grade_stats['official_only']}")
    self.add_statement(f"-- Draft grades only (pending/draft): {draft_grade_stats['draft_only']}")
    self.add_statement(f"-- No grades yet: {draft_grade_stats['neither']}")
    self.add_statement(f"-- ")
    self.add_statement(f"-- CURRICULUM COMPLETION:")
    self.add_statement(f"-- Total senior students: {total_senior_students}")
    self.add_statement(f"-- Seniors with 100% curriculum: {students_with_full_curriculum}")
    if total_senior_students > 0:
        completion_rate = (students_with_full_curriculum / total_senior_students * 100)
        self.add_statement(f"-- Completion rate: {completion_rate:.1f}%")
    
    self.bulk_insert('student_enrollment',
                    ['enrollment_id', 'student_id', 'course_class_id', 'enrollment_date',
                    'enrollment_status', 'cancellation_date', 'cancellation_reason',
                    'attendance_grade', 'midterm_grade', 'final_grade',
                    'attendance_grade_draft', 'midterm_grade_draft', 'final_grade_draft'],
                    enrollment_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_student_enrollments = create_student_enrollments