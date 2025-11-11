-- ============================================================
-- VERIFY TEST STUDENT EXAM DISTRIBUTION
-- ============================================================
-- This query verifies that the test student (student.test@edu.vn) has:
-- - 2 completed exams (on 11/6/2025 or before TODAY)
-- - 2 upcoming exams (on 11/12/2025)  
-- - 2 future exams (on 11/19/2025)
-- For the summer 2024-2025 semester

USE EduManagement;
GO

DECLARE @TestStudentEmail VARCHAR(255) = 'student.test@edu.vn';
DECLARE @TODAY DATE = CAST(GETDATE() AS DATE);

-- Get test student info
DECLARE @StudentId UNIQUEIDENTIFIER;
SELECT @StudentId = s.student_id 
FROM student s
INNER JOIN person p ON s.person_id = p.person_id 
WHERE p.email = @TestStudentEmail;

-- Find summer 2024-2025 semester  
DECLARE @SummerSemesterId UNIQUEIDENTIFIER;
SELECT @SummerSemesterId = s.semester_id
FROM semester s
INNER JOIN academic_year ay ON s.academic_year_id = ay.academic_year_id
WHERE s.semester_type = 'summer'
    AND ay.year_name = '2024-2025'  -- Academic year 2024-2025
    AND MONTH(s.end_date) = 11      -- Ends in November
    AND YEAR(s.end_date) = 2025;    -- Year 2025

-- Display student and semester info
SELECT 
    'VERIFICATION INFO' AS section,
    @TestStudentEmail AS test_student_email,
    CASE WHEN @StudentId IS NOT NULL THEN 'FOUND' ELSE 'NOT FOUND' END AS student_status,
    CASE WHEN @SummerSemesterId IS NOT NULL THEN 'FOUND' ELSE 'NOT FOUND' END AS summer_semester_status,
    @TODAY AS today_date;

-- If student and semester found, check exam distribution
IF @StudentId IS NOT NULL AND @SummerSemesterId IS NOT NULL
BEGIN
    -- Get all exams for test student in summer 2024-2025
    -- Display all exams with details
    WITH TestStudentExams AS (
        SELECT 
            ec.exam_class_id,
            ec.start_time,
            CAST(ec.start_time AS DATE) AS exam_date,
            CAST(ec.start_time AS TIME) AS exam_time,
            ec.exam_status,
            s.subject_code,
            s.subject_name,
            r.room_code,
            p_monitor.full_name AS monitor_instructor,
            
            -- Categorize exams based on date relative to TODAY
            CASE 
                WHEN CAST(ec.start_time AS DATE) < @TODAY THEN 'COMPLETED'
                WHEN CAST(ec.start_time AS DATE) = @TODAY THEN 'TODAY'
                WHEN CAST(ec.start_time AS DATE) BETWEEN DATEADD(DAY, 1, @TODAY) AND DATEADD(DAY, 7, @TODAY) THEN 'UPCOMING'
                WHEN CAST(ec.start_time AS DATE) > DATEADD(DAY, 7, @TODAY) THEN 'FUTURE'
                ELSE 'OTHER'
            END AS exam_category,
            
            -- Check if exam is on expected dates
            CASE 
                WHEN CAST(ec.start_time AS DATE) = '2025-11-06' THEN 'EXPECTED_COMPLETED'
                WHEN CAST(ec.start_time AS DATE) = '2025-11-12' THEN 'EXPECTED_UPCOMING'  
                WHEN CAST(ec.start_time AS DATE) = '2025-11-19' THEN 'EXPECTED_FUTURE'
                ELSE 'UNEXPECTED_DATE'
            END AS date_expectation
            
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
        INNER JOIN room r ON ec.room_id = r.room_id
        LEFT JOIN instructor i ON ec.monitor_instructor_id = i.instructor_id
        LEFT JOIN person p_monitor ON i.person_id = p_monitor.person_id
        WHERE se.student_id = @StudentId
            AND c.semester_id = @SummerSemesterId
            AND se.enrollment_status = 'registered'
            AND se.is_active = 1
            AND se.is_deleted = 0
    )
    SELECT 
        'EXAM DETAILS' AS section,
        exam_date,
        exam_time,
        subject_code + ' - ' + subject_name AS subject,
        room_code,
        monitor_instructor,
        exam_status,
        exam_category,
        date_expectation
    FROM TestStudentExams
    ORDER BY exam_date, exam_time;
    
    -- Summary by category
    WITH TestStudentExams AS (
        SELECT 
            ec.exam_class_id,
            ec.start_time,
            CAST(ec.start_time AS DATE) AS exam_date,
            CAST(ec.start_time AS TIME) AS exam_time,
            ec.exam_status,
            s.subject_code,
            s.subject_name,
            r.room_code,
            p_monitor.full_name AS monitor_instructor,
            
            -- Categorize exams based on date relative to TODAY
            CASE 
                WHEN CAST(ec.start_time AS DATE) < @TODAY THEN 'COMPLETED'
                WHEN CAST(ec.start_time AS DATE) = @TODAY THEN 'TODAY'
                WHEN CAST(ec.start_time AS DATE) BETWEEN DATEADD(DAY, 1, @TODAY) AND DATEADD(DAY, 7, @TODAY) THEN 'UPCOMING'
                WHEN CAST(ec.start_time AS DATE) > DATEADD(DAY, 7, @TODAY) THEN 'FUTURE'
                ELSE 'OTHER'
            END AS exam_category,
            
            -- Check if exam is on expected dates
            CASE 
                WHEN CAST(ec.start_time AS DATE) = '2025-11-06' THEN 'EXPECTED_COMPLETED'
                WHEN CAST(ec.start_time AS DATE) = '2025-11-12' THEN 'EXPECTED_UPCOMING'  
                WHEN CAST(ec.start_time AS DATE) = '2025-11-19' THEN 'EXPECTED_FUTURE'
                ELSE 'UNEXPECTED_DATE'
            END AS date_expectation
            
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
        INNER JOIN room r ON ec.room_id = r.room_id
        LEFT JOIN instructor i ON ec.monitor_instructor_id = i.instructor_id
        LEFT JOIN person p_monitor ON i.person_id = p_monitor.person_id
        WHERE se.student_id = @StudentId
            AND c.semester_id = @SummerSemesterId
            AND se.enrollment_status = 'registered'
            AND se.is_active = 1
            AND se.is_deleted = 0
    )
    SELECT 
        'EXAM SUMMARY BY CATEGORY' AS section,
        exam_category,
        COUNT(*) AS exam_count
    FROM TestStudentExams
    GROUP BY exam_category
    ORDER BY 
        CASE exam_category 
            WHEN 'COMPLETED' THEN 1
            WHEN 'TODAY' THEN 2
            WHEN 'UPCOMING' THEN 3
            WHEN 'FUTURE' THEN 4
            ELSE 5
        END;
    
    -- Summary by expected dates
    WITH TestStudentExams AS (
        SELECT 
            ec.exam_class_id,
            ec.start_time,
            CAST(ec.start_time AS DATE) AS exam_date,
            CAST(ec.start_time AS TIME) AS exam_time,
            ec.exam_status,
            s.subject_code,
            s.subject_name,
            r.room_code,
            p_monitor.full_name AS monitor_instructor,
            
            -- Categorize exams based on date relative to TODAY
            CASE 
                WHEN CAST(ec.start_time AS DATE) < @TODAY THEN 'COMPLETED'
                WHEN CAST(ec.start_time AS DATE) = @TODAY THEN 'TODAY'
                WHEN CAST(ec.start_time AS DATE) BETWEEN DATEADD(DAY, 1, @TODAY) AND DATEADD(DAY, 7, @TODAY) THEN 'UPCOMING'
                WHEN CAST(ec.start_time AS DATE) > DATEADD(DAY, 7, @TODAY) THEN 'FUTURE'
                ELSE 'OTHER'
            END AS exam_category,
            
            -- Check if exam is on expected dates
            CASE 
                WHEN CAST(ec.start_time AS DATE) = '2025-11-06' THEN 'EXPECTED_COMPLETED'
                WHEN CAST(ec.start_time AS DATE) = '2025-11-12' THEN 'EXPECTED_UPCOMING'  
                WHEN CAST(ec.start_time AS DATE) = '2025-11-19' THEN 'EXPECTED_FUTURE'
                ELSE 'UNEXPECTED_DATE'
            END AS date_expectation
            
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
        INNER JOIN room r ON ec.room_id = r.room_id
        LEFT JOIN instructor i ON ec.monitor_instructor_id = i.instructor_id
        LEFT JOIN person p_monitor ON i.person_id = p_monitor.person_id
        WHERE se.student_id = @StudentId
            AND c.semester_id = @SummerSemesterId
            AND se.enrollment_status = 'registered'
            AND se.is_active = 1
            AND se.is_deleted = 0
    )
    SELECT 
        'EXAM SUMMARY BY EXPECTED DATES' AS section,
        date_expectation,
        COUNT(*) AS exam_count
    FROM TestStudentExams
    GROUP BY date_expectation
    ORDER BY 
        CASE date_expectation 
            WHEN 'EXPECTED_COMPLETED' THEN 1
            WHEN 'EXPECTED_UPCOMING' THEN 2
            WHEN 'EXPECTED_FUTURE' THEN 3
            ELSE 4
        END;
    
    -- Verification result
    SELECT 
        'VERIFICATION RESULT' AS section,
        CASE 
            WHEN (SELECT COUNT(*) 
                  FROM student_enrollment se
                  INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
                  INNER JOIN course c ON cc.course_id = c.course_id
                  INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
                  WHERE se.student_id = @StudentId
                      AND c.semester_id = @SummerSemesterId
                      AND se.enrollment_status = 'registered'
                      AND se.is_active = 1
                      AND se.is_deleted = 0
                      AND CAST(ec.start_time AS DATE) = '2025-11-06') = 2
                AND (SELECT COUNT(*) 
                     FROM student_enrollment se
                     INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
                     INNER JOIN course c ON cc.course_id = c.course_id
                     INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
                     WHERE se.student_id = @StudentId
                         AND c.semester_id = @SummerSemesterId
                         AND se.enrollment_status = 'registered'
                         AND se.is_active = 1
                         AND se.is_deleted = 0
                         AND CAST(ec.start_time AS DATE) = '2025-11-12') = 2
                AND (SELECT COUNT(*) 
                     FROM student_enrollment se
                     INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
                     INNER JOIN course c ON cc.course_id = c.course_id
                     INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
                     WHERE se.student_id = @StudentId
                         AND c.semester_id = @SummerSemesterId
                         AND se.enrollment_status = 'registered'
                         AND se.is_active = 1
                         AND se.is_deleted = 0
                         AND CAST(ec.start_time AS DATE) = '2025-11-19') = 2
            THEN '✓ PASS - Test student has exactly 2 exams on each expected date'
            ELSE '✗ FAIL - Exam distribution does not match expected pattern'
        END AS verification_status,
        
        (SELECT COUNT(*) 
         FROM student_enrollment se
         INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
         INNER JOIN course c ON cc.course_id = c.course_id
         INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
         WHERE se.student_id = @StudentId
             AND c.semester_id = @SummerSemesterId
             AND se.enrollment_status = 'registered'
             AND se.is_active = 1
             AND se.is_deleted = 0
             AND CAST(ec.start_time AS DATE) = '2025-11-06') AS exams_on_11_06,
             
        (SELECT COUNT(*) 
         FROM student_enrollment se
         INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
         INNER JOIN course c ON cc.course_id = c.course_id
         INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
         WHERE se.student_id = @StudentId
             AND c.semester_id = @SummerSemesterId
             AND se.enrollment_status = 'registered'
             AND se.is_active = 1
             AND se.is_deleted = 0
             AND CAST(ec.start_time AS DATE) = '2025-11-12') AS exams_on_11_12,
             
        (SELECT COUNT(*) 
         FROM student_enrollment se
         INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
         INNER JOIN course c ON cc.course_id = c.course_id
         INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
         WHERE se.student_id = @StudentId
             AND c.semester_id = @SummerSemesterId
             AND se.enrollment_status = 'registered'
             AND se.is_active = 1
             AND se.is_deleted = 0
             AND CAST(ec.start_time AS DATE) = '2025-11-19') AS exams_on_11_19,
             
        (SELECT COUNT(*) 
         FROM student_enrollment se
         INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
         INNER JOIN course c ON cc.course_id = c.course_id
         INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
         WHERE se.student_id = @StudentId
             AND c.semester_id = @SummerSemesterId
             AND se.enrollment_status = 'registered'
             AND se.is_active = 1
             AND se.is_deleted = 0
             AND CAST(ec.start_time AS DATE) NOT IN ('2025-11-06', '2025-11-12', '2025-11-19')) AS exams_on_other_dates,
             
        (SELECT COUNT(*) 
         FROM student_enrollment se
         INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
         INNER JOIN course c ON cc.course_id = c.course_id
         INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
         WHERE se.student_id = @StudentId
             AND c.semester_id = @SummerSemesterId
             AND se.enrollment_status = 'registered'
             AND se.is_active = 1
             AND se.is_deleted = 0) AS total_exams;
    
    -- Status verification (based on current date)
    WITH TestStudentExams AS (
        SELECT 
            ec.exam_class_id,
            ec.start_time,
            CAST(ec.start_time AS DATE) AS exam_date,
            CAST(ec.start_time AS TIME) AS exam_time,
            ec.exam_status,
            s.subject_code,
            s.subject_name,
            r.room_code,
            p_monitor.full_name AS monitor_instructor,
            
            -- Categorize exams based on date relative to TODAY
            CASE 
                WHEN CAST(ec.start_time AS DATE) < @TODAY THEN 'COMPLETED'
                WHEN CAST(ec.start_time AS DATE) = @TODAY THEN 'TODAY'
                WHEN CAST(ec.start_time AS DATE) BETWEEN DATEADD(DAY, 1, @TODAY) AND DATEADD(DAY, 7, @TODAY) THEN 'UPCOMING'
                WHEN CAST(ec.start_time AS DATE) > DATEADD(DAY, 7, @TODAY) THEN 'FUTURE'
                ELSE 'OTHER'
            END AS exam_category,
            
            -- Check if exam is on expected dates
            CASE 
                WHEN CAST(ec.start_time AS DATE) = '2025-11-06' THEN 'EXPECTED_COMPLETED'
                WHEN CAST(ec.start_time AS DATE) = '2025-11-12' THEN 'EXPECTED_UPCOMING'  
                WHEN CAST(ec.start_time AS DATE) = '2025-11-19' THEN 'EXPECTED_FUTURE'
                ELSE 'UNEXPECTED_DATE'
            END AS date_expectation
            
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
        INNER JOIN room r ON ec.room_id = r.room_id
        LEFT JOIN instructor i ON ec.monitor_instructor_id = i.instructor_id
        LEFT JOIN person p_monitor ON i.person_id = p_monitor.person_id
        WHERE se.student_id = @StudentId
            AND c.semester_id = @SummerSemesterId
            AND se.enrollment_status = 'registered'
            AND se.is_active = 1
            AND se.is_deleted = 0
    )
    SELECT 
        'STATUS VERIFICATION' AS section,
        CASE 
            WHEN @TODAY < '2025-11-06' THEN 'All exams should be SCHEDULED (before 11/6)'
            WHEN @TODAY = '2025-11-06' THEN '11/6 exams should be SCHEDULED, others SCHEDULED'
            WHEN @TODAY > '2025-11-06' AND @TODAY < '2025-11-12' THEN '11/6 exams should be COMPLETED, others SCHEDULED'
            WHEN @TODAY = '2025-11-12' THEN '11/6 COMPLETED, 11/12 SCHEDULED, 11/19 SCHEDULED'
            WHEN @TODAY > '2025-11-12' AND @TODAY < '2025-11-19' THEN '11/6 COMPLETED, 11/12 COMPLETED, 11/19 SCHEDULED'
            WHEN @TODAY = '2025-11-19' THEN '11/6 COMPLETED, 11/12 COMPLETED, 11/19 SCHEDULED'
            WHEN @TODAY > '2025-11-19' THEN '11/6 COMPLETED, 11/12 COMPLETED, 11/19 COMPLETED'
            ELSE 'Unknown date scenario'
        END AS expected_status_pattern,
        
        (SELECT COUNT(*) FROM TestStudentExams WHERE exam_category = 'COMPLETED') AS actual_completed_count,
        (SELECT COUNT(*) FROM TestStudentExams WHERE exam_category = 'UPCOMING') AS actual_upcoming_count,
        (SELECT COUNT(*) FROM TestStudentExams WHERE exam_category = 'FUTURE') AS actual_future_count,
        (SELECT COUNT(*) FROM TestStudentExams WHERE exam_status = 'completed') AS db_completed_status_count,
        (SELECT COUNT(*) FROM TestStudentExams WHERE exam_status = 'scheduled') AS db_scheduled_status_count;

END
ELSE
BEGIN
    SELECT 
        'ERROR' AS section,
        CASE 
            WHEN @StudentId IS NULL THEN 'Test student not found with email: ' + @TestStudentEmail
            WHEN @SummerSemesterId IS NULL THEN 'Summer 2024-2025 semester not found'
            ELSE 'Unknown error'
        END AS error_message;
END

-- Additional check: Look for any exam conflicts for test student
IF @StudentId IS NOT NULL
BEGIN
    SELECT 
        'CONFLICT CHECK' AS section,
        e1.exam_date AS date1,
        e1.exam_time AS time1,
        e1.subject_code AS subject1,
        e1.room_code AS room1,
        e2.exam_date AS date2,
        e2.exam_time AS time2,
        e2.subject_code AS subject2,
        e2.room_code AS room2,
        'SAME DATE AND OVERLAPPING TIME' AS conflict_type
    FROM (
        SELECT 
            ec.exam_class_id,
            CAST(ec.start_time AS DATE) AS exam_date,
            CAST(ec.start_time AS TIME) AS exam_time,
            ec.start_time,
            DATEADD(MINUTE, ec.duration_minutes, ec.start_time) AS end_time,
            s.subject_code,
            r.room_code
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
        INNER JOIN room r ON ec.room_id = r.room_id
        WHERE se.student_id = @StudentId
            AND se.enrollment_status = 'registered'
            AND se.is_active = 1
    ) e1
    INNER JOIN (
        SELECT 
            ec.exam_class_id,
            CAST(ec.start_time AS DATE) AS exam_date,
            CAST(ec.start_time AS TIME) AS exam_time,
            ec.start_time,
            DATEADD(MINUTE, ec.duration_minutes, ec.start_time) AS end_time,
            s.subject_code,
            r.room_code
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        INNER JOIN exam_class ec ON cc.course_class_id = ec.course_class_id
        INNER JOIN room r ON ec.room_id = r.room_id
        WHERE se.student_id = @StudentId
            AND se.enrollment_status = 'registered'
            AND se.is_active = 1
    ) e2 ON 
        e1.exam_class_id < e2.exam_class_id  -- Avoid duplicates
        AND e1.exam_date = e2.exam_date      -- Same date
        AND e1.start_time < e2.end_time      -- Time overlap check
        AND e1.end_time > e2.start_time;     -- Time overlap check
    
    -- If no conflicts found
    IF @@ROWCOUNT = 0
    BEGIN
        SELECT 
            'CONFLICT CHECK' AS section,
            '✓ No exam conflicts found for test student' AS result;
    END
END