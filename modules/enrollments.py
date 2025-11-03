import random
from collections import defaultdict
from .config import *

def create_student_enrollments(self):
    """
    UPDATED: New schema with separate tables for draft grades and grade versions
    - student_enrollment: Only tracks enrollment, no grades
    - enrollment_draft_grade: Draft grades being worked on by instructors
    - enrollment_grade_version: Version history of grade submissions per course_class
    - enrollment_grade_detail: Actual grades for each student in each version
    """
    self.add_statement("\n-- ==================== STUDENT COURSE ENROLLMENTS (NEW SCHEMA) ====================")
    self.add_statement("-- Phase 1: Create enrollments (no grades)")
    self.add_statement("-- Phase 2: Create draft grades for current courses")
    self.add_statement("-- Phase 3: Create grade versions for approved/pending submissions")
    self.add_statement("-- Senior students (2021-2022) complete 100% of curriculum requirements")
    
    enrollment_rows = []
    draft_grade_rows = []
    grade_version_rows = []
    grade_detail_rows = []
    
    self.data['enrollments'] = []
    self.data['grade_versions'] = {}  # course_class_id -> list of versions
    
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
    
    stats = {
        'total_enrollments': 0,
        'with_draft_grades': 0,
        'with_official_grades': 0,
        'no_grades_yet': 0
    }

    # =================================================================
    # PHASE 1: CREATE ENROLLMENTS FOR ALL STUDENTS
    # =================================================================
    for student in self.data['students']:
        class_id = student['class_id']
        cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
        if not cls:
            continue
        
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
        
        # Normal enrollment
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
            
            # Determine enrollment status
            is_past = (course['start_year'] < 2025) or \
                     (course['start_year'] == 2025 and course['semester_type'] == 'spring')
            is_current = (course['start_year'] == 2025 and course['semester_type'] == 'fall')
            
            status = 'completed' if is_past else 'registered'
            
            # Create enrollment record (NO GRADES HERE)
            enrollment_rows.append([
                enrollment_id,
                student['student_id'],
                assigned_course_class['course_class_id'],
                course['semester_start'],
                status,
                None, None  # cancellation_date, cancellation_reason
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
            
            stats['total_enrollments'] += 1
        
        # Force-enroll seniors in missing subjects
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
                        
                        # Create enrollment record
                        enrollment_rows.append([
                            enrollment_id,
                            student['student_id'],
                            cc['course_class_id'],
                            course['semester_start'],
                            'completed',
                            None, None
                        ])
                        
                        self.data['enrollments'].append({
                            'enrollment_id': enrollment_id,
                            'student_id': student['student_id'],
                            'course_class_id': cc['course_class_id'],
                            'course_id': course['course_id'],
                            'semester_id': course['semester_id'],
                            'credits': course['credits'],
                            'enrollment_date': course['semester_start'],
                            'status': 'completed'
                        })
                        
                        stats['total_enrollments'] += 1
                        enrolled_in_missing = True
                        break
                    
                    if enrolled_in_missing:
                        break
                
                if not enrolled_in_missing:
                    self.add_statement(f"-- ERROR: Could not enroll senior {student['student_code']} in subject {subject_id}")
            
            # Final check
            if not (curriculum_subject_ids - enrolled_subjects_for_student):
                students_with_full_curriculum += 1

    # =================================================================
    # PHASE 2: CREATE DRAFT GRADES FOR CURRENT COURSES
    # =================================================================
    self.add_statement(f"\n-- Creating draft grades for current semester courses...")
    
    for enrollment in self.data['enrollments']:
        course_class_id = enrollment['course_class_id']
        cc = next((c for c in self.data['course_classes'] if c['course_class_id'] == course_class_id), None)
        if not cc:
            continue
        
        grade_status = cc.get('grade_submission_status', 'draft')
        is_current = (cc['start_year'] == 2025 and cc['semester_type'] == 'fall')
        
        # Only create draft grades for current courses with draft/pending status
        if is_current and grade_status in ('draft', 'pending'):
            student = next((s for s in self.data['students'] if s['student_id'] == enrollment['student_id']), None)
            is_fixed = student.get('is_fixed', False) if student else False
            
            draft_grade_id = self.generate_uuid()
            
            attendance_draft = None
            midterm_draft = None
            final_draft = None
            
            if grade_status == 'pending':
                # Most pending classes have complete draft grades
                rand = random.random()
                if rand < 0.85:
                    attendance_draft = round(random.uniform(att_min, att_max), 2)
                    midterm_draft = round(random.uniform(mid_min, mid_max), 2)
                    final_draft = None
                else:
                    attendance_draft = round(random.uniform(att_min, att_max), 2)
                    midterm_draft = None
                    final_draft = None
            
            elif grade_status == 'draft':
                if is_fixed:
                    # Fixed student always has draft grades
                    attendance_draft = round(random.uniform(7.5, 9.5), 2)
                    midterm_draft = round(random.uniform(6.5, 9.0), 2)
                    final_draft = None
                else:
                    # Random progress on drafts
                    rand = random.random()
                    if rand < 0.40:
                        attendance_draft = round(random.uniform(att_min, att_max), 2)
                        midterm_draft = round(random.uniform(mid_min, mid_max), 2)
                        final_draft = None
                    elif rand < 0.70:
                        attendance_draft = round(random.uniform(att_min, att_max), 2)
                        midterm_draft = None
                        final_draft = None
                    # else: no grades yet
            
            # Only create record if at least one grade exists
            if attendance_draft is not None or midterm_draft is not None or final_draft is not None:
                draft_grade_rows.append([
                    draft_grade_id,
                    enrollment['enrollment_id'],
                    attendance_draft,
                    midterm_draft,
                    final_draft,
                    None  # updated_at
                ])
                stats['with_draft_grades'] += 1

    # =================================================================
    # PHASE 3: CREATE GRADE VERSIONS AND GRADE DETAILS
    # =================================================================
    self.add_statement(f"\n-- Creating grade versions for approved/pending submissions...")
    
    # Group enrollments by course_class
    enrollments_by_course_class = defaultdict(list)
    for enrollment in self.data['enrollments']:
        enrollments_by_course_class[enrollment['course_class_id']].append(enrollment)
    
    for cc in self.data['course_classes']:
        grade_status = cc.get('grade_submission_status', 'draft')
        
        # Only create grade versions for approved or pending submissions
        if grade_status not in ('approved', 'pending'):
            continue
        
        course_class_id = cc['course_class_id']
        enrollments = enrollments_by_course_class.get(course_class_id, [])
        
        if not enrollments:
            continue
        
        # Create grade version
        grade_version_id = self.generate_uuid()
        version_number = 1  # First version for now
        
        # Get instructor who submitted
        instructor_id = cc.get('instructor_id')
        submitted_at = cc.get('grade_submitted_at')
        submission_note = cc.get('grade_submission_note', 'Grade submission')
        
        # Get admin who approved (if approved)
        approved_by = cc.get('grade_approved_by') if grade_status == 'approved' else None
        approved_at = cc.get('grade_approved_at') if grade_status == 'approved' else None
        approval_note = cc.get('grade_approval_note') if grade_status == 'approved' else None
        
        grade_version_rows.append([
            grade_version_id,
            course_class_id,
            version_number,
            grade_status,
            instructor_id,
            submitted_at,
            submission_note,
            approved_by,
            approved_at,
            approval_note,
            submitted_at  # created_at = submitted_at
        ])
        
        # Track version
        if course_class_id not in self.data['grade_versions']:
            self.data['grade_versions'][course_class_id] = []
        self.data['grade_versions'][course_class_id].append({
            'grade_version_id': grade_version_id,
            'version_number': version_number,
            'status': grade_status
        })
        
        # Create grade details for each enrolled student
        for enrollment in enrollments:
            grade_detail_id = self.generate_uuid()
            
            # Generate official grades
            is_past = (cc['start_year'] < 2025) or \
                     (cc['start_year'] == 2025 and cc['semester_type'] == 'spring')
            is_current = (cc['start_year'] == 2025 and cc['semester_type'] == 'fall')
            
            attendance = None
            midterm = None
            final = None
            
            if grade_status == 'approved':
                if is_past:
                    # Completed courses with full grades
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(max(mid_min, 5.5), mid_max), 2)
                    final = round(random.uniform(max(fin_min, 6.0), fin_max), 2)
                elif is_current:
                    # Current approved - has midterm
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(mid_min, mid_max), 2)
                    final = None
            
            elif grade_status == 'pending':
                # Pending approval - similar to draft but submitted
                if is_current:
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(mid_min, mid_max), 2)
                    final = None
            
            grade_detail_rows.append([
                grade_detail_id,
                grade_version_id,
                enrollment['enrollment_id'],
                attendance,
                midterm,
                final
            ])
            
            if attendance is not None or midterm is not None or final is not None:
                stats['with_official_grades'] += 1

    # Calculate no grades yet
    stats['no_grades_yet'] = stats['total_enrollments'] - stats['with_draft_grades'] - stats['with_official_grades']

    # Statistics
    self.add_statement(f"\n-- ========================================")
    self.add_statement(f"-- ENROLLMENT SUMMARY")
    self.add_statement(f"-- ========================================")
    self.add_statement(f"-- Total enrollments: {stats['total_enrollments']}")
    self.add_statement(f"-- Normal enrollments: {stats['total_enrollments'] - forced_enrollment_count}")
    self.add_statement(f"-- Forced enrollments (seniors): {forced_enrollment_count}")
    self.add_statement(f"-- Schedule conflicts detected: {conflict_count}")
    self.add_statement(f"-- Skipped (non-seniors): {skipped_count}")
    self.add_statement(f"-- ")
    self.add_statement(f"-- GRADE DISTRIBUTION:")
    self.add_statement(f"-- With official grades: {stats['with_official_grades']}")
    self.add_statement(f"-- With draft grades only: {stats['with_draft_grades']}")
    self.add_statement(f"-- No grades yet: {stats['no_grades_yet']}")
    self.add_statement(f"-- ")
    self.add_statement(f"-- GRADE VERSIONS:")
    self.add_statement(f"-- Total grade versions created: {len(grade_version_rows)}")
    self.add_statement(f"-- Total grade details created: {len(grade_detail_rows)}")
    self.add_statement(f"-- ")
    self.add_statement(f"-- CURRICULUM COMPLETION:")
    self.add_statement(f"-- Total senior students: {total_senior_students}")
    self.add_statement(f"-- Seniors with 100% curriculum: {students_with_full_curriculum}")
    if total_senior_students > 0:
        completion_rate = (students_with_full_curriculum / total_senior_students * 100)
        self.add_statement(f"-- Completion rate: {completion_rate:.1f}%")
    
    # Insert data
    self.bulk_insert('student_enrollment',
                    ['enrollment_id', 'student_id', 'course_class_id', 'enrollment_date',
                     'enrollment_status', 'cancellation_date', 'cancellation_reason'],
                    enrollment_rows)
    
    if draft_grade_rows:
        self.bulk_insert('enrollment_draft_grade',
                        ['draft_grade_id', 'enrollment_id', 'attendance_grade_draft',
                         'midterm_grade_draft', 'final_grade_draft', 'updated_at'],
                        draft_grade_rows)
    
    if grade_version_rows:
        self.bulk_insert('enrollment_grade_version',
                        ['grade_version_id', 'course_class_id', 'version_number', 'version_status',
                         'submitted_by', 'submitted_at', 'submission_note',
                         'approved_by', 'approved_at', 'approval_note', 'created_at'],
                        grade_version_rows)
    
    if grade_detail_rows:
        self.bulk_insert('enrollment_grade_detail',
                        ['grade_detail_id', 'grade_version_id', 'enrollment_id',
                         'attendance_grade', 'midterm_grade', 'final_grade'],
                        grade_detail_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_student_enrollments = create_student_enrollments