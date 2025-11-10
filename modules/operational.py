import random
from datetime import datetime, timedelta
from .config import *

def create_schedule_changes(self):
    """
    NEW: Generate schedule change records (makeup classes, cancellations)
    """
    self.add_statement("\n-- ==================== SCHEDULE CHANGES ====================")
    
    schedule_change_rows = []
    
    # Create schedule changes for ~10% of course_classes
    sample_classes = random.sample(self.data['course_classes'], 
                                min(len(self.data['course_classes']) // 10, 50))
    
    for cc in sample_classes:
        schedule_change_id = self.generate_uuid()
        
        # Random cancelled week and makeup week
        cancelled_week = random.randint(1, 12)
        makeup_week = random.randint(13, 16)
        
        # Makeup date
        makeup_date = cc['semester_start'] + timedelta(weeks=makeup_week)
        
        # Different room for makeup
        makeup_room = random.choice(self.data['rooms'])
        
        # Use original day/time or adjust
        day_of_week = cc['days'][0]  # Use first day
        
        schedule_change_rows.append([
            schedule_change_id,
            cc['course_class_id'],
            cancelled_week,
            makeup_week,
            makeup_date,
            makeup_room['room_id'],
            day_of_week,
            cc['start_period'],
            cc['end_period'],
            'Lý do hủy: Giảng viên bận công tác'
        ])
    
    self.add_statement(f"-- Total schedule changes: {len(schedule_change_rows)}")
    
    self.bulk_insert('schedule_change',
                    ['schedule_change_id', 'course_class_id', 'cancelled_week',
                    'makeup_week', 'makeup_date', 'makeup_room_id', 'day_of_week',
                    'start_period', 'end_period', 'reason'],
                    schedule_change_rows)

def create_notifications(self):
    """Generate 30 notifications per test user (90 total)"""
    self.add_statement("\n-- ==================== NOTIFICATIONS ====================")
    
    import random
    from datetime import datetime, timedelta
    
    notification_rows = []
    base_date = datetime.now()
    
    # Test user IDs
    users = [
        '00000000-0000-0000-0000-000000000002',  # student
        '00000000-0000-0000-0000-000000000012',  # instructor
        '00000000-0000-0000-0000-000000009999',  # admin
    ]
    admin_id = users[2]
    
    # Simple notification templates
    titles = [
        ('event', 'Hội thảo AI/ML', 'Giảng viên Google Vietnam. 14:00-17:00', 'Hội trường A'),
        ('event', 'Workshop Mobile', 'React Native và Flutter. 3 tiếng', 'Lab 1'),
        ('event', 'Cuộc thi Lập trình', 'Giải nhất 50 triệu. Đội 3-5 người', 'Lab tổng hợp'),
        ('event', 'Ngày hội việc làm', '50 doanh nghiệp tuyển dụng', 'Nhà thi đấu'),
        ('event', 'Giải bóng đá', 'Tranh cúp Hiệu trưởng. Giải 10 triệu', 'Sân vận động'),
        ('tuition', 'Đóng học phí HK1', 'Hạn cuối 30/12. Mức 8.5 triệu. TK: 0123456789', None),
        ('tuition', 'HẠN CUỐI học phí', 'Còn 5 ngày. Chưa đóng bị khóa tài khoản', None),
        ('tuition', 'Xác nhận học phí', 'Đã hoàn tất. Kiểm tra biên lai trên Portal', None),
        ('tuition', 'Hỗ trợ học phí', 'Nộp hồ sơ trước 15/12. Hỗ trợ đến 50%', None),
        ('schedule', 'Thay đổi lịch học', 'CTDL: Thứ 2 7h sang Thứ 3 9h, B202', None),
        ('schedule', 'HỦY buổi 15/12', 'CSDL hủy. Học bù 22/12 Lab 2', None),
        ('schedule', 'Lịch thi giữa kỳ', 'OOP: 20/12 13:00 phòng A101. Mang CMND', None),
        ('schedule', 'Lịch thi cuối kỳ', 'Tra cứu Portal từ 01/12. Thi 09/01-25/01', None),
        ('schedule', 'Đăng ký môn HK2', '15/12-25/12. Tối đa 24 TC. Xem Portal', None),
        ('important', 'Cập nhật thông tin', 'Cập nhật email, SĐT trước 20/12', None),
        ('important', 'Quy chế đào tạo mới', 'Điểm qua môn 5.0. Học tối đa 6 năm', None),
        ('important', 'Khảo sát giảng dạy', '10-15 phút. Trúng thưởng 500k. Hạn 25/12', None),
        ('important', 'Bảo trì Portal', '18/12 00:00-06:00. Hoàn thành đăng ký trước', None),
        ('important', 'Xét học bổng HK1', 'GPA>=3.5. Hồ sơ trước 30/12. 2-5 triệu/kỳ', None),
    ]
    
    for user_id in users:
        # Generate 30 notifications per user
        for i in range(30):
            notif_type, title, content, location = random.choice(titles)
            
            # Random timing
            days_offset = random.randint(-10, 7)
            scheduled = base_date + timedelta(days=days_offset)
            visible = scheduled - timedelta(days=random.randint(1, 2))
            created = visible - timedelta(days=random.randint(1, 5))
            
            # Status
            status = 'sent' if scheduled < base_date else 'sent'
            if status == 'sent' and random.random() > 0.9:
                status = 'cancelled'
            
            # Read status
            is_read = 1 if (status == 'sent' and random.random() < 0.7) else 0
            
            # Active/deleted
            is_deleted = 1 if random.random() > 0.97 else 0
            is_active = 0 if is_deleted else 1
            
            # Updated timestamp
            updated = None
            if random.random() < 0.3:
                updated = (created + timedelta(days=random.randint(1, 3))).strftime('%Y-%m-%d %H:%M:%S')
            
            # Event fields
            event_start = None
            if notif_type == 'event':
                event_start = (scheduled + timedelta(days=random.randint(1, 21))).strftime('%Y-%m-%d')
            
            notification_rows.append([
                self.generate_uuid(),
                notif_type,
                title,
                content,
                scheduled.strftime('%Y-%m-%d'),
                visible.strftime('%Y-%m-%d'),
                is_read,
                'all_students',
                None,
                admin_id,
                status,
                location,
                event_start,
                created.strftime('%Y-%m-%d %H:%M:%S'),
                updated,
                is_deleted,
                is_active
            ])
    
    self.add_statement(f"-- Generated {len(notification_rows)} notifications")
    
    self.bulk_insert('notification_schedule',
                    ['schedule_id', 'notification_type', 'title', 'content',
                     'scheduled_date', 'visible_from', 'is_read', 'target_type',
                     'target_id', 'created_by_user', 'status', 'event_location',
                     'event_start_date', 'created_at', 'updated_at', 'is_deleted',
                     'is_active'],
                    notification_rows)

def create_documents(self):
    """
    Generate document records for course materials
    Associates documents with course_classes and instructors
    """
    self.add_statement("\n-- ==================== COURSE DOCUMENTS ====================")
    self.add_statement("-- Generating course material documents (PDFs, images, Excel files)")
    
    document_rows = []
    
    # Get available document files from media scanner
    pdf_files = self.media_scanner.files['course_docs']['pdf']
    image_files = self.media_scanner.files['course_docs']['images']
    excel_files = self.media_scanner.files['course_docs']['excel']
    
    total_files = len(pdf_files) + len(image_files) + len(excel_files)
    
    if total_files == 0:
        self.add_statement("-- WARNING: No course document files found in medias/course_docs/")
        self.add_statement("-- Skipping document generation")
        return
    
    self.add_statement(f"-- Found {len(pdf_files)} PDFs, {len(image_files)} images, {len(excel_files)} Excel files")
    
    # Document types (matching CHECK constraint)
    document_types = ['Bài tập', 'Tài liệu', 'Slide', 'Bài LAB']
    
    # Document type descriptions mapped to document types
    descriptions = {
        'Bài tập': [
            'Bài tập thực hành tuần',
            'Bài tập ôn tập',
            'Đề bài tập lớn',
            'Bài tập làm thêm'
        ],
        'Tài liệu': [
            'Bài giảng lý thuyết',
            'Tài liệu tham khảo',
            'Đề cương môn học',
            'Tài liệu ôn tập',
            'Giáo trình môn học'
        ],
        'Slide': [
            'Slide bài giảng',
            'Slide tổng quan',
            'Slide minh họa',
            'Slide thảo luận'
        ],
        'Bài LAB': [
            'Hướng dẫn thực hành',
            'Bài LAB thực hành',
            'Đề bài thí nghiệm',
            'Mẫu báo cáo LAB'
        ]
    }
    
    # File size ranges (in bytes)
    file_size_ranges = {
        'pdf': (100000, 5000000),
        'docx': (50000, 2000000),
        'doc': (50000, 2000000),
        'pptx': (500000, 10000000),
        'ppt': (500000, 10000000),
        'xlsx': (50000, 1000000),
        'xls': (50000, 1000000),
        'jpg': (100000, 5000000),
        'jpeg': (100000, 5000000),
        'png': (100000, 5000000),
        'zip': (1000000, 50000000),
        'rar': (1000000, 50000000)
    }
    
    # Generate documents for course_classes
    # Each course_class gets 2-5 documents
    for course_class in self.data['course_classes']:
        num_docs = random.randint(2, 5)
        
        for i in range(num_docs):
            document_id = self.generate_uuid()
            
            # Randomly select document type
            document_type = random.choice(document_types)
            
            # Randomly select file type and file
            file_category = random.choice(['pdf', 'image', 'excel'])
            
            if file_category == 'pdf' and pdf_files:
                file_name = random.choice(pdf_files)
                file_type = 'pdf'
            elif file_category == 'image' and image_files:
                file_name = random.choice(image_files)
                file_ext = file_name.split('.')[-1].lower()
                file_type = file_ext if file_ext in ['jpg', 'jpeg', 'png'] else 'jpg'
            elif file_category == 'excel' and excel_files:
                file_name = random.choice(excel_files)
                file_ext = file_name.split('.')[-1].lower()
                file_type = file_ext if file_ext in ['xlsx', 'xls'] else 'xlsx'
            else:
                # Fallback to PDF if preferred type not available
                if pdf_files:
                    file_name = random.choice(pdf_files)
                    file_type = 'pdf'
                else:
                    continue
            
            # Build file path URL using correct bucket
            file_path = self.media_scanner.build_url('instructor_documents', file_name)
            
            # Generate file size
            size_min, size_max = file_size_ranges.get(file_type, (100000, 5000000))
            file_size = random.randint(size_min, size_max)
            
            # Get description based on document type
            desc_pool = descriptions[document_type]
            description = random.choice(desc_pool)
            
            # Uploaded by instructor
            uploaded_by = course_class.get('instructor_id')
            
            document_rows.append([
                document_id,
                course_class['course_class_id'],
                file_name,
                document_type,
                file_path,
                file_type,
                file_size,
                uploaded_by,
                description
            ])
    
    self.add_statement(f"-- Total documents generated: {len(document_rows)}")
    
    self.bulk_insert('document',
                    ['document_id', 'course_class_id', 'file_name', 'document_type',
                     'file_path', 'file_type', 'file_size', 'uploaded_by', 'description'],
                    document_rows)

def create_regulations(self):
    """
    Generate regulation records from spec file
    """
    self.add_statement("\n-- ==================== REGULATIONS ====================")
    
    regulation_rows = []
    
    # Get admin for created_by - using simple ID
    admin_id = self.data['fixed_accounts']['admin']['admin_id']
    
    self.add_statement(f"-- Using admin_id: {admin_id}")
    self.add_statement(f"-- Found {len(self.spec_data.get('regulations', []))} regulation entries in spec")
    
    for line in self.spec_data.get('regulations', []):
        parts = [p.strip() for p in line.split('|')]
        
        if len(parts) < 4:
            self.add_statement(f"-- WARNING: Invalid regulation line (need at least 4 parts): {line[:100]}...")
            continue
        
        regulation_name = parts[0]
        target = parts[1]
        pdf_path = parts[2]
        description = parts[3]
        expire_date = None
        
        # Handle expire_date (5th part is optional)
        if len(parts) > 4:
            expire_val = parts[4].strip()
            if expire_val and expire_val.upper() != 'NULL':
                try:
                    expire_date = datetime.strptime(expire_val, '%Y-%m-%d').date()
                except:
                    expire_date = None
        
        # Validate target
        if target not in ['student', 'instructor']:
            self.add_statement(f"-- WARNING: Invalid target '{target}' for regulation: {regulation_name}")
            continue
        
        regulation_id = self.generate_uuid()
        
        self.data['regulations'].append({
            'regulation_id': regulation_id,
            'regulation_name': regulation_name,
            'target': target
        })
        
        regulation_rows.append([
            regulation_id,
            regulation_name,
            target,
            pdf_path,
            description,
            expire_date,
            admin_id  # Using simple predictable admin_id
        ])
        
        self.add_statement(f"-- Added: {regulation_name} (target: {target})")
    
    self.add_statement(f"-- Total regulations to insert: {len(regulation_rows)}")
    
    if len(regulation_rows) > 0:
        self.bulk_insert('regulation',
                        ['regulation_id', 'regulation_name', 'target', 'pdf_file_path', 
                        'regulation_description', 'expire_date', 'created_by_admin'],
                        regulation_rows)
    else:
        self.add_statement("-- WARNING: No regulations to insert!")

def create_notes(self):
    """Generate simple one-line notes for the test student"""
    self.add_statement("\n-- ==================== STUDENT NOTES ====================")
    
    import random
    from datetime import datetime, timedelta
    
    # FIXED TEST STUDENT ID
    test_student_id = '00000000-0000-0000-0000-000000000003'
    
    note_rows = []
    
    # Simple one-line note content
    note_contents = [
        'Nhắc nhở: Thi giữa kỳ vào tuần sau',
        'Còn 5 ngày nữa đến kỳ thi cuối kỳ',
        'Thi tuần này - Phòng A101, đến trước 15 phút',
        'Kỳ thi thực hành trên máy - Cần chuẩn bị tài khoản đăng nhập',
        'Ôn tập chương 3: Cấu trúc dữ liệu (Stack, Queue, Linked List, Tree)',
        'Cần xem lại: Bài giảng tuần 5-6 về thuật toán sắp xếp',
        'Làm lại bài tập về con trỏ - Bài 4.3, 4.7, 4.9',
        'Ôn thi: Tập trung Database Normalization (1NF, 2NF, 3NF, BCNF)',
        'Học nhóm: Ôn chương 2 với bạn vào thứ 5',
        'Bài tập tuần 7 - Deadline 3 ngày nữa (Stack, Queue, BST)',
        'Hoàn thành Lab 4 trước buổi học - Chương trình quản lý sinh viên',
        'Bài tập nhóm - Thuyết trình tuần sau (Hoàn thiện slide và demo)',
        'Đọc tài liệu chương 5 trước lớp (Section 5.1-5.3)',
        'Tổng hợp: Lập trình hướng đối tượng (Class, Inheritance, Polymorphism)',
        'Công thức quan trọng cần nhớ: Tổ hợp C(n,k), Hoán vị P(n,k)',
        'Tổng hợp bài tập đã chữa trên lớp (Tuần 1-3)',
        'Lý thuyết trọng tâm: SQL Queries (SELECT, JOIN, GROUP BY)',
        'Ghi chú buổi học 15/11: Graph, BFS và DFS algorithms',
        'Lưu ý từ giảng viên về đồ án: Deadline 20/12, nhóm 3-4 người',
        'Slide bài giảng đã được đăng - Chương 4 và 5',
        'Meeting với nhóm - Thứ 5 lúc 14:00 để review tiến độ project',
        'Kế hoạch ôn thi cuối kỳ: 3 tuần ôn tập từng chương',
        'Lịch học tuần này: T2 Toán, T3 Lập trình, T5 CSDL',
        'Mục tiêu học tập tháng này: GPA >= 3.5 và hoàn thành đồ án',
        'Chuẩn bị giấy nháp cho bài thi viết tay',
        'Không được sử dụng điện thoại trong phòng thi',
        'Sinh viên cần mang theo CMND/CCCD và thẻ sinh viên',
        'Bài thi có thời gian 120 phút, không được mang tài liệu',
        'Ôn lại các khái niệm khó từ chương 1 đến chương 4',
        'Làm đề thi mẫu để làm quen với format câu hỏi',
    ]
    
    # Generate 10-15 random notes for test student
    total_notes_to_generate = random.randint(10, 15)
    
    for i in range(total_notes_to_generate):
        note_id = self.generate_uuid()
        
        # Randomly select note content
        content = random.choice(note_contents)
        
        # Random date within last 30 days or future 30 days
        days_offset = random.randint(-60, 1)
        created_at = datetime.now() + timedelta(days=days_offset)
        
        # 20% have updated_at (edited notes)
        updated_at = None
        if random.random() < 0.2:
            updated_at = (created_at + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d %H:%M:%S')
        
        note_rows.append([
            note_id,
            test_student_id,
            content,
            created_at.strftime('%Y-%m-%d %H:%M:%S'),
            updated_at
        ])
    
    self.add_statement(f"-- Generated {len(note_rows)} notes for test student")
    
    self.bulk_insert('note',
                    ['note_id', 'student_id', 'content', 'created_at', 'updated_at'],
                    note_rows)

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_notes = create_notes

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_schedule_changes = create_schedule_changes
SQLDataGenerator.create_notifications = create_notifications
SQLDataGenerator.create_documents = create_documents
SQLDataGenerator.create_regulations = create_regulations
SQLDataGenerator.create_notes = create_notes