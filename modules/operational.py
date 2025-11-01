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
    """
    NEW: Generate notification schedules
    """
    self.add_statement("\n-- ==================== NOTIFICATIONS ====================")
    
    notification_rows = []
    
    # Get admin user for creating notifications
    admin_user_id = self.data['fixed_accounts']['admin']['user_id']
    
    notification_types = ['event', 'tuition', 'schedule', 'important']
    target_types = ['all', 'all_students', 'all_instructors', 'class', 'faculty', 'instructor']
    statuses = ['pending', 'sent', 'cancelled']
    
    # Create 20 sample notifications
    for i in range(20):
        schedule_id = self.generate_uuid()
        notif_type = random.choice(notification_types)
        target_type = random.choice(target_types)
        status = random.choice(statuses)
        
        # target_id will be None for now - you can populate it later if needed
        target_id = None
        
        scheduled_date = datetime.now() - timedelta(days=random.randint(0, 90))
        visible_from = scheduled_date - timedelta(days=random.randint(1, 7))
        created_at = visible_from - timedelta(days=random.randint(1, 5))
        updated_at = created_at + timedelta(days=random.randint(0, 3)) if random.random() > 0.5 else None
        
        # Event-specific fields
        event_location = None
        event_start_date = None
        if notif_type == 'event':
            event_location = random.choice(['Hội trường A', 'Phòng 101', 'Sân trường', 'Phòng hội thảo B', 'Khu vực ngoài trời'])
            event_start_date = scheduled_date + timedelta(days=random.randint(1, 14))
        
        titles = {
            'event': f'Sự kiện: Hội thảo khoa học #{i+1}',
            'tuition': f'Thông báo: Đóng học phí kỳ {i+1}',
            'schedule': f'Thay đổi lịch học tuần {i+1}',
            'important': f'Thông báo quan trọng #{i+1}'
        }
        
        is_read = 1 if random.random() > 0.7 else 0
        is_deleted = 1 if random.random() > 0.95 else 0
        is_active = 0 if is_deleted else (0 if random.random() > 0.9 else 1)
        
        notification_rows.append([
            schedule_id,
            notif_type,
            titles.get(notif_type, 'Thông báo'),
            f'Nội dung thông báo số {i+1}. Đây là thông tin chi tiết về {titles.get(notif_type, "thông báo")}.',
            scheduled_date,
            visible_from,
            is_read,
            target_type,
            target_id,
            admin_user_id,
            status,
            event_location,
            event_start_date,
            created_at,
            updated_at,
            is_deleted,
            is_active
        ])
    
    self.add_statement(f"-- Total notifications: {len(notification_rows)}")
    
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
    """Generate notes for all users (students, instructors, admins)"""
    self.add_statement("\n-- ==================== NOTES ====================")
    
    import random
    from datetime import datetime, timedelta
    
    note_rows = []
    note_types = ['exam', 'homework', 'schedule', 'personal', 'reminder', 'announcement']
    
    # Sample note content templates
    note_contents = {
        'exam': [
            'Ôn tập chương 3: Cấu trúc dữ liệu và giải thuật',
            'Chuẩn bị tài liệu cho kỳ thi giữa kỳ môn Lập trình',
            'Lưu ý: Kỳ thi cuối kỳ sẽ thi trên máy tính',
            'Ôn lại các bài tập đã làm trên lớp',
            'Xem lại slide bài giảng về OOP',
        ],
        'homework': [
            'Hoàn thành bài tập lập trình tuần 5',
            'Nộp báo cáo project môn Cơ sở dữ liệu',
            'Làm bài tập về nhà phần Mạng máy tính',
            'Chuẩn bị thuyết trình nhóm',
            'Đọc tài liệu chương 4 trước buổi học',
        ],
        'schedule': [
            'Lịch học thay đổi: Thứ 3 sang Thứ 5 cùng giờ',
            'Buổi học bù: Thứ 7 tuần sau lúc 8:00',
            'Nhắc nhở: Họp lớp vào thứ 6 này',
            'Lớp học chuyển sang phòng B201',
            'Giảng viên nghỉ buổi học tuần này',
        ],
        'personal': [
            'Ghi chú: Cần mua thêm giáo trình',
            'Nhớ in tài liệu cho bài thuyết trình',
            'Mục tiêu: Hoàn thành 3 chương ôn tập',
            'Cần liên hệ nhóm để bàn về project',
            'Đăng ký môn học kỳ sau',
        ],
        'reminder': [
            'Nhắc nhở: Deadline nộp bài tuần sau',
            'Đừng quên mang theo USB đến lớp',
            'Nhớ đóng học phí trước ngày 15',
            'Cần nộp đơn xin học bổng',
            'Nhắc: Meeting với advisor vào thứ 4',
        ],
        'announcement': [
            'Thông báo: Lịch thi đã được cập nhật',
            'Lưu ý từ giảng viên: Thay đổi tiêu chí chấm điểm',
            'Cập nhật mới: Tài liệu bài giảng đã đăng',
            'Thông báo nghỉ học do thời tiết xấu',
            'Trường tổ chức hội thảo chuyên ngành',
        ]
    }
    
    # Collect all user_ids from fixed accounts
    all_user_ids = []
    for account_key, account_data in self.data['fixed_accounts'].items():
        if 'user_id' in account_data:
            all_user_ids.append(account_data['user_id'])
    
    if not all_user_ids:
        self.add_statement("-- WARNING: No user accounts found for note generation")
        return
    
    # Generate 2-5 notes per user with random dates in the past 90 days
    for user_id in all_user_ids:
        num_notes = random.randint(2, 5)
        for _ in range(num_notes):
            note_id = self.generate_uuid()
            note_type = random.choice(note_types)
            content = random.choice(note_contents[note_type])
            
            # Random date within last 90 days
            days_ago = random.randint(0, 90)
            created_at = datetime.now() - timedelta(days=days_ago)
            
            note_rows.append([note_id, user_id, content, note_type, created_at])
    
    if note_rows:
        self.bulk_insert('note',
                        ['note_id', 'user_id', 'content', 'note_type', 'created_at'],
                        note_rows)
        
        self.add_statement(f"-- Generated {len(note_rows)} notes for {len(all_user_ids)} users")
    else:
        self.add_statement("-- No notes generated")

from modules.base_generator import SQLDataGenerator
SQLDataGenerator.create_schedule_changes = create_schedule_changes
SQLDataGenerator.create_notifications = create_notifications
SQLDataGenerator.create_documents = create_documents
SQLDataGenerator.create_regulations = create_regulations
SQLDataGenerator.create_notes = create_notes