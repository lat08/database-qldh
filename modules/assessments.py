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