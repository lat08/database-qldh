import random
from collections import defaultdict
from .config import *

def create_student_enrollments(self):
    """
    UPDATED: Track enrollment IDs and course info for payment generation
    Fixed: Added deduplication to prevent UNIQUE constraint violations
    """
    self.add_statement("\n-- ==================== STUDENT COURSE ENROLLMENTS (REALISTIC & MASSIVE) ====================")
    self.add_statement("-- Students enrolled with STRICT schedule conflict checking")
    self.add_statement("-- Fixed STUDENT account gets deterministic grades for testing")
    
    enrollment_rows = []
    
    # IMPORTANT: Initialize enrollments list to track IDs and course info
    self.data['enrollments'] = []
    
    # Track enrollments to prevent duplicates: (student_id, course_class_id) -> True
    enrolled_combinations = set()
    
    # Group course_classes by course_id
    course_classes_by_course = defaultdict(list)
    for cc in self.data['course_classes']:
        course_classes_by_course[cc['course_id']].append(cc)
    
    att_min = float(self.enrollment_config.get('attendance_min', 7.0))
    att_max = float(self.enrollment_config.get('attendance_max', 10.0))
    mid_min = float(self.enrollment_config.get('midterm_min', 5.0))
    mid_max = float(self.enrollment_config.get('midterm_max', 9.5))
    fin_min = float(self.enrollment_config.get('final_min', 5.0))
    fin_max = float(self.enrollment_config.get('final_max', 9.5))
    
    # Track each student's schedule: student_id -> {semester_id: [(day, start_period, end_period), ...]}
    student_schedules = defaultdict(lambda: defaultdict(list))
    
    conflict_count = 0
    skipped_count = 0
    duplicate_count = 0
    
    for student in self.data['students']:
        class_id = student['class_id']
        cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
        if not cls or 'curriculum' not in cls:
            continue
        
        curriculum_subject_ids = {s['subject_id'] for s in cls['curriculum']}
        is_fixed = student.get('is_fixed', False)
        student_start_year = student['class_start_year']
        
        # Get all courses this student should take
        student_courses = []
        for course in self.data['courses']:
            if course['subject_id'] not in curriculum_subject_ids:
                continue
            
            # Only enroll in courses at or after student's start year
            if course['start_year'] < student_start_year:
                continue
            
            # Don't enroll in future semesters (after Fall 2025)
            if course['start_year'] > 2025:
                continue
            if course['start_year'] == 2025 and course['semester_type'] == 'summer':
                continue  # Skip summer 2025 (future)
            
            student_courses.append(course)
        
        # Sort courses by semester for proper scheduling
        semester_order = {'fall': 1, 'spring': 2, 'summer': 3}
        student_courses.sort(key=lambda c: (c['start_year'], semester_order.get(c['semester_type'], 0)))
        
        for course in student_courses:
            # Find available course_class sections for this course
            available_classes = course_classes_by_course.get(course['course_id'], [])
            if not available_classes:
                continue
            
            # Try to find a course_class section without schedule conflicts
            assigned_course_class = None
            
            for cc in available_classes:
                # CHECK FOR DUPLICATE ENROLLMENT FIRST
                enrollment_key = (student['student_id'], cc['course_class_id'])
                if enrollment_key in enrolled_combinations:
                    duplicate_count += 1
                    continue
                
                # Check if this course_class conflicts with student's existing schedule IN THIS SEMESTER
                has_conflict = False
                
                semester_schedule = student_schedules[student['student_id']][cc['semester_id']]
                
                # Check each day this course_class meets
                for day in cc['days']:
                    for existing_schedule in semester_schedule:
                        existing_day, existing_start, existing_end = existing_schedule
                        
                        # Check if same day
                        if day == existing_day:
                            # Check time overlap
                            if not (cc['end_period'] < existing_start or cc['start_period'] > existing_end):
                                has_conflict = True
                                conflict_count += 1
                                break
                    
                    if has_conflict:
                        break
                
                # Check if section is full
                if not has_conflict:
                    if cc['enrolled_count'] < cc['max_students']:
                        assigned_course_class = cc
                        cc['enrolled_count'] += 1
                        break
            
            # If NO conflict-free section found, SKIP this enrollment
            if not assigned_course_class:
                skipped_count += 1
                if is_fixed:
                    self.add_statement(f"-- SKIPPED: STUDENT (fixed) - {course['subject_code']} in {course['start_year']} {course['semester_type']} (No conflict-free section)")
                continue
            
            # MARK AS ENROLLED (prevent duplicates)
            enrollment_key = (student['student_id'], assigned_course_class['course_class_id'])
            enrolled_combinations.add(enrollment_key)
            
            # Add to student's schedule for THIS SEMESTER
            for day in assigned_course_class['days']:
                student_schedules[student['student_id']][assigned_course_class['semester_id']].append((
                    day,
                    assigned_course_class['start_period'],
                    assigned_course_class['end_period']
                ))
            
            enrollment_id = self.generate_uuid()
            
            # Determine if this is a past, current, or future semester
            is_past_semester = (course['start_year'] < 2025) or \
                            (course['start_year'] == 2025 and course['semester_type'] == 'spring')
            is_current_semester = (course['start_year'] == 2025 and course['semester_type'] == 'fall')
            
            if is_fixed:
                # FIXED STUDENT ACCOUNT - DETERMINISTIC GRADES
                if is_past_semester:
                    # ALL past semesters: COMPLETED with full grades
                    attendance = round(random.uniform(7.5, 9.5), 2)
                    midterm = round(random.uniform(6.5, 9.0), 2)
                    final = round(random.uniform(7.0, 9.5), 2)
                    status = 'completed'
                    
                elif is_current_semester:
                    # Fall 2025: IN PROGRESS - ALL have attendance + midterm, NO finals
                    attendance = round(random.uniform(7.5, 9.5), 2)
                    midterm = round(random.uniform(6.5, 9.0), 2)
                    final = None
                    status = 'registered'
                    
                else:
                    # Future semesters: SKIP
                    continue
                    
            else:
                # REGULAR STUDENTS - VARIED GRADES
                if is_past_semester:
                    # Past semesters: Completed with full grades
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(mid_min, mid_max), 2)
                    final = round(random.uniform(fin_min, fin_max), 2)
                    status = 'completed'
                    
                elif is_current_semester:
                    # Fall 2025: In progress - varied completion
                    rand = random.random()
                    if rand < 0.60:  # 60% have midterm done
                        attendance = round(random.uniform(att_min, att_max), 2)
                        midterm = round(random.uniform(mid_min, mid_max), 2)
                        final = None
                    elif rand < 0.85:  # 25% have only attendance
                        attendance = round(random.uniform(att_min, att_max), 2)
                        midterm = None
                        final = None
                    else:  # 15% not started
                        attendance = None
                        midterm = None
                        final = None
                    status = 'registered'
                    
                else:
                    # Future semesters: SKIP
                    continue
            
            # Insert enrollment
            enrollment_rows.append([
                enrollment_id,
                student['student_id'],
                assigned_course_class['course_class_id'],
                course['semester_start'],
                status,
                None,  # cancellation_date
                None,  # cancellation_reason
                attendance,
                midterm,
                final
            ])
            
            # STORE enrollment data for payment generation (with course info)
            self.data['enrollments'].append({
                'enrollment_id': enrollment_id,
                'student_id': student['student_id'],
                'course_class_id': assigned_course_class['course_class_id'],
                'course_id': course['course_id'],  # Store course_id
                'semester_id': course['semester_id'],  # Store semester_id
                'credits': course['credits'],
                'enrollment_date': course['semester_start'],
                'status': status
            })
            
            # Log fixed student enrollments for debugging
            if is_fixed:
                grade_status = "FULL GRADES" if final is not None else \
                            "ATT+MID" if midterm is not None else \
                            "ATT ONLY" if attendance is not None else "NO GRADES"
                self.add_statement(f"-- ENROLLED: STUDENT (fixed) - {course['subject_code']} - {course['start_year']} {course['semester_type']} - {grade_status}")
    
    self.add_statement(f"\n-- ========================================")
    self.add_statement(f"-- ENROLLMENT SUMMARY")
    self.add_statement(f"-- ========================================")
    self.add_statement(f"-- Total enrollments created: {len(enrollment_rows)}")
    self.add_statement(f"-- Schedule conflicts detected: {conflict_count}")
    self.add_statement(f"-- Duplicate enrollments prevented: {duplicate_count}")
    self.add_statement(f"-- Enrollments skipped (no conflict-free slot): {skipped_count}")
    
    # REMOVED is_paid column from insert
    self.bulk_insert('student_enrollment',
                    ['enrollment_id', 'student_id', 'course_class_id', 'enrollment_date',
                    'enrollment_status', 'cancellation_date', 'cancellation_reason',
                    'attendance_grade', 'midterm_grade', 'final_grade'],
                    enrollment_rows)


from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_student_enrollments = create_student_enrollments