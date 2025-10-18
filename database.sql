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
    citizen_id NVARCHAR,
    address NVARCHAR(500),
    profile_picture NVARCHAR(500),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1
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
    status NVARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    last_login_time DATETIME2,

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_user_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE
);

-- ============================================================
-- PERMISSIONS
-- ============================================================
CREATE TABLE permissions (
    permission_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    role_name NVARCHAR(50) NOT NULL CHECK (role_name IN ('Admin', 'Instructor', 'Student')),
    permission_name NVARCHAR(255) NOT NULL UNIQUE,
    description NVARCHAR(MAX),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1
);

-- ============================================================
-- STUDENT
-- ============================================================
CREATE TABLE student (
    student_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    student_code NVARCHAR(50) NOT NULL UNIQUE,
    class_id UNIQUEIDENTIFIER NULL,
    accumulated_credits INT DEFAULT 0 CHECK (accumulated_credits >= 0),
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'graduated', 'dropped_out')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_student_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE
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
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'retired')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_instructor_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE
);

-- ============================================================
-- ADMIN
-- ============================================================
CREATE TABLE admin (
    admin_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    person_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    admin_code NVARCHAR(50) NOT NULL UNIQUE,
    position NVARCHAR(200),
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_admin_person FOREIGN KEY (person_id)
        REFERENCES person(person_id) ON DELETE CASCADE
);

-- ============================================================
-- OTP & REFRESH TOKEN
-- ============================================================
CREATE TABLE user_otps (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    otp_code NVARCHAR(6) NOT NULL,
    expired_at DATETIME2 NOT NULL,
    is_used BIT NOT NULL DEFAULT 0,
    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_user_otps_user FOREIGN KEY (user_id) REFERENCES user_account(user_id) ON DELETE CASCADE
);

CREATE TABLE user_refresh_tokens (
    id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL,
    refresh_token NVARCHAR(500) NOT NULL,
    expires_at DATETIME2 NOT NULL,
    revoked BIT NOT NULL DEFAULT 0,
    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT FK_refresh_user FOREIGN KEY (user_id) REFERENCES user_account(user_id) ON DELETE CASCADE
);

-- ============================================================
-- FACULTY & DEPARTMENT
-- ============================================================
CREATE TABLE faculty (
    faculty_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    faculty_name NVARCHAR(200) NOT NULL,
    faculty_code NVARCHAR(50) NOT NULL UNIQUE,
    dean_id UNIQUEIDENTIFIER NULL,
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','inactive')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_faculty_dean FOREIGN KEY (dean_id) REFERENCES instructor(instructor_id) ON DELETE SET NULL
);

CREATE TABLE department (
    department_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    department_name NVARCHAR(200) NOT NULL,
    department_code NVARCHAR(50) NOT NULL UNIQUE,
    faculty_id UNIQUEIDENTIFIER NOT NULL,
    head_of_department_id UNIQUEIDENTIFIER NULL,

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_department_faculty FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE,
    CONSTRAINT FK_department_head FOREIGN KEY (head_of_department_id) REFERENCES instructor(instructor_id) ON DELETE SET NULL
);

-- ============================================================
-- ACADEMIC YEAR & CLASS
-- ============================================================
CREATE TABLE academic_year (
    academic_year_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status NVARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1
);

CREATE TABLE class (
    class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    class_code NVARCHAR(50) NOT NULL UNIQUE,
    class_name NVARCHAR(200) NOT NULL,
    department_id UNIQUEIDENTIFIER NOT NULL,
    start_academic_year_id UNIQUEIDENTIFIER NOT NULL,
    end_academic_year_id UNIQUEIDENTIFIER NULL,
    curriculum_desc_pdf NVARCHAR(1000),
    
    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_class_department FOREIGN KEY (department_id) REFERENCES department(department_id) ON DELETE CASCADE,
    CONSTRAINT FK_class_start_year FOREIGN KEY (start_academic_year_id) REFERENCES academic_year(academic_year_id),
    CONSTRAINT FK_class_end_year FOREIGN KEY (end_academic_year_id) REFERENCES academic_year(academic_year_id)
);

ALTER TABLE student ADD CONSTRAINT FK_student_class FOREIGN KEY (class_id) REFERENCES class(class_id);
ALTER TABLE instructor ADD CONSTRAINT FK_instructor_department FOREIGN KEY (department_id) REFERENCES department(department_id);

-- ============================================================
-- SUBJECT & SEMESTER
-- ============================================================
CREATE TABLE subject (
    subject_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    subject_name NVARCHAR(200) NOT NULL,
    subject_code NVARCHAR(50) NOT NULL UNIQUE,
    credits INT NOT NULL CHECK (credits > 0),
    theory_hours INT DEFAULT 0,
    practice_hours INT DEFAULT 0,
    is_general BIT DEFAULT 0,
    department_id UNIQUEIDENTIFIER NOT NULL,
    prerequisite_subject_id UNIQUEIDENTIFIER NULL,
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_subject_department FOREIGN KEY (department_id) REFERENCES department(department_id),
    CONSTRAINT FK_subject_prerequisite FOREIGN KEY (prerequisite_subject_id) REFERENCES subject(subject_id)
);

CREATE TABLE semester (
    semester_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    semester_name NVARCHAR(100) NOT NULL,
    academic_year_id UNIQUEIDENTIFIER NOT NULL,
    semester_type NVARCHAR(20) NOT NULL CHECK (semester_type IN ('fall', 'spring', 'summer')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    registration_start_date DATE NOT NULL,
    registration_end_date DATE NOT NULL,
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_semester_academic_year FOREIGN KEY (academic_year_id) REFERENCES academic_year(academic_year_id)
);

-- ============================================================
-- CURRICULUM (Chi tiết chương trình đào tạo)
-- ============================================================
CREATE TABLE curriculum_detail (
    curriculum_detail_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    class_id UNIQUEIDENTIFIER NOT NULL,
    subject_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_curriculum_detail_class FOREIGN KEY (class_id) REFERENCES class(class_id),
    CONSTRAINT FK_curriculum_detail_subject FOREIGN KEY (subject_id) REFERENCES subject(subject_id),
    CONSTRAINT FK_curriculum_detail_semester FOREIGN KEY (semester_id) REFERENCES semester(semester_id),
);

-- ============================================================
-- COURSE (Học phần)
-- ============================================================
CREATE TABLE course (
    course_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    subject_id UNIQUEIDENTIFIER NOT NULL,
    instructor_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,
    fee_per_credit NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (fee_per_credit >= 0),
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'completed', 'cancelled')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_course_subject FOREIGN KEY (subject_id) REFERENCES subject(subject_id) ON DELETE CASCADE,
    CONSTRAINT FK_course_instructor FOREIGN KEY (instructor_id) REFERENCES instructor(instructor_id) ON DELETE NO ACTION,
    CONSTRAINT FK_course_semester FOREIGN KEY (semester_id) REFERENCES semester(semester_id) ON DELETE CASCADE
);

-- ============================================================
-- BUILDING & ROOM
-- ============================================================
CREATE TABLE building (
    building_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    building_name NVARCHAR(200) NOT NULL,
    building_code NVARCHAR(50) NOT NULL UNIQUE,
    address NVARCHAR(500),
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1
);

CREATE TABLE room (
    room_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    room_code NVARCHAR(50) NOT NULL UNIQUE,
    room_name NVARCHAR(200) NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0),
    room_type NVARCHAR(20) NOT NULL CHECK (room_type IN ('lecture_hall', 'classroom', 'computer_lab', 'laboratory')),
    building_id UNIQUEIDENTIFIER NOT NULL,
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,
    
    CONSTRAINT FK_room_building FOREIGN KEY (building_id) REFERENCES building(building_id)
);

-- ============================================================
-- ROOM BOOKING (NEW - Centralized room reservation system)
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
    status NVARCHAR(20) DEFAULT 'confirmed' CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_room_booking_room FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE CASCADE,
    CONSTRAINT FK_room_booking_user FOREIGN KEY (booked_by) REFERENCES user_account(user_id) ON DELETE NO ACTION,
    CHECK (end_time > start_time)
);

-- ============================================================
-- COURSE CLASS (Lớp học phần) - References room directly
-- ============================================================
CREATE TABLE course_class (
    course_class_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_id UNIQUEIDENTIFIER NOT NULL,
    room_id UNIQUEIDENTIFIER NOT NULL,
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    max_students INT NOT NULL CHECK (max_students > 0),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 2 AND 8),
    start_period INT NOT NULL CHECK (start_period BETWEEN 1 AND 16),
    end_period INT NOT NULL CHECK (end_period BETWEEN 1 AND 16),
    status NVARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'completed', 'cancelled')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_course_class_course FOREIGN KEY (course_id) REFERENCES course(course_id) ON DELETE CASCADE,
    CONSTRAINT FK_course_class_room FOREIGN KEY (room_id) REFERENCES room(room_id) ON DELETE NO ACTION,
    CHECK (end_period >= start_period),
    CHECK (date_end >= date_start)
);

-- ============================================================
-- CLASS COURSE STUDENT (Student enrollment in course class)
-- ============================================================
CREATE TABLE class_course_student (
    enrollment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    enrollment_date DATE DEFAULT GETDATE(),
    status NVARCHAR(20) DEFAULT 'registered' CHECK (status IN ('registered', 'dropped', 'completed')),
    attendance_grade NUMERIC(4,2) CHECK (attendance_grade BETWEEN 0 AND 10),
    midterm_grade NUMERIC(4,2) CHECK (midterm_grade BETWEEN 0 AND 10),
    final_grade NUMERIC(4,2) CHECK (final_grade BETWEEN 0 AND 10),
    is_paid BIT NOT NULL DEFAULT 0,

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT UQ_student_course_class UNIQUE (student_id, course_class_id),
    CONSTRAINT FK_class_course_student_student FOREIGN KEY (student_id) REFERENCES student(student_id) ON DELETE CASCADE,
    CONSTRAINT FK_class_course_student_course_class FOREIGN KEY (course_class_id) REFERENCES course_class(course_class_id) ON DELETE CASCADE
);

-- ============================================================
-- SCHEDULE CHANGE (Thay đổi lịch học)
-- ============================================================
CREATE TABLE schedule_change (
    schedule_change_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    cancelled_week INT NOT NULL CHECK (cancelled_week > 0),
    makeup_week INT CHECK (makeup_week > 0),
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 2 AND 8),
    start_period INT NOT NULL CHECK (start_period BETWEEN 1 AND 16),
    end_period INT NOT NULL CHECK (end_period BETWEEN 1 AND 16),
    reason NVARCHAR(500),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_schedule_change_course_class FOREIGN KEY (course_class_id) REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CHECK (end_period >= start_period)
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
    uploaded_by UNIQUEIDENTIFIER NOT NULL,
    description NVARCHAR(1000),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_document_course_class FOREIGN KEY (course_class_id) REFERENCES course_class(course_class_id),
    CONSTRAINT FK_document_uploader FOREIGN KEY (uploaded_by) REFERENCES user_account(user_id)
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

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_notification_creator FOREIGN KEY (created_by_user) REFERENCES user_account(user_id)
);
-- ============================================================
-- EXAM SCHEDULE - UPDATED to reference room_booking
-- ============================================================
CREATE TABLE exam_schedule (
    exam_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    course_class_id UNIQUEIDENTIFIER NOT NULL,
    room_booking_id UNIQUEIDENTIFIER NOT NULL,
    exam_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    exam_format NVARCHAR(50) NOT NULL CHECK (exam_format IN ('multiple_choice', 'essay', 'practical', 'oral')),
    exam_type NVARCHAR(20) DEFAULT 'final' CHECK (exam_type IN ('midterm', 'final', 'makeup')),
    notes NVARCHAR(500),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_exam_course_class FOREIGN KEY (course_class_id) REFERENCES course_class(course_class_id) ON DELETE CASCADE,
    CONSTRAINT FK_exam_room_booking FOREIGN KEY (room_booking_id) REFERENCES room_booking(booking_id) ON DELETE NO ACTION,
    CHECK (end_time > start_time)
);

-- ============================================================
-- SCHOLARSHIP REQUEST (One per student for entire time on campus)
-- ============================================================
CREATE TABLE scholarship_request (
    request_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL UNIQUE,
    verification_document_path NVARCHAR(1000),
    eligible_type INT NOT NULL CHECK (eligible_type IN (40, 60, 100)),
    status NVARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'denied', 'failed')),
    approved_date DATETIME2 NULL,
    denied_date DATETIME2 NULL,
    failed_date DATETIME2 NULL,

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_scholarship_student FOREIGN KEY (student_id) 
        REFERENCES student(student_id) ON DELETE CASCADE
);

-- ============================================================
-- PAYMENT (Student payment per semester)
-- ============================================================
CREATE TABLE payment (
    payment_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    student_id UNIQUEIDENTIFIER NOT NULL,
    semester_id UNIQUEIDENTIFIER NOT NULL,
    amount NUMERIC(15,2) NOT NULL CHECK (amount >= 0),
    payment_date DATETIME2 NOT NULL DEFAULT GETDATE(),
    payment_method NVARCHAR(50) NOT NULL CHECK (payment_method IN ('bank_transfer', 'cash', 'online', 'credit_card', 'e_wallet')),
    status NVARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'rejected')),

    created DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated DATETIME2 NULL,
    created_by UNIQUEIDENTIFIER NULL,
    updated_by UNIQUEIDENTIFIER NULL,
    deleted BIT NOT NULL DEFAULT 0,
    active BIT NOT NULL DEFAULT 1,

    CONSTRAINT FK_payment_student FOREIGN KEY (student_id) 
        REFERENCES student(student_id) ON DELETE CASCADE,
    CONSTRAINT FK_payment_semester FOREIGN KEY (semester_id) 
        REFERENCES semester(semester_id) ON DELETE CASCADE
);