-- ============================================================
-- CONFLICT DETECTION QUERIES
-- ============================================================
-- Conflicts are defined as:
-- - Same day, same room, overlapping time periods
-- - Time periods are grouped into: Morning (1-5), Afternoon (6-9), Evening (10-12)

USE EduManagement;
GO

-- ============================================================
-- 1. CHECK FOR COURSE CLASS CONFLICTS
-- ============================================================
-- Two course classes conflict if they have the same day_of_week, same room_id, 
-- and overlapping time periods (same period block: morning/afternoon/evening)

WITH CourseClassTimeBlocks AS (
    SELECT 
        cc.course_class_id,
        cc.course_id,
        s.subject_name,
        s.subject_code,
        cc.room_id,
        r.room_code,
        cc.day_of_week,
        cc.start_period,
        cc.end_period,
        cc.date_start,
        cc.date_end,
        -- Determine time block
        CASE 
            WHEN cc.start_period BETWEEN 1 AND 5 THEN 'Morning'
            WHEN cc.start_period BETWEEN 6 AND 9 THEN 'Afternoon'  
            WHEN cc.start_period BETWEEN 10 AND 12 THEN 'Evening'
        END AS time_block,
        p.full_name AS instructor_name,
        i.instructor_code
    FROM course_class cc
    INNER JOIN course c ON cc.course_id = c.course_id
    INNER JOIN subject s ON c.subject_id = s.subject_id
    INNER JOIN room r ON cc.room_id = r.room_id
    LEFT JOIN instructor i ON cc.instructor_id = i.instructor_id
    LEFT JOIN person p ON i.person_id = p.person_id
    WHERE cc.is_active = 1 AND cc.is_deleted = 0
)
SELECT 
    'COURSE CLASS CONFLICTS' AS conflict_type,
    cc1.subject_code + ' (' + cc1.subject_name + ')' AS course1,
    cc2.subject_code + ' (' + cc2.subject_name + ')' AS course2,
    cc1.room_code,
    CASE cc1.day_of_week 
        WHEN 2 THEN 'Monday'
        WHEN 3 THEN 'Tuesday' 
        WHEN 4 THEN 'Wednesday'
        WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
        WHEN 7 THEN 'Saturday'
        WHEN 8 THEN 'Sunday'
    END AS day_of_week,
    cc1.time_block,
    'Periods ' + CAST(cc1.start_period AS VARCHAR) + '-' + CAST(cc1.end_period AS VARCHAR) AS periods1,
    'Periods ' + CAST(cc2.start_period AS VARCHAR) + '-' + CAST(cc2.end_period AS VARCHAR) AS periods2,
    cc1.instructor_name AS instructor1,
    cc2.instructor_name AS instructor2,
    'Date overlap: ' + CAST(GREATEST(cc1.date_start, cc2.date_start) AS VARCHAR) + 
    ' to ' + CAST(LEAST(cc1.date_end, cc2.date_end) AS VARCHAR) AS date_overlap_period
FROM CourseClassTimeBlocks cc1
INNER JOIN CourseClassTimeBlocks cc2 ON 
    cc1.course_class_id < cc2.course_class_id  -- Avoid duplicates
    AND cc1.day_of_week = cc2.day_of_week      -- Same day of week
    AND cc1.room_id = cc2.room_id              -- Same room
    AND cc1.time_block = cc2.time_block        -- Same time block (morning/afternoon/evening)
    AND (
        -- Date ranges overlap
        cc1.date_start <= cc2.date_end 
        AND cc1.date_end >= cc2.date_start
    )
ORDER BY cc1.day_of_week, cc1.room_code, cc1.start_period;

-- ============================================================
-- 2. CHECK FOR EXAM CONFLICTS  
-- ============================================================
-- Two exams conflict if they are scheduled at the same room and overlapping times

WITH ExamTimeBlocks AS (
    SELECT 
        ec.exam_class_id,
        ec.exam_id,
        s.subject_name,
        s.subject_code,
        e.exam_type,
        ec.room_id,
        r.room_code,
        ec.start_time,
        DATEADD(MINUTE, ec.duration_minutes, ec.start_time) AS end_time,
        CAST(ec.start_time AS DATE) AS exam_date,
        -- Determine time block based on hour
        CASE 
            WHEN DATEPART(HOUR, ec.start_time) BETWEEN 6 AND 11 THEN 'Morning'
            WHEN DATEPART(HOUR, ec.start_time) BETWEEN 12 AND 17 THEN 'Afternoon'
            WHEN DATEPART(HOUR, ec.start_time) BETWEEN 18 AND 23 THEN 'Evening'
            ELSE 'Night'
        END AS time_block,
        p.full_name AS monitor_instructor,
        i.instructor_code
    FROM exam_class ec
    INNER JOIN exam e ON ec.exam_id = e.exam_id
    INNER JOIN course c ON e.course_id = c.course_id
    INNER JOIN subject s ON c.subject_id = s.subject_id
    INNER JOIN room r ON ec.room_id = r.room_id
    LEFT JOIN instructor i ON ec.monitor_instructor_id = i.instructor_id
    LEFT JOIN person p ON i.person_id = p.person_id
    WHERE ec.is_active = 1 AND ec.is_deleted = 0
        AND ec.exam_status = 'scheduled'
)
SELECT 
    'EXAM CONFLICTS' AS conflict_type,
    e1.subject_code + ' (' + e1.subject_name + ') - ' + e1.exam_type AS exam1,
    e2.subject_code + ' (' + e2.subject_name + ') - ' + e2.exam_type AS exam2,
    e1.room_code,
    CAST(e1.exam_date AS VARCHAR) AS exam_date,
    e1.time_block,
    CAST(e1.start_time AS VARCHAR) + ' - ' + CAST(e1.end_time AS VARCHAR) AS time_period1,
    CAST(e2.start_time AS VARCHAR) + ' - ' + CAST(e2.end_time AS VARCHAR) AS time_period2,
    e1.monitor_instructor AS monitor1,
    e2.monitor_instructor AS monitor2,
    'Overlap: ' + CAST(GREATEST(e1.start_time, e2.start_time) AS VARCHAR) + 
    ' to ' + CAST(LEAST(e1.end_time, e2.end_time) AS VARCHAR) AS overlap_period
FROM ExamTimeBlocks e1
INNER JOIN ExamTimeBlocks e2 ON 
    e1.exam_class_id < e2.exam_class_id        -- Avoid duplicates
    AND e1.room_id = e2.room_id                -- Same room
    AND e1.exam_date = e2.exam_date           -- Same date
    AND e1.start_time < e2.end_time           -- Time overlap condition
    AND e1.end_time > e2.start_time           -- Time overlap condition
ORDER BY e1.exam_date, e1.room_code, e1.start_time;

-- ============================================================
-- 3. CHECK CONFLICTS FOR TEST STUDENT (student.test@edu.vn)
-- ============================================================

DECLARE @StudentTestEmail VARCHAR(255) = 'student.test@edu.vn';

-- Get the student ID
DECLARE @StudentId UNIQUEIDENTIFIER;
SELECT @StudentId = s.student_id 
FROM student s
INNER JOIN person p ON s.person_id = p.person_id 
WHERE p.email = @StudentTestEmail;

IF @StudentId IS NOT NULL
BEGIN
    -- Course class conflicts for the test student
    WITH StudentCourseSchedule AS (
        SELECT 
            se.enrollment_id,
            cc.course_class_id,
            s.subject_code,
            s.subject_name,
            cc.day_of_week,
            cc.start_period,
            cc.end_period,
            cc.date_start,
            cc.date_end,
            r.room_code,
            CASE 
                WHEN cc.start_period BETWEEN 1 AND 5 THEN 'Morning'
                WHEN cc.start_period BETWEEN 6 AND 9 THEN 'Afternoon'  
                WHEN cc.start_period BETWEEN 10 AND 12 THEN 'Evening'
            END AS time_block
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN room r ON cc.room_id = r.room_id
        WHERE se.student_id = @StudentId 
            AND se.is_active = 1 
            AND se.enrollment_status = 'registered'
    ),
    StudentExamSchedule AS (
        SELECT 
            ec.exam_class_id,
            s.subject_code,
            s.subject_name,
            e.exam_type,
            ec.start_time,
            DATEADD(MINUTE, ec.duration_minutes, ec.start_time) AS end_time,
            CAST(ec.start_time AS DATE) AS exam_date,
            DATEPART(dw, ec.start_time) + 1 AS day_of_week, -- Convert to match course_class day_of_week
            r.room_code,
            CASE 
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 6 AND 11 THEN 'Morning'
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 12 AND 17 THEN 'Afternoon'
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 18 AND 23 THEN 'Evening'
                ELSE 'Night'
            END AS time_block
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
        INNER JOIN exam e ON ec.exam_id = e.exam_id
        INNER JOIN course c ON e.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN room r ON ec.room_id = r.room_id
        WHERE se.student_id = @StudentId 
            AND se.is_active = 1 
            AND se.enrollment_status = 'registered'
            AND ec.exam_status = 'scheduled'
    )
    
    -- Course vs Course conflicts
    SELECT 
        'STUDENT COURSE-COURSE CONFLICT' AS conflict_type,
        @StudentTestEmail AS student_email,
        c1.subject_code + ' vs ' + c2.subject_code AS conflict_subjects,
        CASE c1.day_of_week 
            WHEN 2 THEN 'Monday' WHEN 3 THEN 'Tuesday' WHEN 4 THEN 'Wednesday'
            WHEN 5 THEN 'Thursday' WHEN 6 THEN 'Friday' WHEN 7 THEN 'Saturday'
            WHEN 8 THEN 'Sunday'
        END AS day_of_week,
        c1.time_block,
        'Periods ' + CAST(c1.start_period AS VARCHAR) + '-' + CAST(c1.end_period AS VARCHAR) + 
        ' vs ' + CAST(c2.start_period AS VARCHAR) + '-' + CAST(c2.end_period AS VARCHAR) AS time_periods,
        c1.room_code + ' vs ' + c2.room_code AS rooms
    FROM StudentCourseSchedule c1
    INNER JOIN StudentCourseSchedule c2 ON 
        c1.course_class_id < c2.course_class_id
        AND c1.day_of_week = c2.day_of_week
        AND c1.time_block = c2.time_block
        AND (c1.date_start <= c2.date_end AND c1.date_end >= c2.date_start)

    UNION ALL

    -- Exam vs Exam conflicts  
    SELECT 
        'STUDENT EXAM-EXAM CONFLICT' AS conflict_type,
        @StudentTestEmail AS student_email,
        e1.subject_code + ' (' + e1.exam_type + ') vs ' + e2.subject_code + ' (' + e2.exam_type + ')' AS conflict_subjects,
        CAST(e1.exam_date AS VARCHAR) AS day_of_week,
        e1.time_block + ' vs ' + e2.time_block AS time_block,
        CAST(e1.start_time AS VARCHAR) + '-' + CAST(e1.end_time AS VARCHAR) + 
        ' vs ' + CAST(e2.start_time AS VARCHAR) + '-' + CAST(e2.end_time AS VARCHAR) AS time_periods,
        e1.room_code + ' vs ' + e2.room_code AS rooms
    FROM StudentExamSchedule e1
    INNER JOIN StudentExamSchedule e2 ON 
        e1.exam_class_id < e2.exam_class_id
        AND e1.exam_date = e2.exam_date
        AND e1.start_time < e2.end_time 
        AND e1.end_time > e2.start_time

    UNION ALL

    -- Course vs Exam conflicts (same day, overlapping time blocks)
    SELECT 
        'STUDENT COURSE-EXAM CONFLICT' AS conflict_type,
        @StudentTestEmail AS student_email,
        c.subject_code + ' (Course) vs ' + e.subject_code + ' (' + e.exam_type + ')' AS conflict_subjects,
        CASE c.day_of_week 
            WHEN 2 THEN 'Monday' WHEN 3 THEN 'Tuesday' WHEN 4 THEN 'Wednesday'
            WHEN 5 THEN 'Thursday' WHEN 6 THEN 'Friday' WHEN 7 THEN 'Saturday'
            WHEN 8 THEN 'Sunday'
        END AS day_of_week,
        c.time_block + ' vs ' + e.time_block AS time_block,
        'Periods ' + CAST(c.start_period AS VARCHAR) + '-' + CAST(c.end_period AS VARCHAR) + 
        ' vs Exam time' AS time_periods,
        c.room_code + ' vs ' + e.room_code AS rooms
    FROM StudentCourseSchedule c
    INNER JOIN StudentExamSchedule e ON 
        c.day_of_week = e.day_of_week
        AND c.time_block = e.time_block
        AND e.exam_date BETWEEN c.date_start AND c.date_end
    
    ORDER BY conflict_type, day_of_week;
END
ELSE
BEGIN
    SELECT 'No student found with email: ' + @StudentTestEmail AS message;
END

-- ============================================================
-- 4. CHECK CONFLICTS FOR TEST INSTRUCTOR (instructor.test@edu.vn)
-- ============================================================

DECLARE @InstructorTestEmail VARCHAR(255) = 'instructor.test@edu.vn';

-- Get the instructor ID
DECLARE @InstructorId UNIQUEIDENTIFIER;
SELECT @InstructorId = i.instructor_id 
FROM instructor i
INNER JOIN person p ON i.person_id = p.person_id 
WHERE p.email = @InstructorTestEmail;

IF @InstructorId IS NOT NULL
BEGIN
    -- Teaching schedule for the instructor
    WITH InstructorCourseSchedule AS (
        SELECT 
            cc.course_class_id,
            s.subject_code,
            s.subject_name,
            cc.day_of_week,
            cc.start_period,
            cc.end_period,
            cc.date_start,
            cc.date_end,
            r.room_code,
            CASE 
                WHEN cc.start_period BETWEEN 1 AND 5 THEN 'Morning'
                WHEN cc.start_period BETWEEN 6 AND 9 THEN 'Afternoon'  
                WHEN cc.start_period BETWEEN 10 AND 12 THEN 'Evening'
            END AS time_block
        FROM course_class cc
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN room r ON cc.room_id = r.room_id
        WHERE cc.instructor_id = @InstructorId
            AND cc.is_active = 1 
            AND cc.course_class_status = 'active'
    ),
    InstructorExamSchedule AS (
        SELECT 
            ec.exam_class_id,
            s.subject_code,
            s.subject_name,
            e.exam_type,
            ec.start_time,
            DATEADD(MINUTE, ec.duration_minutes, ec.start_time) AS end_time,
            CAST(ec.start_time AS DATE) AS exam_date,
            DATEPART(dw, ec.start_time) + 1 AS day_of_week,
            r.room_code,
            CASE 
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 6 AND 11 THEN 'Morning'
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 12 AND 17 THEN 'Afternoon'
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 18 AND 23 THEN 'Evening'
                ELSE 'Night'
            END AS time_block
        FROM exam_class ec
        INNER JOIN exam e ON ec.exam_id = e.exam_id
        INNER JOIN course c ON e.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN room r ON ec.room_id = r.room_id
        WHERE ec.monitor_instructor_id = @InstructorId
            AND ec.is_active = 1 
            AND ec.exam_status = 'scheduled'
    )
    
    -- Course vs Course conflicts
    SELECT 
        'INSTRUCTOR COURSE-COURSE CONFLICT' AS conflict_type,
        @InstructorTestEmail AS instructor_email,
        c1.subject_code + ' vs ' + c2.subject_code AS conflict_subjects,
        CASE c1.day_of_week 
            WHEN 2 THEN 'Monday' WHEN 3 THEN 'Tuesday' WHEN 4 THEN 'Wednesday'
            WHEN 5 THEN 'Thursday' WHEN 6 THEN 'Friday' WHEN 7 THEN 'Saturday'
            WHEN 8 THEN 'Sunday'
        END AS day_of_week,
        c1.time_block,
        'Periods ' + CAST(c1.start_period AS VARCHAR) + '-' + CAST(c1.end_period AS VARCHAR) + 
        ' vs ' + CAST(c2.start_period AS VARCHAR) + '-' + CAST(c2.end_period AS VARCHAR) AS time_periods,
        c1.room_code + ' vs ' + c2.room_code AS rooms
    FROM InstructorCourseSchedule c1
    INNER JOIN InstructorCourseSchedule c2 ON 
        c1.course_class_id < c2.course_class_id
        AND c1.day_of_week = c2.day_of_week
        AND c1.time_block = c2.time_block
        AND (c1.date_start <= c2.date_end AND c1.date_end >= c2.date_start)

    UNION ALL

    -- Exam monitoring vs Exam monitoring conflicts
    SELECT 
        'INSTRUCTOR EXAM-EXAM CONFLICT' AS conflict_type,
        @InstructorTestEmail AS instructor_email,
        e1.subject_code + ' (' + e1.exam_type + ') vs ' + e2.subject_code + ' (' + e2.exam_type + ')' AS conflict_subjects,
        CAST(e1.exam_date AS VARCHAR) AS day_of_week,
        e1.time_block + ' vs ' + e2.time_block AS time_block,
        CAST(e1.start_time AS VARCHAR) + '-' + CAST(e1.end_time AS VARCHAR) + 
        ' vs ' + CAST(e2.start_time AS VARCHAR) + '-' + CAST(e2.end_time AS VARCHAR) AS time_periods,
        e1.room_code + ' vs ' + e2.room_code AS rooms
    FROM InstructorExamSchedule e1
    INNER JOIN InstructorExamSchedule e2 ON 
        e1.exam_class_id < e2.exam_class_id
        AND e1.exam_date = e2.exam_date
        AND e1.start_time < e2.end_time 
        AND e1.end_time > e2.start_time

    UNION ALL

    -- Teaching vs Exam monitoring conflicts
    SELECT 
        'INSTRUCTOR COURSE-EXAM CONFLICT' AS conflict_type,
        @InstructorTestEmail AS instructor_email,
        c.subject_code + ' (Teaching) vs ' + e.subject_code + ' (Monitoring ' + e.exam_type + ')' AS conflict_subjects,
        CASE c.day_of_week 
            WHEN 2 THEN 'Monday' WHEN 3 THEN 'Tuesday' WHEN 4 THEN 'Wednesday'
            WHEN 5 THEN 'Thursday' WHEN 6 THEN 'Friday' WHEN 7 THEN 'Saturday'
            WHEN 8 THEN 'Sunday'
        END AS day_of_week,
        c.time_block + ' vs ' + e.time_block AS time_block,
        'Periods ' + CAST(c.start_period AS VARCHAR) + '-' + CAST(c.end_period AS VARCHAR) + 
        ' vs Exam monitoring' AS time_periods,
        c.room_code + ' vs ' + e.room_code AS rooms
    FROM InstructorCourseSchedule c
    INNER JOIN InstructorExamSchedule e ON 
        c.day_of_week = e.day_of_week
        AND c.time_block = e.time_block
        AND e.exam_date BETWEEN c.date_start AND c.date_end
    
    ORDER BY conflict_type, day_of_week;
END
ELSE
BEGIN
    SELECT 'No instructor found with email: ' + @InstructorTestEmail AS message;
END