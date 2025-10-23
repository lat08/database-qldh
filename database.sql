USE EduManagement;
GO

-- ============================================================
-- PERSON (Thông tin cá nhân)
-- ============================================================
CREATE TABLE person (
    person_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    full_name NVARCHAR(200) NOT NULL,
    date_of_birth DATE,
    gender NVARCHAR(10) CHECK (gender IN ('male', 'female')),
    email NVARCHAR(255) NOT NULL UNIQUE,
    phone_number NVARCHAR(20),
    citizen_id NVARCHAR(50),
    address NVARCHAR(500),
    profile_picture NVARCHAR(500),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- USER ACCOUNT
-- ============================================================
CREATE TABLE user_account (
    user_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    username NVARCHAR(100) NOT NULL UNIQUE,
    password_hash NVARCHAR(255) NOT NULL,
    password_salt NVARCHAR(255) NOT NULL,
    role_name NVARCHAR(50) NOT NULL CHECK (role_name IN ('Admin', 'Instructor', 'Student')),
    email_verified BIT DEFAULT 0,
    email_verification_code NVARCHAR(255),
    account_status NVARCHAR(20) NOT NULL DEFAULT 'active' CHECK (account_status IN ('active', 'inactive', 'suspended')),
    last_login_time DATETIME2,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_user_account_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE
);

-- ============================================================
-- PERMISSIONS
-- ============================================================
CREATE TABLE permission (
    permission_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    role_name NVARCHAR(50) NOT NULL CHECK (role_name IN ('Admin', 'Instructor', 'Student')),
    permission_name NVARCHAR(255) NOT NULL UNIQUE,
    description NVARCHAR(MAX),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- OTP & REFRESH TOKEN
-- ============================================================
CREATE TABLE user_otp (
    otp_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    otp_code NVARCHAR(6) NOT NULL,
    expired_at DATETIME2 NOT NULL,
    is_used BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_user_otp_user_account FOREIGN KEY (user_id) 
        REFERENCES user_account(user_id) ON DELETE CASCADE
);

CREATE TABLE user_refresh_token (
    token_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    refresh_token NVARCHAR(500) NOT NULL,
    expires_at DATETIME2 NOT NULL,
    is_revoked BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    
    CONSTRAINT FK_user_refresh_token_user_account FOREIGN KEY (user_id) 
        REFERENCES user_account(user_id) ON DELETE CASCADE
);

-- ============================================================
-- BUILDING & ROOM
-- ============================================================
CREATE TABLE building (
    building_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    building_name NVARCHAR(200) NOT NULL,
    building_code NVARCHAR(50) NOT NULL UNIQUE,
    address NVARCHAR(500),
    building_status NVARCHAR(20) DEFAULT 'active' CHECK (building_status IN ('active', 'inactive', 'maintenance')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

CREATE TABLE room (
    room_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    room_code NVARCHAR(50) NOT NULL UNIQUE,
    room_name NVARCHAR(200) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    room_type NVARCHAR(20) NOT NULL CHECK (room_type IN ('lecture_hall', 'classroom', 'computer_lab', 'laboratory')),
    building_id UNIQUEIDENTIFIER NOT NULL,
    room_status NVARCHAR(20) DEFAULT 'active' CHECK (room_status IN ('active', 'inactive', 'maintenance')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    
    CONSTRAINT FK_room_building FOREIGN KEY (building_id) 
        REFERENCES building(building_id) ON DELETE CASCADE
);

-- ============================================================
-- ROOM_AMENITY
-- ============================================================
CREATE TABLE room_amenity (
    amenity_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    amenity_name NVARCHAR(100) NOT NULL UNIQUE,
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- ROOM_AMENITY_MAPPING
-- ============================================================
CREATE TABLE room_amenity_mapping (
    room_amenity_mapping_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    room_id UNIQUEIDENTIFIER NOT NULL,
    amenity_id UNIQUEIDENTIFIER NOT NULL,
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    created_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    
    CONSTRAINT FK_room_amenity_mapping_room FOREIGN KEY (room_id)
        REFERENCES room(room_id) ON DELETE CASCADE,
    CONSTRAINT FK_room_amenity_mapping_amenity FOREIGN KEY (amenity_id)
        REFERENCES room_amenity(amenity_id) ON DELETE CASCADE,
    CONSTRAINT UQ_room_amenity_mapping UNIQUE (room_id, amenity_id)
);

-- ============================================================
-- ACADEMIC YEAR
-- ============================================================
CREATE TABLE academic_year (
    academic_year_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    year_name NVARCHAR(50) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    academic_year_status NVARCHAR(20) NOT NULL DEFAULT 'active' CHECK (academic_year_status IN ('active', 'inactive', 'completed')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,
    
    CONSTRAINT CHK_academic_year_dates CHECK (end_date > start_date)
);

-- ============================================================
-- SEMESTER
-- ============================================================
CREATE TABLE semester (
    semester_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    semester_name NVARCHAR(100) NOT NULL,
    academic_year_id UNIQUEIDENTIFIER NOT NULL,
    semester_type NVARCHAR(20) NOT NULL CHECK (semester_type IN ('fall', 'spring', 'summer')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    registration_start_date DATE NOT NULL,
    registration_end_date DATE NOT NULL,
    semester_status NVARCHAR(20) DEFAULT 'active' CHECK (semester_status IN ('active', 'inactive', 'completed')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_semester_academic_year FOREIGN KEY (academic_year_id) 
        REFERENCES academic_year(academic_year_id) ON DELETE CASCADE,
    CONSTRAINT CHK_semester_dates CHECK (end_date > start_date),
    CONSTRAINT CHK_semester_registration_dates CHECK (registration_end_date > registration_start_date),
    CONSTRAINT CHK_semester_registration_before_start CHECK (registration_end_date <= start_date)
);

-- ============================================================
-- FACULTY
-- ============================================================
CREATE TABLE faculty (
    faculty_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    faculty_name NVARCHAR(200) NOT NULL,
    faculty_code NVARCHAR(50) NOT NULL UNIQUE,
    dean_id UNIQUEIDENTIFIER NULL,
    faculty_status NVARCHAR(20) DEFAULT 'active' CHECK (faculty_status IN ('active','inactive')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- DEPARTMENT
-- ============================================================
CREATE TABLE department (
    department_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    department_name NVARCHAR(200) NOT NULL,
    department_code NVARCHAR(50) NOT NULL UNIQUE,
    faculty_id UNIQUEIDENTIFIER NOT NULL,
    head_of_department_id UNIQUEIDENTIFIER NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_department_faculty FOREIGN KEY (faculty_id) 
        REFERENCES faculty(faculty_id) ON DELETE CASCADE
);

-- ============================================================
-- INSTRUCTOR
-- ============================================================
CREATE TABLE instructor (
    instructor_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    instructor_code NVARCHAR(50) NOT NULL UNIQUE,
    degree NVARCHAR(200),
    specialization NVARCHAR(500),
    department_id UNIQUEIDENTIFIER NULL,
    hire_date DATE,
    employment_status NVARCHAR(20) DEFAULT 'active' CHECK (employment_status IN ('active', 'inactive', 'retired', 'on_leave')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_instructor_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE,
    CONSTRAINT FK_instructor_department FOREIGN KEY (department_id) 
        REFERENCES department(department_id) ON DELETE SET NULL
);

-- Add circular foreign keys
ALTER TABLE faculty 
    ADD CONSTRAINT FK_faculty_dean_instructor 
    FOREIGN KEY (dean_id) REFERENCES instructor(instructor_id) ON DELETE SET NULL;

ALTER TABLE department 
    ADD CONSTRAINT FK_department_head_instructor 
    FOREIGN KEY (head_of_department_id) REFERENCES instructor(instructor_id) ON DELETE SET NULL;

-- ============================================================
-- SUBJECT
-- ============================================================
CREATE TABLE subject (
    subject_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    subject_name NVARCHAR(200) NOT NULL,
    subject_code NVARCHAR(50) NOT NULL UNIQUE,
    credits INT NOT NULL CHECK (credits > 0),
    theory_hours INT DEFAULT 0 CHECK (theory_hours >= 0),
    practice_hours INT DEFAULT 0 CHECK (practice_hours >= 0),
    is_general BIT DEFAULT 0,
    department_id UNIQUEIDENTIFIER NOT NULL,
    prerequisite_subject_id UNIQUEIDENTIFIER NULL,
    subject_status NVARCHAR(20) DEFAULT 'active' CHECK (subject_status IN ('active', 'inactive', 'archived')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_subject_department FOREIGN KEY (department_id) 
        REFERENCES department(department_id) ON DELETE CASCADE,
    CONSTRAINT FK_subject_prerequisite_subject FOREIGN KEY (prerequisite_subject_id) 
        REFERENCES subject(subject_id) ON DELETE NO ACTION
);

-- ============================================================
-- CLASS
-- ============================================================
CREATE TABLE class (
    class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    class_code NVARCHAR(50) NOT NULL UNIQUE,
    class_name NVARCHAR(200) NOT NULL,
    department_id UNIQUEIDENTIFIER NOT NULL,
    advisor_instructor_id UNIQUEIDENTIFIER NULL,
    start_academic_year_id UNIQUEIDENTIFIER NOT NULL,
    end_academic_year_id UNIQUEIDENTIFIER NULL,
    curriculum_desc_pdf NVARCHAR(1000),
    class_status NVARCHAR(20) DEFAULT 'active' CHECK (class_status IN ('active', 'inactive', 'graduated')),
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_class_department FOREIGN KEY (department_id) 
        REFERENCES department(department_id) ON DELETE CASCADE,
    CONSTRAINT FK_class_advisor_instructor FOREIGN KEY (advisor_instructor_id)
        REFERENCES instructor(instructor_id) ON DELETE SET NULL,
    CONSTRAINT FK_class_start_academic_year FOREIGN KEY (start_academic_year_id) 
        REFERENCES academic_year(academic_year_id) ON DELETE NO ACTION,
    CONSTRAINT FK_class_end_academic_year FOREIGN KEY (end_academic_year_id) 
        REFERENCES academic_year(academic_year_id) ON DELETE NO ACTION
);

-- ============================================================
-- STUDENT
-- ============================================================
CREATE TABLE student (
    student_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    student_code NVARCHAR(50) NOT NULL UNIQUE,
    class_id UNIQUEIDENTIFIER NULL,
    enrollment_status NVARCHAR(20) DEFAULT 'active' CHECK (enrollment_status IN ('active', 'inactive', 'graduated', 'dropped_out', 'suspended')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_student_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE,
    CONSTRAINT FK_student_class FOREIGN KEY (class_id) 
        REFERENCES class(class_id) ON DELETE SET NULL
);

-- ============================================================
-- ADMIN
-- ============================================================
CREATE TABLE admin (
    admin_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    admin_code NVARCHAR(50) NOT NULL UNIQUE,
    position NVARCHAR(200),
    admin_status NVARCHAR(20) DEFAULT 'active' CHECK (admin_status IN ('active', 'inactive')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_admin_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE
);

-- ============================================================
-- CURRICULUM
-- ============================================================
CREATE TABLE curriculum_detail (
    curriculum_detail_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    department_id UNIQUEIDENTIFIER NOT NULL,
    subject_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_curriculum_detail_department FOREIGN KEY (department_id) 
        REFERENCES department(department_id) ON DELETE CASCADE,
    CONSTRAINT FK_curriculum_detail_subject FOREIGN KEY (subject_id) 
        REFERENCES subject(subject_id) ON DELETE NO ACTION,
    CONSTRAINT FK_curriculum_detail_semester FOREIGN KEY (semester_id) 
        REFERENCES semester(semester_id) ON DELETE CASCADE
);

-- ============================================================
-- COURSE
-- ============================================================
CREATE TABLE course (
    course_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    subject_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,
    fee_per_credit NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (fee_per_credit >= 0),
    course_status NVARCHAR(20) DEFAULT 'active' CHECK (course_status IN ('active', 'inactive', 'completed', 'cancelled')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_course_subject FOREIGN KEY (subject_id) 
        REFERENCES subject(subject_id) ON DELETE CASCADE,
    CONSTRAINT FK_course_semester FOREIGN KEY (semester_id) 
        REFERENCES semester(semester_id) ON DELETE CASCADE
);

-- ============================================================
-- COURSE CLASS
-- ============================================================
CREATE TABLE course_class (
    course_class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_id UNIQUEIDENTIFIER NOT NULL,
    instructor_id UNIQUEIDENTIFIER NULL,
    room_id UNIQUEIDENTIFIER NOT NULL,
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    max_students INT NOT NULL CHECK (max_students > 0),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 2 AND 8),
    start_period INT NOT NULL CHECK (start_period BETWEEN 1 AND 16),
    end_period INT NOT NULL CHECK (end_period BETWEEN 1 AND 16),
    course_class_status NVARCHAR(20) DEFAULT 'active' CHECK (course_class_status IN ('active', 'inactive', 'completed', 'cancelled')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_course_class_course FOREIGN KEY (course_id) 
        REFERENCES course(course_id) ON DELETE CASCADE,
    CONSTRAINT FK_course_class_instructor FOREIGN KEY (instructor_id) 
        REFERENCES instructor(instructor_id) ON DELETE SET NULL,
    CONSTRAINT FK_course_class_room FOREIGN KEY (room_id) 
        REFERENCES room(room_id) ON DELETE NO ACTION,
    CONSTRAINT CHK_course_class_periods CHECK (end_period >= start_period),
    CONSTRAINT CHK_course_class_dates CHECK (date_end > date_start)
);

-- ============================================================
-- STUDENT ENROLLMENT
-- ============================================================
CREATE TABLE student_enrollment (
    enrollment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    enrollment_date DATE DEFAULT GETDATE(),
    enrollment_status NVARCHAR(20) DEFAULT 'registered' CHECK (enrollment_status IN ('registered', 'dropped', 'completed', 'cancelled')),
    cancellation_date DATE NULL,
    cancellation_reason NVARCHAR(500) NULL,
    attendance_grade NUMERIC(4,2) CHECK (attendance_grade BETWEEN 0 AND 10),
    midterm_grade NUMERIC(4,2) CHECK (midterm_grade BETWEEN 0 AND 10),
    final_grade NUMERIC(4,2) CHECK (final_grade BETWEEN 0 AND 10),
    is_paid BIT NOT NULL DEFAULT 0,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT UQ_student_enrollment_course_class UNIQUE (student_id, course_class_id),
    CONSTRAINT FK_student_enrollment_student FOREIGN KEY (student_id) 
        REFERENCES student(student_id) ON DELETE CASCADE,
    CONSTRAINT FK_student_enrollment_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id) ON DELETE CASCADE
);

-- ============================================================
-- SCHEDULE CHANGE
-- ============================================================
CREATE TABLE schedule_change (
    schedule_change_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    cancelled_week INT NOT NULL CHECK (cancelled_week > 0),
    makeup_week INT CHECK (makeup_week > 0),
    makeup_date DATE NULL,
    makeup_room_id UNIQUEIDENTIFIER NULL,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 2 AND 8),
    start_period INT NOT NULL CHECK (start_period BETWEEN 1 AND 16),
    end_period INT NOT NULL CHECK (end_period BETWEEN 1 AND 16),
    reason NVARCHAR(500),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_schedule_change_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CONSTRAINT FK_schedule_change_makeup_room FOREIGN KEY (makeup_room_id) 
        REFERENCES room(room_id) ON DELETE NO ACTION,
    CONSTRAINT CHK_schedule_change_periods CHECK (end_period >= start_period)
);

-- ============================================================
-- DOCUMENT
-- ============================================================
CREATE TABLE document (
    document_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    file_name NVARCHAR(500) NOT NULL,
    file_path NVARCHAR(1000) NOT NULL,
    file_type NVARCHAR(20) CHECK (file_type IN ('pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls', 'jpg', 'jpeg', 'png', 'zip', 'rar')),
    file_size BIGINT CHECK (file_size > 0),
    uploaded_by UNIQUEIDENTIFIER NULL,
    description NVARCHAR(1000),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_document_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CONSTRAINT FK_document_uploaded_by_instructor FOREIGN KEY (uploaded_by) 
        REFERENCES instructor(instructor_id) ON DELETE SET NULL
);

-- ============================================================
-- NOTIFICATION
-- ============================================================
CREATE TABLE notification_schedule (
    schedule_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    notification_type NVARCHAR(50) NOT NULL CHECK (notification_type IN ('event', 'tuition', 'schedule', 'important')),
    title NVARCHAR(500) NOT NULL,
    content NVARCHAR(MAX),
    scheduled_date DATETIME2 NOT NULL,
    visible_from DATETIME2 NOT NULL,
    is_read BIT NOT NULL DEFAULT 0,
    target_type NVARCHAR(50) NOT NULL CHECK (target_type IN ('all', 'all_students', 'all_instructors', 'class', 'faculty', 'instructor')),
    target_id UNIQUEIDENTIFIER NULL,
    created_by_user UNIQUEIDENTIFIER NOT NULL,
    status NVARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_notification_creator FOREIGN KEY (created_by_user) 
        REFERENCES user_account(user_id) ON DELETE NO ACTION
);

-- ============================================================
-- EXAM (Course-level exam definition)
-- ============================================================
CREATE TABLE exam (
    exam_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_id UNIQUEIDENTIFIER NOT NULL,
    exam_format NVARCHAR(50) NOT NULL CHECK (exam_format IN ('multiple_choice', 'essay', 'practical', 'oral', 'mixed')),
    exam_type NVARCHAR(20) DEFAULT 'final' CHECK (exam_type IN ('midterm', 'final', 'makeup', 'quiz')),
    exam_file_pdf NVARCHAR(1000),
    answer_key_pdf NVARCHAR(1000),
    notes NVARCHAR(500),
    is_approved BIT NOT NULL DEFAULT 0,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_exam_course FOREIGN KEY (course_id) 
        REFERENCES course(course_id) ON DELETE CASCADE
);

-- ============================================================
-- EXAM CLASS (Exam schedule for specific course class)
-- ============================================================
CREATE TABLE exam_class (
    exam_class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    exam_id UNIQUEIDENTIFIER NOT NULL,
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    room_id UNIQUEIDENTIFIER NOT NULL,
    monitor_instructor_id UNIQUEIDENTIFIER NULL,
    start_time DATETIME2 NOT NULL,
    duration_minutes INT NOT NULL CHECK (duration_minutes > 0),
    exam_status NVARCHAR(20) DEFAULT 'scheduled' CHECK (exam_status IN ('scheduled', 'completed', 'cancelled')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_exam_class_exam FOREIGN KEY (exam_id) 
        REFERENCES exam(exam_id) ON DELETE NO ACTION,
    CONSTRAINT FK_exam_class_course_class FOREIGN KEY (course_class_id) 
        REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CONSTRAINT FK_exam_class_room FOREIGN KEY (room_id) 
        REFERENCES room(room_id) ON DELETE NO ACTION,
    CONSTRAINT FK_exam_class_monitor FOREIGN KEY (monitor_instructor_id) 
        REFERENCES instructor(instructor_id) ON DELETE SET NULL
);

-- ============================================================
-- STUDENT HEALTH INSURANCE
-- ============================================================
CREATE TABLE student_health_insurance (
    insurance_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    academic_year_id UNIQUEIDENTIFIER NOT NULL,
    insurance_fee NUMERIC(15,2) NOT NULL CHECK (insurance_fee >= 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    insurance_status NVARCHAR(20) DEFAULT 'active' CHECK (insurance_status IN ('active', 'expired', 'cancelled')),
    is_paid BIT NOT NULL DEFAULT 0,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_student_health_insurance_student FOREIGN KEY (student_id) 
        REFERENCES student(student_id) ON DELETE CASCADE,
    CONSTRAINT FK_student_health_insurance_academic_year FOREIGN KEY (academic_year_id) 
        REFERENCES academic_year(academic_year_id) ON DELETE CASCADE,
    CONSTRAINT UQ_student_academic_year_insurance UNIQUE (student_id, academic_year_id),
    CONSTRAINT CHK_student_health_insurance_dates CHECK (end_date > start_date)
);

-- ============================================================
-- PAYMENT_ENROLLMENT (Course Tuition Payments)
-- ============================================================
CREATE TABLE payment_enrollment (
    payment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    enrollment_id UNIQUEIDENTIFIER NOT NULL,
    payment_type NVARCHAR(50) NOT NULL CHECK (payment_type IN ('cash', 'qr')),
    payment_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    notes NVARCHAR(500),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_payment_enrollment_enrollment FOREIGN KEY (enrollment_id) 
        REFERENCES student_enrollment(enrollment_id) ON DELETE CASCADE
);

-- ============================================================
-- PAYMENT_INSURANCE (Health Insurance Payments)
-- ============================================================
CREATE TABLE payment_insurance (
    payment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    insurance_id UNIQUEIDENTIFIER NOT NULL,
    payment_type NVARCHAR(50) NOT NULL CHECK (payment_type IN ('cash', 'qr')),
    payment_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    notes NVARCHAR(500),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_payment_insurance_insurance FOREIGN KEY (insurance_id) 
        REFERENCES student_health_insurance(insurance_id) ON DELETE CASCADE
);

-- ============================================================
-- ROOM BOOKING
-- ============================================================
CREATE TABLE room_booking (
    booking_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    room_id UNIQUEIDENTIFIER NOT NULL,
    booking_type NVARCHAR(50) NOT NULL CHECK (booking_type IN ('course_class', 'exam', 'event', 'meeting', 'other')),
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    booked_by UNIQUEIDENTIFIER NOT NULL,
    purpose NVARCHAR(500),
    booking_status NVARCHAR(20) DEFAULT 'confirmed' CHECK (booking_status IN ('pending', 'confirmed', 'cancelled', 'completed')),

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_room_booking_room FOREIGN KEY (room_id) 
        REFERENCES room(room_id) ON DELETE CASCADE,
    CONSTRAINT FK_room_booking_user FOREIGN KEY (booked_by) 
        REFERENCES user_account(user_id) ON DELETE NO ACTION,
    CONSTRAINT CHK_room_booking_times CHECK (end_time > start_time)
);

-- ============================================================
-- REGULATION
-- ============================================================
CREATE TABLE regulation (
    regulation_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    regulation_name NVARCHAR(200) NOT NULL,
    target NVARCHAR(20) NOT NULL CHECK (target IN ('student', 'instructor')),
    pdf_file_path NVARCHAR(1000) NOT NULL,
    regulation_description NVARCHAR(1000) NOT NULL,
	expire_date DATE NULL,
    created_by_admin UNIQUEIDENTIFIER NOT NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_regulation_created_by_admin FOREIGN KEY (created_by_admin) 
        REFERENCES admin(admin_id) ON DELETE NO ACTION
);

-- ============================================================
-- STUDENT_VERIFICATION_REQUEST
-- ============================================================
CREATE TABLE student_verification_request (
    verification_request_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    language NVARCHAR(2) NOT NULL DEFAULT 'vi' CHECK (language IN ('vi', 'en')),
    reason NVARCHAR(500) NOT NULL,
    request_status NVARCHAR(20) DEFAULT 'pending' CHECK (request_status IN ('pending', 'approved', 'rejected', 'completed')),
    
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_verification_request_student FOREIGN KEY (student_id)
        REFERENCES student(student_id) ON DELETE CASCADE
);

-- ============================================================
-- PAYMENT_POSTPONEMENT_REQUEST
-- ============================================================
CREATE TABLE payment_postponement_request (
    request_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,
    request_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    reason NVARCHAR(500) NOT NULL,
    request_status NVARCHAR(20) DEFAULT 'pending' CHECK (request_status IN ('pending', 'approved', 'rejected', 'cancelled')),
    new_payment_deadline DATE NULL,
    
    -- Admin who reviewed/processed the request
    reviewed_by UNIQUEIDENTIFIER NULL,
    reviewed_at DATETIME2 NULL,
    review_notes NVARCHAR(500) NULL,

    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    is_deleted BIT NOT NULL DEFAULT 0,
    is_active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_payment_postponement_student FOREIGN KEY (student_id)
        REFERENCES student(student_id) ON DELETE CASCADE,
    CONSTRAINT FK_payment_postponement_semester FOREIGN KEY (semester_id) 
        REFERENCES semester(semester_id) ON DELETE CASCADE,
    CONSTRAINT FK_payment_postponement_reviewed_by FOREIGN KEY (reviewed_by)
        REFERENCES admin(admin_id) ON DELETE NO ACTION ON UPDATE NO ACTION,
    CONSTRAINT CHK_reviewed_at_when_processed CHECK (
        (request_status = 'pending' AND reviewed_by IS NULL AND reviewed_at IS NULL) OR
        (request_status IN ('approved', 'rejected') AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL) OR
        (request_status = 'cancelled')
    )
);