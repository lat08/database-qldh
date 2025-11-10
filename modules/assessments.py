import random
from datetime import datetime, timedelta
from collections import defaultdict
from .config import *

def create_exams_and_exam_entries(self):
    """
    UPDATED: Generate exam definitions and exam entries
    - exam: course-level exam definition (with notes column)
    - exam_entry: instructor-submitted exam PDFs (pending/approved/rejected, with codes)
    - exam_class: specific exam schedule for a course_class
    """
    self.add_statement("\n-- ==================== EXAMS, EXAM ENTRIES & EXAM CLASSES ====================")
    self.add_statement("-- exam: course-level exam definition")
    self.add_statement("-- exam_entry: instructor submissions (PDFs, approval workflow)")
    self.add_statement("-- exam_class: specific exam schedule with room and time")
    
    exam_rows = []
    exam_entry_rows = []
    exam_class_rows = []
    
    # Initialize storage for exam_classes
    self.data['exam_classes'] = []
    
    # Track created exams by course_id to avoid duplicates
    exams_by_course = {}
    
    # Group course_classes by course
    course_classes_by_course = defaultdict(list)
    for cc in self.data['course_classes']:
        course_classes_by_course[cc['course_id']].append(cc)
    
    # Get admin for reviewing exam entries
    admin_id = self.data['fixed_accounts']['admin']['admin_id']
    
    # Exam notes templates (for the exam.notes column)
    exam_notes_templates = [
        'Sinh viên cần mang theo CMND/CCCD và thẻ sinh viên',
        'Sinh viên được phép sử dụng máy tính cá nhân',
        'Không được mang tài liệu vào phòng thi',
        'Sinh viên cần đến trước 15 phút',
        'Sinh viên được sử dụng tài liệu mở',
        'Bài thi thực hành trên máy tính',
        'Sinh viên cần chuẩn bị giấy nháp',
        'Không được sử dụng điện thoại trong phòng thi',
        'Sinh viên làm bài trên giấy thi phát',
        'Bài thi có thời gian 120 phút',
        'Sinh viên nghỉ có phép cần liên hệ phòng đào tạo',
        'Sinh viên vi phạm quy chế thi sẽ bị xử lý kỷ luật',
        'Mang theo bút viết, tẩy, thước kẻ',
        'Bài thi không được tẩy xóa',
        'Nộp bài trước 30 phút cuối có thể rời phòng thi',
    ]
    
    for course_id, course_classes in course_classes_by_course.items():
        course = next((c for c in self.data['courses'] if c['course_id'] == course_id), None)
        if not course:
            continue
        
        # ============================================================
        # 1. CREATE EXAM DEFINITION (once per course)
        # ============================================================
        exam_id = self.generate_uuid()
        exam_format = random.choice(['multiple_choice', 'essay', 'practical', 'oral', 'mixed'])
        exam_type = random.choice(['midterm', 'final', 'final', 'final'])  # More finals
        
        # Determine how many exam codes needed (typically 2-4 variants)
        num_exam_codes_needed = random.randint(2, 4)
        
        # Generate exam notes (60% chance to have notes)
        exam_notes = None
        if random.random() < 0.80:
            # Pick 1-3 random note templates
            num_notes = random.randint(1, 3)
            selected_notes = random.sample(exam_notes_templates, num_notes)
            exam_notes = '. '.join(selected_notes) + '.'
        
        exam_rows.append([
            exam_id,
            course_id,
            exam_format,
            exam_type,
            exam_notes,  # Single notes column
            num_exam_codes_needed,
            'published'  # Assume published for demo
        ])
        
        exams_by_course[course_id] = exam_id
        
        # ============================================================
        # 2. CREATE EXAM ENTRIES (instructor submissions)
        # ============================================================
        # Each course_class instructor submits their exam version
        submitted_entries = []
        
        for cc in course_classes:
            if random.random() < 0.6:
                exam_entry_id = self.generate_uuid()
                
                # Display name (instructor's submission identifier)
                instructor = next((i for i in self.data['instructors'] 
                                if i['instructor_id'] == cc['instructor_id']), None)
                instructor_name = instructor['full_name'] if instructor else 'GV'
                display_name = f"{course['subject_code']} - {instructor_name} - Lớp {cc['session_number']}"
                
                # Get random exam PDF and answer key
                question_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
                answer_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
                
                question_file_path = self.media_scanner.build_url('exams', question_pdf)
                answer_file_path = self.media_scanner.build_url('exams', answer_pdf)
                
                # Duration
                duration_minutes = random.choice([90, 120, 150, 180])
                
                # Approval status (80% approved, 15% pending, 5% rejected)
                status_rand = random.random()
                if status_rand < 0.80:
                    entry_status = 'approved'
                    is_picked = False  # Will be set to True for selected entries later
                    entry_code = None
                    rejection_reason = None
                    reviewed_by = admin_id
                    reviewed_at = datetime.now() - timedelta(days=random.randint(5, 30))
                elif status_rand < 0.95:
                    entry_status = 'pending'
                    is_picked = False
                    entry_code = None
                    rejection_reason = None
                    reviewed_by = None
                    reviewed_at = None
                else:
                    entry_status = 'rejected'
                    is_picked = False
                    entry_code = None
                    rejection_reason = random.choice([
                        'Đề thi không đúng format',
                        'Thiếu đáp án',
                        'Độ khó chưa phù hợp',
                        'Cần bổ sung câu hỏi'
                    ])
                    reviewed_by = admin_id
                    reviewed_at = datetime.now() - timedelta(days=random.randint(1, 15))
                
                exam_entry_rows.append([
                    exam_entry_id,
                    exam_id,
                    cc['course_class_id'],
                    entry_code,  # Will be updated for picked entries
                    display_name,
                    question_file_path,
                    answer_file_path,
                    duration_minutes,
                    is_picked,
                    entry_status,
                    rejection_reason,
                    reviewed_by,
                    reviewed_at
                ])
                
                if entry_status == 'approved':
                    submitted_entries.append({
                        'exam_entry_id': exam_entry_id,
                        'course_class_id': cc['course_class_id'],
                        'duration_minutes': duration_minutes
                    })
        
        # ============================================================
        # 3. PICK EXAM ENTRIES (assign entry codes A, B, C, etc.)
        # ============================================================
        # Randomly select entries up to num_exam_codes_needed
        if submitted_entries:
            num_to_pick = min(num_exam_codes_needed, len(submitted_entries))
            picked_entries = random.sample(submitted_entries, num_to_pick)
            
            entry_codes = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
            
            for idx, entry in enumerate(picked_entries):
                entry_code = entry_codes[idx] if idx < len(entry_codes) else f"E{idx+1}"
                
                # UPDATE the exam_entry row to mark it as picked with entry_code
                # Find the row in exam_entry_rows
                for i, row in enumerate(exam_entry_rows):
                    if row[0] == entry['exam_entry_id']:  # exam_entry_id match
                        # Update entry_code (index 3) and is_picked (index 8)
                        exam_entry_rows[i][3] = entry_code
                        exam_entry_rows[i][8] = True  # is_picked
                        break
        
        # ============================================================
        # 4. CREATE EXAM_CLASS SCHEDULES
        # ============================================================
        semester = next((s for s in self.data['semesters'] 
                        if s['semester_id'] == course['semester_id']), None)
        
        if not semester:
            continue
        
        # Exam period: last 2 weeks of semester
        sem_end = semester['end_date']
        exam_start = sem_end - timedelta(days=14)
        
        # Generate exam dates (weekdays only)
        exam_dates = []
        current = exam_start
        while current <= sem_end:
            if current.weekday() < 6:  # Monday to Saturday
                exam_dates.append(current)
            current += timedelta(days=1)
        
        if not exam_dates:
            continue
        
        # Exam time slots
        exam_slots = [
            (7, 30, 120),   # 7:30 AM, 2 hours
            (10, 0, 120),   # 10:00 AM, 2 hours
            (13, 30, 120),  # 1:30 PM, 2 hours
            (16, 0, 120),   # 4:00 PM, 2 hours
        ]
        
        # Track room usage: (room_id, datetime) -> True
        exam_room_usage = {}
        
        for cc in course_classes:
            # Try to schedule exam without conflicts
            exam_scheduled = False
            
            for attempt in range(20):
                exam_date = random.choice(exam_dates)
                hour, minute, duration = random.choice(exam_slots)
                start_time = datetime.combine(exam_date, datetime.min.time().replace(hour=hour, minute=minute))
                room = random.choice(self.data['rooms'])
                
                key = (room['room_id'], start_time)
                if key not in exam_room_usage:
                    exam_room_usage[key] = True
                    
                    exam_class_id = self.generate_uuid()
                    monitor_instructor = random.choice(self.data['instructors'])
                    
                    exam_class_rows.append([
                        exam_class_id,
                        exam_id,
                        cc['course_class_id'],
                        room['room_id'],
                        monitor_instructor['instructor_id'],
                        start_time,
                        duration,
                        'scheduled'
                    ])
                    
                    # Store in self.data for potential future use
                    self.data['exam_classes'].append({
                        'exam_class_id': exam_class_id,
                        'exam_id': exam_id,
                        'course_class_id': cc['course_class_id'],
                        'room_id': room['room_id'],
                        'start_time': start_time
                    })
                    
                    exam_scheduled = True
                    break
            
            if not exam_scheduled:
                # Fallback: schedule anyway (may conflict)
                exam_date = random.choice(exam_dates)
                hour, minute, duration = random.choice(exam_slots)
                start_time = datetime.combine(exam_date, datetime.min.time().replace(hour=hour, minute=minute))
                room = random.choice(self.data['rooms'])
                
                exam_class_id = self.generate_uuid()
                monitor_instructor = random.choice(self.data['instructors'])
                
                exam_class_rows.append([
                    exam_class_id,
                    exam_id,
                    cc['course_class_id'],
                    room['room_id'],
                    monitor_instructor['instructor_id'],
                    start_time,
                    duration,
                    'scheduled'
                ])
                
                # Store in self.data for fallback case
                self.data['exam_classes'].append({
                    'exam_class_id': exam_class_id,
                    'exam_id': exam_id,
                    'course_class_id': cc['course_class_id'],
                    'room_id': room['room_id'],
                    'start_time': start_time
                })
    
    # SPECIAL HANDLING FOR TEST STUDENT: Create exam schedules for summer 2024-2025 courses
    # with specific dates: 2 exams on 11/6 (completed), 2 on 11/12 (upcoming), 2 on 11/19 (scheduled)
    test_student_id = self.data['fixed_accounts'].get('student', {}).get('student_id')
    if test_student_id:
        from datetime import date
        TODAY = datetime.now().date()
        
        # Calculate exam dates relative to TODAY
        # Target dates: 11/6, 11/12, 11/19
        # These dates should work for any TODAY:
        # - If TODAY is before 11/6: use current year, all exams are future
        # - If TODAY is between 11/6 and 11/12: use current year, 11/6 is past, others are future
        # - If TODAY is between 11/12 and 11/19: use current year, 11/6 and 11/12 are past, 11/19 is future
        # - If TODAY is after 11/19: use next year's dates
        
        # Calculate target dates based on year
        current_year = TODAY.year
        target_date_past = date(current_year, 11, 6)
        target_date_upcoming = date(current_year, 11, 12)
        target_date_future = date(current_year, 11, 19)
        
        # If we're past 11/19, use next year's dates for all
        if TODAY > target_date_future:
            exam_date_past = date(current_year + 1, 11, 6)
            exam_date_upcoming = date(current_year + 1, 11, 12)
            exam_date_future = date(current_year + 1, 11, 19)
        else:
            # Use current year's dates
            exam_date_past = target_date_past
            exam_date_upcoming = target_date_upcoming
            exam_date_future = target_date_future
        
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
            # Get test student's enrollments in summer 2024-2025
            test_student_summer_enrollments = [
                e for e in self.data['enrollments'] 
                if e['student_id'] == test_student_id 
                and e['semester_id'] == summer_2024_2025_semester['semester_id']
            ]
            
            # Get course classes for these enrollments
            test_student_course_classes = []
            for enrollment in test_student_summer_enrollments:
                cc = next((c for c in self.data['course_classes'] 
                          if c['course_class_id'] == enrollment['course_class_id']), None)
                if cc:
                    test_student_course_classes.append(cc)
            
            # Remove existing exam_class entries for test student's courses (to override normal exam creation)
            test_student_course_class_ids = {cc['course_class_id'] for cc in test_student_course_classes}
            
            # Remove exam_class entries that were already created for these course classes
            exam_class_rows_to_remove = []
            for i in range(len(exam_class_rows) - 1, -1, -1):
                if exam_class_rows[i][2] in test_student_course_class_ids:  # course_class_id is at index 2
                    exam_class_rows_to_remove.append(exam_class_rows.pop(i))
            
            if exam_class_rows_to_remove:
                self.add_statement(f"-- TEST STUDENT: Removed {len(exam_class_rows_to_remove)} existing exam_class entries to override with specific dates")
            
            # Work with available course classes (even if less than 6, we'll still create exams)
            # But try to ensure we have at least 6 enrollments
            if len(test_student_course_classes) < 6:
                self.add_statement(f"-- WARNING: Test student only has {len(test_student_course_classes)} enrollments in summer 2024-2025, expected 6")
            
            if len(test_student_course_classes) > 0:
                # Get courses for these course classes
                test_student_courses = []
                # Take up to 6 courses (or all if less than 6)
                num_courses_to_use = min(6, len(test_student_course_classes))
                for cc in test_student_course_classes[:num_courses_to_use]:
                    course = next((c for c in self.data['courses'] 
                                 if c['course_id'] == cc['course_id']), None)
                    if course:
                        test_student_courses.append({
                            'course': course,
                            'course_class': cc
                        })
                
                # Assign exam dates: distribute across 11/6, 11/12, 11/19
                # If we have 6 courses: 2 on each date
                # If we have fewer: distribute evenly
                num_courses = len(test_student_courses)
                if num_courses >= 6:
                    exam_date_assignments = [
                        (exam_date_past, 2),      # 2 exams on 11/6
                        (exam_date_upcoming, 2),  # 2 exams on 11/12
                        (exam_date_future, 2),    # 2 exams on 11/19
                    ]
                elif num_courses == 5:
                    exam_date_assignments = [
                        (exam_date_past, 2),      # 2 exams on 11/6
                        (exam_date_upcoming, 2),  # 2 exams on 11/12
                        (exam_date_future, 1),    # 1 exam on 11/19
                    ]
                elif num_courses == 4:
                    exam_date_assignments = [
                        (exam_date_past, 1),      # 1 exam on 11/6
                        (exam_date_upcoming, 1),  # 1 exam on 11/12
                        (exam_date_future, 2),    # 2 exams on 11/19
                    ]
                elif num_courses == 3:
                    exam_date_assignments = [
                        (exam_date_past, 1),      # 1 exam on 11/6
                        (exam_date_upcoming, 1),  # 1 exam on 11/12
                        (exam_date_future, 1),    # 1 exam on 11/19
                    ]
                elif num_courses == 2:
                    exam_date_assignments = [
                        (exam_date_past, 1),      # 1 exam on 11/6
                        (exam_date_upcoming, 1),  # 1 exam on 11/12
                    ]
                else:
                    exam_date_assignments = [
                        (exam_date_past, num_courses),  # All on 11/6
                    ]
                
                course_idx = 0
                for exam_date, count in exam_date_assignments:
                    # Determine exam status based on date relative to TODAY
                    if exam_date < TODAY:
                        exam_status = 'completed'  # Already taken
                    else:
                        exam_status = 'scheduled'  # Upcoming or future
                    
                    for i in range(count):
                        if course_idx >= len(test_student_courses):
                            break
                        
                        course_info = test_student_courses[course_idx]
                        course = course_info['course']
                        cc = course_info['course_class']
                        
                        # Get or create exam for this course
                        exam_id = exams_by_course.get(course['course_id'])
                        if not exam_id:
                            # Create exam if it doesn't exist
                            exam_id = self.generate_uuid()
                            exam_format = random.choice(['multiple_choice', 'essay', 'practical', 'oral', 'mixed'])
                            exam_type = 'final'
                            num_exam_codes_needed = 2
                            
                            exam_notes = None
                            if random.random() < 0.80:
                                num_notes = random.randint(1, 3)
                                selected_notes = random.sample(exam_notes_templates, num_notes)
                                exam_notes = '. '.join(selected_notes) + '.'
                            
                            exam_rows.append([
                                exam_id,
                                course['course_id'],
                                exam_format,
                                exam_type,
                                exam_notes,
                                num_exam_codes_needed,
                                'published'
                            ])
                            
                            exams_by_course[course['course_id']] = exam_id
                        
                        # Create exam_entry if it doesn't exist
                        exam_entry_exists = any(
                            row[2] == cc['course_class_id'] for row in exam_entry_rows
                        )
                        
                        if not exam_entry_exists:
                            exam_entry_id = self.generate_uuid()
                            instructor = next((i for i in self.data['instructors'] 
                                            if i['instructor_id'] == cc['instructor_id']), None)
                            instructor_name = instructor['full_name'] if instructor else 'GV'
                            display_name = f"{course['subject_code']} - {instructor_name} - Lớp {cc.get('session_number', 1)}"
                            
                            question_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
                            answer_pdf = self.media_scanner.get_random_file('course_docs', 'pdf')
                            
                            question_file_path = self.media_scanner.build_url('exams', question_pdf)
                            answer_file_path = self.media_scanner.build_url('exams', answer_pdf)
                            
                            duration_minutes = random.choice([90, 120, 150, 180])
                            
                            exam_entry_rows.append([
                                exam_entry_id,
                                exam_id,
                                cc['course_class_id'],
                                'A',  # entry_code
                                display_name,
                                question_file_path,
                                answer_file_path,
                                duration_minutes,
                                True,  # is_picked
                                'approved',  # entry_status
                                None,  # rejection_reason
                                admin_id,  # reviewed_by
                                datetime.now() - timedelta(days=random.randint(5, 30))  # reviewed_at
                            ])
                        
                        # Create exam_class with specific date and status
                        exam_class_id = self.generate_uuid()
                        room = random.choice(self.data['rooms'])
                        monitor_instructor = random.choice(self.data['instructors'])
                        
                        # Exam time: 8:00 AM
                        exam_datetime = datetime.combine(exam_date, datetime.min.time().replace(hour=8, minute=0))
                        duration_minutes = 120
                        
                        exam_class_rows.append([
                            exam_class_id,
                            exam_id,
                            cc['course_class_id'],
                            room['room_id'],
                            monitor_instructor['instructor_id'],
                            exam_datetime,
                            duration_minutes,
                            exam_status
                        ])
                        
                        self.data['exam_classes'].append({
                            'exam_class_id': exam_class_id,
                            'exam_id': exam_id,
                            'course_class_id': cc['course_class_id'],
                            'room_id': room['room_id'],
                            'start_time': exam_datetime
                        })
                        
                        course_idx += 1
                        
                        self.add_statement(f"-- TEST STUDENT: Exam scheduled for {course['subject_code']} on {exam_date} (status: {exam_status})")
                
                self.add_statement(f"-- TEST STUDENT: Created {course_idx} exam schedules for summer 2024-2025 courses")
    
    self.add_statement(f"-- Total exams (course-level): {len(exam_rows)}")
    self.add_statement(f"-- Total exam entries (instructor submissions): {len(exam_entry_rows)}")
    self.add_statement(f"-- Total exam_class (scheduled): {len(exam_class_rows)}")
    
    # Insert exam definitions
    self.bulk_insert('exam',
                    ['exam_id', 'course_id', 'exam_format', 'exam_type', 
                    'notes', 'num_exam_codes_needed', 'exam_status'],
                    exam_rows)
    
    # Insert exam entries
    self.bulk_insert('exam_entry',
                    ['exam_entry_id', 'exam_id', 'course_class_id', 'entry_code',
                    'display_name', 'question_file_path', 'answer_file_path',
                    'duration_minutes', 'is_picked', 'entry_status', 'rejection_reason',
                    'reviewed_by', 'reviewed_at'],
                    exam_entry_rows)
    
    # Insert exam_class schedules
    self.bulk_insert('exam_class',
                    ['exam_class_id', 'exam_id', 'course_class_id', 'room_id',
                    'monitor_instructor_id', 'start_time', 'duration_minutes', 'exam_status'],
                    exam_class_rows)


# Bind the function to SQLDataGenerator
from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_exams_and_exam_entries = create_exams_and_exam_entries