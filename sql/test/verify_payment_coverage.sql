-- ============================================================
-- VERIFY PAYMENT COVERAGE
-- ============================================================
-- This query verifies that all enrollments except Fall 2025 have payments
-- Expected: 100% payment rate for all semesters except Fall 2025 (upcoming)

USE EduManagement;
GO

PRINT '============================================================';
PRINT 'VERIFYING PAYMENT COVERAGE BY SEMESTER';
PRINT '============================================================';

-- Identify Fall 2025 semester
DECLARE @Fall2025SemesterId UNIQUEIDENTIFIER;
SELECT @Fall2025SemesterId = s.semester_id
FROM semester s
INNER JOIN academic_year ay ON s.academic_year_id = ay.academic_year_id
WHERE s.semester_type = 'fall' 
    AND ay.year_name = '2025-2026';  -- Fall 2025 is in academic year 2025-2026

PRINT '';
PRINT '1. ENROLLMENT AND PAYMENT SUMMARY BY SEMESTER';
PRINT '   --------------------------------------------------------';

-- Get payment coverage by semester
SELECT 
    s.semester_name,
    s.semester_type,
    ay.year_name AS academic_year,
    s.start_date,
    s.end_date,
    COUNT(se.enrollment_id) AS total_enrollments,
    COUNT(DISTINCT pe.payment_id) AS total_payments,
    COUNT(DISTINCT ped.enrollment_id) AS paid_enrollments,
    CASE 
        WHEN COUNT(se.enrollment_id) = 0 THEN 0
        ELSE (COUNT(DISTINCT ped.enrollment_id) * 100.0) / COUNT(se.enrollment_id)
    END AS payment_percentage,
    CASE 
        WHEN s.semester_id = @Fall2025SemesterId THEN 'UPCOMING (Should be 0%)'
        ELSE 'PAST/CURRENT (Should be 100%)'
    END AS expected_status
FROM semester s
INNER JOIN academic_year ay ON s.academic_year_id = ay.academic_year_id
LEFT JOIN course c ON s.semester_id = c.semester_id
LEFT JOIN course_class cc ON c.course_id = cc.course_id
LEFT JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
LEFT JOIN payment_enrollment pe ON s.semester_id = pe.semester_id AND se.student_id = pe.student_id
LEFT JOIN payment_enrollment_detail ped ON pe.payment_id = ped.payment_id AND se.enrollment_id = ped.enrollment_id
WHERE se.enrollment_id IS NOT NULL  -- Only include semesters with enrollments
GROUP BY s.semester_id, s.semester_name, s.semester_type, ay.year_name, s.start_date, s.end_date
ORDER BY s.start_date;

PRINT '';
PRINT '2. FALL 2025 VERIFICATION (Should have NO payments)';
PRINT '   --------------------------------------------------------';

SELECT 
    'Fall 2025 Enrollments' AS category,
    COUNT(se.enrollment_id) AS total_enrollments,
    COUNT(DISTINCT ped.enrollment_id) AS paid_enrollments,
    CASE 
        WHEN COUNT(DISTINCT ped.enrollment_id) = 0 THEN 'CORRECT (No payments)'
        ELSE 'ERROR (Has payments!)'
    END AS status
FROM semester s
INNER JOIN course c ON s.semester_id = c.semester_id
INNER JOIN course_class cc ON c.course_id = cc.course_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
LEFT JOIN payment_enrollment pe ON s.semester_id = pe.semester_id AND se.student_id = pe.student_id
LEFT JOIN payment_enrollment_detail ped ON pe.payment_id = ped.payment_id AND se.enrollment_id = ped.enrollment_id
WHERE s.semester_id = @Fall2025SemesterId;

PRINT '';
PRINT '3. NON-FALL 2025 VERIFICATION (Should have ALL payments)';
PRINT '   --------------------------------------------------------';

SELECT 
    'Non-Fall 2025 Enrollments' AS category,
    COUNT(se.enrollment_id) AS total_enrollments,
    COUNT(DISTINCT ped.enrollment_id) AS paid_enrollments,
    CASE 
        WHEN COUNT(se.enrollment_id) > 0 AND COUNT(se.enrollment_id) = COUNT(DISTINCT ped.enrollment_id) THEN 'CORRECT (100% paid)'
        WHEN COUNT(se.enrollment_id) > 0 THEN 'ERROR (Not 100% paid)'
        ELSE 'NO DATA'
    END AS status,
    CASE 
        WHEN COUNT(se.enrollment_id) = 0 THEN 0
        ELSE (COUNT(DISTINCT ped.enrollment_id) * 100.0) / COUNT(se.enrollment_id)
    END AS payment_percentage
FROM semester s
INNER JOIN course c ON s.semester_id = c.semester_id
INNER JOIN course_class cc ON c.course_id = cc.course_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
LEFT JOIN payment_enrollment pe ON s.semester_id = pe.semester_id AND se.student_id = pe.student_id
LEFT JOIN payment_enrollment_detail ped ON pe.payment_id = ped.payment_id AND se.enrollment_id = ped.enrollment_id
WHERE s.semester_id != @Fall2025SemesterId;

PRINT '';
PRINT '4. DETAILED UNPAID ENROLLMENTS (Should only be Fall 2025)';
PRINT '   --------------------------------------------------------';

SELECT 
    s.semester_name,
    s.semester_type,
    ay.year_name AS academic_year,
    p.full_name AS student_name,
    p.email AS student_email,
    sub.subject_code,
    sub.subject_name,
    se.enrollment_status,
    CASE 
        WHEN s.semester_id = @Fall2025SemesterId THEN 'EXPECTED (Fall 2025)'
        ELSE 'ERROR (Should be paid!)'
    END AS unpaid_status
FROM semester s
INNER JOIN academic_year ay ON s.academic_year_id = ay.academic_year_id
INNER JOIN course c ON s.semester_id = c.semester_id
INNER JOIN course_class cc ON c.course_id = cc.course_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
INNER JOIN student st ON se.student_id = st.student_id
INNER JOIN person p ON st.person_id = p.person_id
INNER JOIN subject sub ON c.subject_id = sub.subject_id
LEFT JOIN payment_enrollment pe ON s.semester_id = pe.semester_id AND se.student_id = pe.student_id
LEFT JOIN payment_enrollment_detail ped ON pe.payment_id = ped.payment_id AND se.enrollment_id = ped.enrollment_id
WHERE ped.enrollment_id IS NULL  -- Unpaid enrollments
ORDER BY s.start_date, p.email, sub.subject_code;

PRINT '';
PRINT '5. OVERALL SUMMARY';
PRINT '   --------------------------------------------------------';

-- Count total enrollments and payments
DECLARE @TotalEnrollments INT;
DECLARE @PaidEnrollments INT;
DECLARE @Fall2025Enrollments INT;
DECLARE @NonFall2025Enrollments INT;

SELECT @TotalEnrollments = COUNT(*)
FROM student_enrollment;

SELECT @PaidEnrollments = COUNT(DISTINCT ped.enrollment_id)
FROM payment_enrollment_detail ped;

SELECT @Fall2025Enrollments = COUNT(se.enrollment_id)
FROM semester s
INNER JOIN course c ON s.semester_id = c.semester_id
INNER JOIN course_class cc ON c.course_id = cc.course_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
WHERE s.semester_id = @Fall2025SemesterId;

SELECT @NonFall2025Enrollments = COUNT(se.enrollment_id)
FROM semester s
INNER JOIN course c ON s.semester_id = c.semester_id
INNER JOIN course_class cc ON c.course_id = cc.course_id
INNER JOIN student_enrollment se ON cc.course_class_id = se.course_class_id
WHERE s.semester_id != @Fall2025SemesterId;

SELECT 
    @TotalEnrollments AS total_enrollments,
    @PaidEnrollments AS paid_enrollments,
    @Fall2025Enrollments AS fall_2025_enrollments,
    @NonFall2025Enrollments AS non_fall_2025_enrollments,
    (@PaidEnrollments * 100.0) / @TotalEnrollments AS overall_payment_percentage,
    CASE 
        WHEN @PaidEnrollments = @NonFall2025Enrollments THEN 'CORRECT (All non-Fall 2025 paid)'
        ELSE 'ERROR (Payment mismatch)'
    END AS payment_policy_status;

PRINT '';
PRINT 'Expected Results:';
PRINT '- Fall 2025 enrollments: 0% paid (upcoming semester)';
PRINT '- All other enrollments: 100% paid (past/current semesters)';
PRINT '- Overall payment rate: depends on Fall 2025 vs other enrollments ratio';

GO