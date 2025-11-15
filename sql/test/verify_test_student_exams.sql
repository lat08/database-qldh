-- ============================================================
-- VERIFICATION QUERY: Test Student Exam Distribution
-- ============================================================
-- This query verifies that the test student has for SUMMER 2024-2025:
-- - 2 exams that have passed (completed status, date < TODAY)
-- - 2 upcoming exams (scheduled status, date within 7 days)
-- - 2 exams in the relative far future (scheduled status, date > 7 days)
-- ============================================================

USE EduManagement;
GO

-- Test Student ID
DECLARE @TestStudentID UNIQUEIDENTIFIER = '00000000-0000-0000-0000-000000000003';
DECLARE @Today DATE = CAST(GETDATE() AS DATE);
-- Summer 2024-2025: semester_type is 'summer' and end_date is in November 2025
-- This uniquely identifies summer 2024-2025 (which ends on 11/20/2025)

-- ============================================================
-- SUMMARY: Count exams by category (SUMMER 2024-2025 ONLY)
-- ============================================================
SELECT 
    ExamCategory,
    COUNT(*) AS ExamCount,
    STRING_AGG(CAST(ExamDate AS NVARCHAR(10)), ', ') AS ExamDates
FROM (
    SELECT 
        CASE 
            WHEN CAST(ec.start_time AS DATE) < @Today AND ec.exam_status = 'completed' THEN 'Past (Completed)'
            WHEN CAST(ec.start_time AS DATE) >= @Today 
                 AND CAST(ec.start_time AS DATE) <= DATEADD(DAY, 7, @Today) 
                 AND ec.exam_status = 'scheduled' THEN 'Upcoming (Within 7 days)'
            WHEN CAST(ec.start_time AS DATE) > DATEADD(DAY, 7, @Today) 
                 AND ec.exam_status = 'scheduled' THEN 'Future (More than 7 days)'
            ELSE 'Other'
        END AS ExamCategory,
        CAST(ec.start_time AS DATE) AS ExamDate
    FROM exam_class ec
    INNER JOIN course_class cc ON ec.course_class_id = cc.course_class_id
    INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
    INNER JOIN course c ON cc.course_id = c.course_id
    INNER JOIN semester sem ON c.semester_id = sem.semester_id
    WHERE se.student_id = @TestStudentID
        AND sem.semester_type = 'summer'
        AND YEAR(sem.end_date) = 2025
        AND MONTH(sem.end_date) = 11
        AND ec.is_deleted = 0
        AND se.is_deleted = 0
        AND cc.is_deleted = 0
        AND sem.is_deleted = 0
) AS ExamCategories
GROUP BY ExamCategory
ORDER BY 
    CASE ExamCategory
        WHEN 'Past (Completed)' THEN 1
        WHEN 'Upcoming (Within 7 days)' THEN 2
        WHEN 'Future (More than 7 days)' THEN 3
        ELSE 4
    END;

-- ============================================================
-- DETAILED VIEW: All exams for test student (SUMMER 2024-2025 ONLY)
-- ============================================================
SELECT 
    s.student_code,
    p.full_name AS StudentName,
    sub.subject_code,
    sub.subject_name,
    CAST(ec.start_time AS DATE) AS ExamDate,
    CAST(ec.start_time AS TIME) AS ExamTime,
    ec.duration_minutes,
    ec.exam_status,
    CASE 
        WHEN CAST(ec.start_time AS DATE) < @Today AND ec.exam_status = 'completed' THEN 'Past (Completed)'
        WHEN CAST(ec.start_time AS DATE) >= @Today 
             AND CAST(ec.start_time AS DATE) <= DATEADD(DAY, 7, @Today) 
             AND ec.exam_status = 'scheduled' THEN 'Upcoming (Within 7 days)'
        WHEN CAST(ec.start_time AS DATE) > DATEADD(DAY, 7, @Today) 
             AND ec.exam_status = 'scheduled' THEN 'Future (More than 7 days)'
        ELSE 'Other'
    END AS TimeCategory,
    DATEDIFF(DAY, @Today, CAST(ec.start_time AS DATE)) AS DaysFromToday,
    r.room_code,
    r.room_name,
    sem.semester_name,
    sem.semester_type,
    YEAR(sem.start_date) AS start_year
FROM exam_class ec
INNER JOIN course_class cc ON ec.course_class_id = cc.course_class_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
INNER JOIN student s ON se.student_id = s.student_id
INNER JOIN person p ON s.person_id = p.person_id
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN subject sub ON c.subject_id = sub.subject_id
INNER JOIN semester sem ON c.semester_id = sem.semester_id
INNER JOIN room r ON ec.room_id = r.room_id
WHERE s.student_id = @TestStudentID
    AND sem.semester_type = 'summer'
    AND YEAR(sem.end_date) = 2025
    AND MONTH(sem.end_date) = 11
    AND ec.is_deleted = 0
    AND se.is_deleted = 0
    AND cc.is_deleted = 0
    AND sem.is_deleted = 0
ORDER BY ec.start_time;

-- ============================================================
-- SPECIFIC VERIFICATION: Check for exact dates (11/6, 11/12, 11/19)
-- SUMMER 2024-2025 ONLY
-- ============================================================
SELECT 
    CAST(ec.start_time AS DATE) AS ExamDate,
    COUNT(*) AS ExamCount,
    STRING_AGG(sub.subject_code, ', ') AS Subjects,
    STRING_AGG(ec.exam_status, ', ') AS Statuses
FROM exam_class ec
INNER JOIN course_class cc ON ec.course_class_id = cc.course_class_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN subject sub ON c.subject_id = sub.subject_id
INNER JOIN semester sem ON c.semester_id = sem.semester_id
WHERE se.student_id = @TestStudentID
    AND sem.semester_type = 'summer'
    AND YEAR(sem.end_date) = 2025
    AND MONTH(sem.end_date) = 11
    AND ec.is_deleted = 0
    AND se.is_deleted = 0
    AND cc.is_deleted = 0
    AND sem.is_deleted = 0
    AND (
        -- Check for November 6th (any year)
        (MONTH(ec.start_time) = 11 AND DAY(ec.start_time) = 6)
        OR
        -- Check for November 12th (any year)
        (MONTH(ec.start_time) = 11 AND DAY(ec.start_time) = 12)
        OR
        -- Check for November 19th (any year)
        (MONTH(ec.start_time) = 11 AND DAY(ec.start_time) = 19)
    )
GROUP BY CAST(ec.start_time AS DATE)
ORDER BY CAST(ec.start_time AS DATE);

-- ============================================================
-- EXPECTED RESULT VERIFICATION (SUMMER 2024-2025 ONLY)
-- ============================================================
-- Expected results:
-- 1. Past (Completed): 2 exams (on 11/6 if TODAY > 11/6)
-- 2. Upcoming (Within 7 days): 2 exams (on 11/12 if TODAY is around 11/10)
-- 3. Future (More than 7 days): 2 exams (on 11/19 if TODAY is around 11/10)
-- ============================================================
SELECT 
    'VERIFICATION SUMMARY (Summer 2024-2025)' AS SummaryType,
    COUNT(CASE WHEN CAST(ec.start_time AS DATE) < @Today AND ec.exam_status = 'completed' THEN 1 END) AS PastCompletedExams,
    COUNT(CASE WHEN CAST(ec.start_time AS DATE) >= @Today 
               AND CAST(ec.start_time AS DATE) <= DATEADD(DAY, 7, @Today) 
               AND ec.exam_status = 'scheduled' THEN 1 END) AS UpcomingExams,
    COUNT(CASE WHEN CAST(ec.start_time AS DATE) > DATEADD(DAY, 7, @Today) 
               AND ec.exam_status = 'scheduled' THEN 1 END) AS FutureExams,
    COUNT(*) AS TotalExams,
    CASE 
        WHEN COUNT(CASE WHEN CAST(ec.start_time AS DATE) < @Today AND ec.exam_status = 'completed' THEN 1 END) = 2
         AND COUNT(CASE WHEN CAST(ec.start_time AS DATE) >= @Today 
                        AND CAST(ec.start_time AS DATE) <= DATEADD(DAY, 7, @Today) 
                        AND ec.exam_status = 'scheduled' THEN 1 END) = 2
         AND COUNT(CASE WHEN CAST(ec.start_time AS DATE) > DATEADD(DAY, 7, @Today) 
                        AND ec.exam_status = 'scheduled' THEN 1 END) = 2
        THEN 'PASS: Test student has correct exam distribution (2 past, 2 upcoming, 2 future)'
        ELSE 'FAIL: Test student exam distribution does not match expected (2 past, 2 upcoming, 2 future)'
    END AS VerificationResult
FROM exam_class ec
INNER JOIN course_class cc ON ec.course_class_id = cc.course_class_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN semester sem ON c.semester_id = sem.semester_id
WHERE se.student_id = @TestStudentID
        AND sem.semester_type = 'summer'
        AND YEAR(sem.end_date) = 2025
        AND MONTH(sem.end_date) = 11
        AND ec.is_deleted = 0
        AND se.is_deleted = 0
        AND cc.is_deleted = 0
        AND sem.is_deleted = 0;

GO

