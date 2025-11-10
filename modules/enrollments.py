import random
from collections import defaultdict
from .config import *

def create_student_enrollments(self):
    """
    FIXED: Better enrollment distribution
    - Enrollments distributed more evenly across sections
    - Students enroll in available seats randomly
    - Better tracking of enrolled_count
    """
    self.add_statement("\n-- ==================== STUDENT COURSE ENROLLMENTS (FIXED) ====================")
    self.add_statement("-- More balanced enrollment distribution")
    self.add_statement("-- Enrollment cutoff: Fall 2025")
    
    enrollment_rows = []
    draft_grade_rows = []
    grade_version_rows = []
    grade_detail_rows = []
    
    self.data['enrollments'] = []
    self.data['grade_versions'] = {}
    
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
    
    students_with_full_curriculum = 0
    total_senior_students = 0
    
    stats = {
        'total_enrollments': 0,
        'enrolled_students': 0,
        'not_enrolled': 0,
        'with_draft_grades': 0,
        'with_official_grades': 0,
        'no_grades_yet': 0
    }

    # PHASE 1: CREATE ENROLLMENTS
    for student in self.data['students']:
        class_id = student['class_id']
        cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
        if not cls:
            continue
        
        curriculum_id = cls.get('curriculum_id')
        if not curriculum_id:
            continue
        
        curriculum_subject_ids = set()
        for cd in self.data.get('curriculum_details', []):
            if cd['curriculum_id'] == curriculum_id:
                curriculum_subject_ids.add(cd['subject_id'])
        
        if not curriculum_subject_ids:
            continue
        
        is_fixed = student.get('is_fixed', False)
        student_start_year = student['class_start_year']
        
        is_senior = student_start_year <= 2022
        if is_senior:
            total_senior_students += 1
        
        enrolled_subjects_for_student = set()
        student_has_enrolled = False
        
        # Get all eligible courses for this student
        # Eligible courses include:
        # - Past semesters (start_year < 2025) - all types (fall, spring, summer)
        # - Spring 2024-2025 (start_year == 2024, semester_type == 'spring') - past/completed
        # - Summer 2024-2025 (start_year == 2024, semester_type == 'summer') - current/ongoing
        # - Fall 2025 (start_year == 2025, semester_type == 'fall') - current registration period
        # Exclude:
        # - Future semesters (start_year > 2025)
        # - Spring/Summer 2025 (start_year == 2025, semester_type in ('spring', 'summer')) - future
        eligible_courses = []
        for course in self.data['courses']:
            if course['subject_id'] not in curriculum_subject_ids:
                continue
            if course['start_year'] < student_start_year:
                continue
            if course['start_year'] > 2025:
                continue
            # Exclude Spring/Summer 2025 (future semesters)
            if course['start_year'] == 2025 and course['semester_type'] in ('spring', 'summer'):
                continue
            # Include all other courses (past and current semesters)
            eligible_courses.append(course)
        
        # FIXED: Prioritize summer 2024-2025 and current semester courses
        # Separate summer 2024-2025 and fall 2025 courses from others
        summer_2024_2025_courses = [c for c in eligible_courses 
                                     if c['start_year'] == 2024 and c['semester_type'] == 'summer']
        fall_2025_courses = [c for c in eligible_courses 
                            if c['start_year'] == 2025 and c['semester_type'] == 'fall']
        other_courses = [c for c in eligible_courses 
                        if c not in summer_2024_2025_courses and c not in fall_2025_courses]
        
        # Shuffle each group separately
        random.shuffle(summer_2024_2025_courses)
        random.shuffle(fall_2025_courses)
        random.shuffle(other_courses)
        
        # Prioritize: summer 2024-2025 > fall 2025 > others
        prioritized_courses = summer_2024_2025_courses + fall_2025_courses + other_courses
        
        # SPECIAL HANDLING FOR TEST STUDENT: Enroll in more past courses
        test_student_id = self.data['fixed_accounts'].get('student', {}).get('student_id')
        is_test_student = student['student_id'] == test_student_id if test_student_id else False
        
        # FIXED: Enroll in ~70% of eligible courses, but ensure summer 2024-2025 courses are prioritized
        # For test student, enroll in ~90% of eligible courses to ensure more past enrollments
        enrollment_rate = 0.9 if is_test_student else 0.7
        num_to_enroll = int(len(eligible_courses) * enrollment_rate)
        # Ensure at least some summer 2024-2025 courses are enrolled if available
        if summer_2024_2025_courses and not is_senior:
            # Enroll in at least 50% of summer 2024-2025 courses
            min_summer_enroll = max(1, int(len(summer_2024_2025_courses) * 0.5))
            num_to_enroll = max(num_to_enroll, min_summer_enroll + len(fall_2025_courses))
        
        # For test student, ensure they enroll in most past courses (prioritize past over current)
        if is_test_student:
            # Separate past courses (completed) from current courses
            past_courses = [c for c in other_courses if c['start_year'] < 2024 or 
                           (c['start_year'] == 2024 and c['semester_type'] in ('fall', 'spring'))]
            current_courses = summer_2024_2025_courses + fall_2025_courses
            
            # Enroll in ~95% of past courses and all current courses
            past_enroll_count = int(len(past_courses) * 0.95)
            num_to_enroll = max(num_to_enroll, past_enroll_count + len(current_courses))
            # Re-prioritize: past courses first, then current
            prioritized_courses = past_courses + current_courses
        
        courses_to_enroll = prioritized_courses[:num_to_enroll] if not is_senior else prioritized_courses
        
        for course in courses_to_enroll:
            key = (course['course_id'], course['semester_id'])
            available_classes = course_classes_by_course_semester.get(key, [])
            if not available_classes:
                continue
            
            # FIXED: Shuffle sections to distribute enrollment evenly
            random.shuffle(available_classes)
            
            # Find conflict-free section with available space
            assigned_course_class = None
            for cc in available_classes:
                enrollment_key = (student['student_id'], cc['course_class_id'])
                if enrollment_key in enrolled_combinations:
                    continue
                
                # Check if class is full
                if cc['enrolled_count'] >= cc['max_students']:
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
                
                if not has_conflict:
                    assigned_course_class = cc
                    cc['enrolled_count'] += 1  # FIXED: Properly track enrollment
                    break
            
            if not assigned_course_class:
                if not is_senior:
                    skipped_count += 1
                continue
            
            # Mark as enrolled
            enrollment_key = (student['student_id'], assigned_course_class['course_class_id'])
            enrolled_combinations.add(enrollment_key)
            enrolled_subjects_for_student.add(course['subject_id'])
            student_has_enrolled = True
            
            # Add to schedule
            for day in assigned_course_class['days']:
                student_schedules[student['student_id']][assigned_course_class['semester_id']].append((
                    day,
                    assigned_course_class['start_period'],
                    assigned_course_class['end_period']
                ))
            
            enrollment_id = self.generate_uuid()
            
            # Determine enrollment status:
            # - Past/completed: start_year < 2025 OR Spring 2024-2025 (start_year == 2024, semester_type == 'spring')
            # - Current/registered: Fall 2025 (start_year == 2025, semester_type == 'fall') OR Summer 2024-2025 (start_year == 2024, semester_type == 'summer')
            is_past = (course['start_year'] < 2024) or \
                     (course['start_year'] == 2024 and course['semester_type'] in ('fall', 'spring')) or \
                     (course['start_year'] == 2025 and course['semester_type'] == 'spring')
            is_current = (course['start_year'] == 2024 and course['semester_type'] == 'summer') or \
                        (course['start_year'] == 2025 and course['semester_type'] == 'fall')
            
            status = 'completed' if is_past else 'registered'
            
            enrollment_rows.append([
                enrollment_id,
                student['student_id'],
                assigned_course_class['course_class_id'],
                course['semester_start'],
                status,
                None, None
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
        
        if student_has_enrolled:
            stats['enrolled_students'] += 1
        else:
            stats['not_enrolled'] += 1
        
        # Force-enroll seniors in missing subjects
        if is_senior:
            missing_subjects = curriculum_subject_ids - enrolled_subjects_for_student
            
            if not missing_subjects:
                students_with_full_curriculum += 1
            
            for subject_id in missing_subjects:
                available_courses = courses_by_subject.get(subject_id, [])
                if not available_courses:
                    continue
                
                # Include past and current semesters for senior enrollment
                # Past: start_year < 2025 (all types) OR Spring 2024-2025
                # Current: Fall 2025 OR Summer 2024-2025
                available_courses = [c for c in available_courses 
                                    if c['start_year'] < 2025 or 
                                    (c['start_year'] == 2024 and c['semester_type'] == 'summer') or
                                    (c['start_year'] == 2025 and c['semester_type'] == 'fall')]
                
                if not available_courses:
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
                        
                        # FORCE ENROLL (ignore capacity)
                        enrolled_combinations.add(enrollment_key)
                        enrolled_subjects_for_student.add(subject_id)
                        forced_enrollment_count += 1
                        
                        enrollment_id = self.generate_uuid()
                        
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
            
            if not (curriculum_subject_ids - enrolled_subjects_for_student):
                students_with_full_curriculum += 1

    # SPECIAL HANDLING FOR TEST STUDENT: Enroll in exactly 6 courses in summer 2024-2025
    test_student_id = self.data['fixed_accounts'].get('student', {}).get('student_id')
    if test_student_id:
        test_student = next((s for s in self.data['students'] if s['student_id'] == test_student_id), None)
        if test_student:
            # Find summer 2024-2025 semester
            # Summer 2024-2025: academic year is 2024-2025 (start_year=2024, end_year=2025)
            # and ends in November 2025 (end_date month is 11)
            summer_2024_2025_semester = None
            for sem in self.data['semesters']:
                if sem['semester_type'] == 'summer':
                    # Check if this is summer 2024-2025: academic year 2024-2025
                    if sem.get('start_year') == 2024 and sem.get('end_year') == 2025:
                        # Also verify end date is in November 2025
                        sem_end = sem['end_date']
                        if isinstance(sem_end, str):
                            from datetime import datetime as dt
                            sem_end = dt.strptime(sem_end, '%Y-%m-%d').date()
                        if sem_end.year == 2025 and sem_end.month == 11:
                            summer_2024_2025_semester = sem
                            break
            
            if summer_2024_2025_semester:
                test_student_class_id = test_student['class_id']
                test_student_class = next((c for c in self.data['classes'] if c['class_id'] == test_student_class_id), None)
                
                if test_student_class:
                    curriculum_id = test_student_class.get('curriculum_id')
                    curriculum_subject_ids = set()
                    for cd in self.data.get('curriculum_details', []):
                        if cd['curriculum_id'] == curriculum_id:
                            curriculum_subject_ids.add(cd['subject_id'])
                    
                    # Get all courses in summer 2024-2025
                    summer_courses = [c for c in self.data['courses'] 
                                     if c['semester_id'] == summer_2024_2025_semester['semester_id']]
                    
                    # Separate curriculum and non-curriculum courses
                    curriculum_courses = [c for c in summer_courses if c['subject_id'] in curriculum_subject_ids]
                    non_curriculum_courses = [c for c in summer_courses if c['subject_id'] not in curriculum_subject_ids]
                    
                    # Get test student's existing enrollments in summer 2024-2025
                    test_student_summer_enrollments = [
                        e for e in self.data['enrollments'] 
                        if e['student_id'] == test_student_id 
                        and e['semester_id'] == summer_2024_2025_semester['semester_id']
                    ]
                    test_student_summer_course_ids = {e['course_id'] for e in test_student_summer_enrollments}
                    
                    # Target: 6 courses total in summer
                    target_count = 6
                    current_count = len(test_student_summer_enrollments)
                    needed_count = max(0, target_count - current_count)
                    
                    if needed_count > 0:
                        # Enroll in curriculum courses first (at least 3-4), then non-curriculum
                        courses_to_enroll = []
                        curriculum_needed = min(needed_count, max(3, len(curriculum_courses)))
                        non_curriculum_needed = needed_count - curriculum_needed
                        
                        # Select curriculum courses not already enrolled
                        available_curriculum = [c for c in curriculum_courses if c['course_id'] not in test_student_summer_course_ids]
                        courses_to_enroll.extend(available_curriculum[:curriculum_needed])
                        
                        # Select non-curriculum courses to make up to 6
                        available_non_curriculum = [c for c in non_curriculum_courses if c['course_id'] not in test_student_summer_course_ids]
                        courses_to_enroll.extend(available_non_curriculum[:non_curriculum_needed])
                        
                        # Enroll test student in these courses
                        for course in courses_to_enroll:
                            key = (course['course_id'], course['semester_id'])
                            available_classes = course_classes_by_course_semester.get(key, [])
                            if not available_classes:
                                continue
                            
                            # Find available course class (prefer one with space, but can force if needed)
                            assigned_course_class = None
                            for cc in available_classes:
                                enrollment_key = (test_student_id, cc['course_class_id'])
                                if enrollment_key in enrolled_combinations:
                                    continue
                                
                                # For test student, allow enrollment even if class is full (force enrollment)
                                assigned_course_class = cc
                                if cc['enrolled_count'] < cc['max_students']:
                                    cc['enrolled_count'] += 1
                                break
                            
                            if assigned_course_class:
                                enrollment_key = (test_student_id, assigned_course_class['course_class_id'])
                                enrolled_combinations.add(enrollment_key)
                                
                                enrollment_id = self.generate_uuid()
                                
                                enrollment_rows.append([
                                    enrollment_id,
                                    test_student_id,
                                    assigned_course_class['course_class_id'],
                                    course['semester_start'],
                                    'registered',  # Summer 2024-2025 is current/ongoing
                                    None, None
                                ])
                                
                                self.data['enrollments'].append({
                                    'enrollment_id': enrollment_id,
                                    'student_id': test_student_id,
                                    'course_class_id': assigned_course_class['course_class_id'],
                                    'course_id': course['course_id'],
                                    'semester_id': course['semester_id'],
                                    'credits': course['credits'],
                                    'enrollment_date': course['semester_start'],
                                    'status': 'registered'
                                })
                                
                                stats['total_enrollments'] += 1
                                self.add_statement(f"-- TEST STUDENT: Enrolled in {course['subject_code']} for summer 2024-2025")
                        
                        # Verify final count
                        final_summer_enrollments = [
                            e for e in self.data['enrollments'] 
                            if e['student_id'] == test_student_id 
                            and e['semester_id'] == summer_2024_2025_semester['semester_id']
                        ]
                        self.add_statement(f"-- TEST STUDENT: Total enrollments in summer 2024-2025: {len(final_summer_enrollments)}")

    # PHASE 1.5: BACKFILL ENROLLMENTS FOR SUMMER 2024-2025 COURSE CLASSES WITH 0 ENROLLMENTS
    # Ensure that summer 2024-2025 course classes have at least some enrollments
    self.add_statement(f"\n-- Backfilling enrollments for summer 2024-2025 course classes with 0 enrollments...")
    
    # Find summer 2024-2025 semester
    summer_2024_2025_semester = None
    for sem in self.data['semesters']:
        if sem['semester_type'] == 'summer':
            if sem.get('start_year') == 2024 and sem.get('end_year') == 2025:
                sem_end = sem['end_date']
                if isinstance(sem_end, str):
                    from datetime import datetime as dt
                    sem_end = dt.strptime(sem_end, '%Y-%m-%d').date()
                if sem_end.year == 2025 and sem_end.month == 11:
                    summer_2024_2025_semester = sem
                    break
    
    if summer_2024_2025_semester:
        # Find course classes in summer 2024-2025 with 0 enrollments
        # Count actual enrollments from enrollment data to be accurate
        enrollments_by_course_class = defaultdict(int)
        for e in self.data['enrollments']:
            enrollments_by_course_class[e['course_class_id']] += 1
        
        summer_course_classes = []
        for cc in self.data['course_classes']:
            if cc['semester_id'] == summer_2024_2025_semester['semester_id']:
                actual_enrollments = enrollments_by_course_class.get(cc['course_class_id'], 0)
                if actual_enrollments == 0:
                    summer_course_classes.append(cc)
        
        self.add_statement(f"-- Found {len(summer_course_classes)} summer 2024-2025 course classes with 0 enrollments")
        
        backfill_count = 0
        for cc in summer_course_classes:
            # Find the course for this course class
            course = next((c for c in self.data['courses'] if c['course_id'] == cc['course_id']), None)
            if not course:
                self.add_statement(f"-- WARNING: Course not found for course_class_id: {cc['course_class_id'][:8]}...")
                continue
            
            self.add_statement(f"-- Backfilling {course['subject_code']} ({course['subject_name']}) - course_class_id: {cc['course_class_id'][:8]}...")
            
            # Find students who can enroll in this course
            # For summer 2024-2025, be more aggressive - allow students even if:
            # 1. Course is not strictly in their curriculum (summer can be electives)
            # 2. They're already enrolled in another section (allow multiple sections for summer)
            potential_students = []
            for student in self.data['students']:
                class_id = student['class_id']
                cls = next((c for c in self.data['classes'] if c['class_id'] == class_id), None)
                if not cls:
                    continue
                
                # Check if course is in student's curriculum (preferred)
                curriculum_id = cls.get('curriculum_id')
                in_curriculum = False
                if curriculum_id:
                    curriculum_subject_ids = set()
                    for cd in self.data.get('curriculum_details', []):
                        if cd['curriculum_id'] == curriculum_id:
                            curriculum_subject_ids.add(cd['subject_id'])
                    in_curriculum = course['subject_id'] in curriculum_subject_ids
                
                # For summer 2024-2025, prioritize students with course in curriculum,
                # but also allow others if needed
                # Check if student is already enrolled in THIS specific course class
                already_enrolled_this_class = any(
                    e['student_id'] == student['student_id'] and 
                    e['course_class_id'] == cc['course_class_id']
                    for e in self.data['enrollments']
                )
                if not already_enrolled_this_class:
                    # Prioritize students with course in curriculum
                    priority = 1 if in_curriculum else 2
                    potential_students.append((priority, student))
            
            # Sort by priority (curriculum students first), then shuffle within each priority
            potential_students.sort(key=lambda x: x[0])
            # Separate by priority
            curriculum_students = [s for p, s in potential_students if p == 1]
            non_curriculum_students = [s for p, s in potential_students if p == 2]
            # Shuffle each group
            random.shuffle(curriculum_students)
            random.shuffle(non_curriculum_students)
            # Combine: curriculum students first, then non-curriculum
            potential_students = curriculum_students + non_curriculum_students
            
            # GUARANTEE: Enroll at least 1 student per course class, up to 10 students
            # Try to get at least 3-5 students per course class, but MUST get at least 1
            enrolled_in_backfill = 0
            target_enrollments = min(10, cc.get('max_students', 45) // 4)  # At least 25% capacity
            
            # Try all potential students if needed to guarantee at least 1 enrollment
            students_to_try = potential_students[:target_enrollments] if len(potential_students) >= target_enrollments else potential_students
            
            # If we don't have enough students, expand search to ALL students (last resort)
            if len(students_to_try) == 0:
                self.add_statement(f"-- WARNING: No potential students found for {course['subject_code']}, trying ALL students as last resort")
                # Last resort: try ALL students, regardless of curriculum
                for student in self.data['students']:
                    # Only check if already enrolled in this specific class
                    already_enrolled_this_class = any(
                        e['student_id'] == student['student_id'] and 
                        e['course_class_id'] == cc['course_class_id']
                        for e in self.data['enrollments']
                    )
                    if not already_enrolled_this_class:
                        students_to_try.append(student)
                random.shuffle(students_to_try)
            
            for student in students_to_try:
                enrollment_key = (student['student_id'], cc['course_class_id'])
                if enrollment_key in enrolled_combinations:
                    continue
                
                # Check for actual schedule conflicts (same day, overlapping time)
                # STRICT: No overlaps allowed - students cannot be in two places at once
                has_conflict = False
                student_semester_enrollments = [
                    e for e in self.data['enrollments']
                    if e['student_id'] == student['student_id'] and e['semester_id'] == cc['semester_id']
                ]
                
                for enrollment in student_semester_enrollments:
                    existing_cc = next((c for c in self.data['course_classes'] 
                                      if c['course_class_id'] == enrollment['course_class_id']), None)
                    if not existing_cc:
                        continue
                    
                    # Check if days and periods overlap
                    cc_days = cc.get('days', [])
                    existing_days = existing_cc.get('days', [])
                    
                    for day in cc_days:
                        if day in existing_days:
                            # Same day - check if periods overlap (STRICT: any overlap is a conflict)
                            if not (cc['end_period'] < existing_cc['start_period'] or 
                                   cc['start_period'] > existing_cc['end_period']):
                                has_conflict = True
                                break
                        if has_conflict:
                            break
                    if has_conflict:
                        break
                
                if not has_conflict:
                    enrolled_combinations.add(enrollment_key)
                    cc['enrolled_count'] += 1
                    
                    enrollment_id = self.generate_uuid()
                    enrollment_rows.append([
                        enrollment_id,
                        student['student_id'],
                        cc['course_class_id'],
                        course['semester_start'],
                        'registered',
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
                        'status': 'registered'
                    })
                    
                    stats['total_enrollments'] += 1
                    enrolled_in_backfill += 1
                    backfill_count += 1
            
            # GUARANTEE: If still 0 enrollments, try ALL remaining students (not just first N)
            if enrolled_in_backfill == 0 and len(potential_students) > len(students_to_try):
                self.add_statement(f"-- CRITICAL: {course['subject_code']} still has 0 enrollments. Trying ALL {len(potential_students)} potential students...")
                # Try ALL potential students, not just the first batch
                for student in potential_students[len(students_to_try):]:
                    enrollment_key = (student['student_id'], cc['course_class_id'])
                    if enrollment_key in enrolled_combinations:
                        continue
                    
                    # Check for conflicts (strict)
                    has_conflict = False
                    student_semester_enrollments = [
                        e for e in self.data['enrollments']
                        if e['student_id'] == student['student_id'] and e['semester_id'] == cc['semester_id']
                    ]
                    
                    for enrollment in student_semester_enrollments:
                        existing_cc = next((c for c in self.data['course_classes'] 
                                          if c['course_class_id'] == enrollment['course_class_id']), None)
                        if not existing_cc:
                            continue
                        
                        cc_days = cc.get('days', [])
                        existing_days = existing_cc.get('days', [])
                        
                        for day in cc_days:
                            if day in existing_days:
                                if not (cc['end_period'] < existing_cc['start_period'] or 
                                       cc['start_period'] > existing_cc['end_period']):
                                    has_conflict = True
                                    break
                            if has_conflict:
                                break
                        if has_conflict:
                            break
                    
                    if not has_conflict:
                        enrolled_combinations.add(enrollment_key)
                        cc['enrolled_count'] += 1
                        
                        enrollment_id = self.generate_uuid()
                        enrollment_rows.append([
                            enrollment_id,
                            student['student_id'],
                            cc['course_class_id'],
                            course['semester_start'],
                            'registered',
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
                            'status': 'registered'
                        })
                        
                        stats['total_enrollments'] += 1
                        enrolled_in_backfill += 1
                        backfill_count += 1
                        self.add_statement(f"-- ✓ Found student after expanding search - enrolled in {course['subject_code']}")
                        break  # Got at least 1, that's enough for guarantee
            
            if enrolled_in_backfill > 0:
                self.add_statement(f"-- ✓ Backfilled {enrolled_in_backfill} enrollments for {course['subject_code']} (course_class_id: {cc['course_class_id'][:8]}...)")
            else:
                self.add_statement(f"-- ✗ CRITICAL FAILURE: Could not backfill {course['subject_code']} - no students available at all!")
        
        # Recalculate enrollments after backfill
        final_enrollments_by_course_class = defaultdict(int)
        for e in self.data['enrollments']:
            final_enrollments_by_course_class[e['course_class_id']] += 1
        
        remaining_empty = len([cc for cc in summer_course_classes 
                              if final_enrollments_by_course_class.get(cc['course_class_id'], 0) == 0])
        
        self.add_statement(f"-- Total backfilled enrollments: {backfill_count}")
        self.add_statement(f"-- Remaining course classes with 0 enrollments: {remaining_empty}")

    # PHASE 2: CREATE DRAFT GRADES
    self.add_statement(f"\n-- Creating draft grades for current semester courses...")
    
    for enrollment in self.data['enrollments']:
        course_class_id = enrollment['course_class_id']
        cc = next((c for c in self.data['course_classes'] if c['course_class_id'] == course_class_id), None)
        if not cc:
            continue
        
        grade_status = cc.get('grade_submission_status', 'draft')
        # Current semesters: Summer 2024-2025 OR Fall 2025
        is_current = (cc['start_year'] == 2024 and cc['semester_type'] == 'summer') or \
                    (cc['start_year'] == 2025 and cc['semester_type'] == 'fall')
        
        if is_current and grade_status in ('draft', 'pending'):
            student = next((s for s in self.data['students'] if s['student_id'] == enrollment['student_id']), None)
            is_fixed = student.get('is_fixed', False) if student else False
            
            draft_grade_id = self.generate_uuid()
            
            attendance_draft = None
            midterm_draft = None
            final_draft = None
            
            if grade_status == 'pending':
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
                    attendance_draft = round(random.uniform(7.5, 9.5), 2)
                    midterm_draft = round(random.uniform(6.5, 9.0), 2)
                    final_draft = None
                else:
                    rand = random.random()
                    if rand < 0.40:
                        attendance_draft = round(random.uniform(att_min, att_max), 2)
                        midterm_draft = round(random.uniform(mid_min, mid_max), 2)
                        final_draft = None
                    elif rand < 0.70:
                        attendance_draft = round(random.uniform(att_min, att_max), 2)
                        midterm_draft = None
                        final_draft = None
            
            if attendance_draft is not None or midterm_draft is not None or final_draft is not None:
                draft_grade_rows.append([
                    draft_grade_id,
                    enrollment['enrollment_id'],
                    attendance_draft,
                    midterm_draft,
                    final_draft,
                    None
                ])
                stats['with_draft_grades'] += 1

    # PHASE 3: CREATE GRADE VERSIONS AND DETAILS
    self.add_statement(f"\n-- Creating grade versions for approved/pending submissions...")
    
    enrollments_by_course_class = defaultdict(list)
    for enrollment in self.data['enrollments']:
        enrollments_by_course_class[enrollment['course_class_id']].append(enrollment)
    
    for cc in self.data['course_classes']:
        grade_status = cc.get('grade_submission_status', 'draft')
        
        if grade_status not in ('approved', 'pending'):
            continue
        
        course_class_id = cc['course_class_id']
        enrollments = enrollments_by_course_class.get(course_class_id, [])
        
        if not enrollments:
            continue
        
        grade_version_id = self.generate_uuid()
        version_number = 1
        
        instructor_id = cc.get('instructor_id')
        submitted_at = cc.get('grade_submitted_at')
        submission_note = cc.get('grade_submission_note', 'Grade submission')
        
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
            submitted_at
        ])
        
        if course_class_id not in self.data['grade_versions']:
            self.data['grade_versions'][course_class_id] = []
        self.data['grade_versions'][course_class_id].append({
            'grade_version_id': grade_version_id,
            'version_number': version_number,
            'status': grade_status
        })
        
        for enrollment in enrollments:
            grade_detail_id = self.generate_uuid()
            
            # Determine if course is past or current for grade purposes
            # Past: start_year < 2024 OR Spring 2024-2025 (start_year == 2024, semester_type == 'spring') OR Fall 2024
            # Current: Summer 2024-2025 (start_year == 2024, semester_type == 'summer') OR Fall 2025
            is_past = (cc['start_year'] < 2024) or \
                     (cc['start_year'] == 2024 and cc['semester_type'] in ('fall', 'spring')) or \
                     (cc['start_year'] == 2025 and cc['semester_type'] == 'spring')
            is_current = (cc['start_year'] == 2024 and cc['semester_type'] == 'summer') or \
                        (cc['start_year'] == 2025 and cc['semester_type'] == 'fall')
            
            attendance = None
            midterm = None
            final = None
            
            if grade_status == 'approved':
                if is_past:
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(max(mid_min, 5.5), mid_max), 2)
                    final = round(random.uniform(max(fin_min, 6.0), fin_max), 2)
                elif is_current:
                    attendance = round(random.uniform(att_min, att_max), 2)
                    midterm = round(random.uniform(mid_min, mid_max), 2)
                    final = None
            
            elif grade_status == 'pending':
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

    stats['no_grades_yet'] = stats['total_enrollments'] - stats['with_draft_grades'] - stats['with_official_grades']

    # Statistics
    self.add_statement(f"\n-- ========================================")
    self.add_statement(f"-- ENROLLMENT SUMMARY")
    self.add_statement(f"-- ========================================")
    self.add_statement(f"-- Total students: {len(self.data['students'])}")
    self.add_statement(f"-- Students enrolled: {stats['enrolled_students']} ({stats['enrolled_students']/len(self.data['students'])*100:.1f}%)")
    self.add_statement(f"-- Students not enrolled: {stats['not_enrolled']} ({stats['not_enrolled']/len(self.data['students'])*100:.1f}%)")
    self.add_statement(f"-- Total enrollments: {stats['total_enrollments']}")
    self.add_statement(f"-- Normal enrollments: {stats['total_enrollments'] - forced_enrollment_count}")
    self.add_statement(f"-- Forced enrollments (seniors): {forced_enrollment_count}")
    self.add_statement(f"-- Enrollment rate: ~70% of available courses")
    self.add_statement(f"-- Enrollment includes:")
    self.add_statement(f"--   - Past semesters (start_year < 2024): all types (fall, spring, summer)")
    self.add_statement(f"--   - Spring 2024-2025 (start_year == 2024, semester_type == 'spring'): past/completed")
    self.add_statement(f"--   - Summer 2024-2025 (start_year == 2024, semester_type == 'summer'): current/ongoing")
    self.add_statement(f"--   - Fall 2025 (start_year == 2025, semester_type == 'fall'): current registration period")
    self.add_statement(f"-- Excludes: Spring/Summer 2025 (future semesters)")
    
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