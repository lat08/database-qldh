-- ============================================================
-- GET SUMMER 2025 GRADES FOR STUDENT: student.test@edu.vn
-- ============================================================
-- This query retrieves all summer 2025 semester grades (draft and official)
-- for the specific student with email student.test@edu.vn

USE EduManagement;
GO

DECLARE @TODAY DATE = CAST(GETDATE() AS DATE);
DECLARE @StudentEmail NVARCHAR(255) = 'student.test@edu.vn';

-- Find summer 2025 semester
DECLARE @SummerSemesterId UNIQUEIDENTIFIER;
SELECT @SummerSemesterId = s.semester_id
FROM semester s
INNER JOIN academic_year ay ON s.academic_year_id = ay.academic_year_id
WHERE s.semester_type = 'summer'
    AND ay.year_name = '2024-2025'
    AND YEAR(s.end_date) = 2025;

-- Find student by email
DECLARE @StudentId UNIQUEIDENTIFIER;
SELECT @StudentId = st.student_id
FROM student st
INNER JOIN person p ON st.person_id = p.person_id
WHERE p.email = @StudentEmail;

-- Display student and semester info
SELECT 
    'STUDENT & SEMESTER INFO' AS section,
    p.full_name AS student_name,
    p.email AS student_email,
    st.student_code,
    s.semester_name,
    s.start_date AS semester_start,
    s.end_date AS semester_end,
    s.semester_status
FROM student st
INNER JOIN person p ON st.person_id = p.person_id
CROSS JOIN semester s
WHERE st.student_id = @StudentId
    AND s.semester_id = @SummerSemesterId;

-- ============================================================
-- ENROLLED COURSES FOR SUMMER 2025
-- ============================================================
SELECT 
    'ENROLLED COURSES' AS section,
    subj.subject_code,
    subj.subject_name,
    subj.credits,
    se.enrollment_status,
    se.enrollment_date,
    cc.course_class_status,
    cc.grade_submission_status
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN subject subj ON c.subject_id = subj.subject_id
WHERE se.student_id = @StudentId
    AND c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
ORDER BY subj.subject_code;

-- ============================================================
-- DRAFT GRADES
-- ============================================================
SELECT 
    'DRAFT GRADES' AS section,
    subj.subject_code,
    subj.subject_name,
    subj.credits,
    edg.attendance_grade_draft,
    edg.midterm_grade_draft,
    edg.final_grade_draft,
    -- Calculate overall draft grade if all components exist
    CASE 
        WHEN edg.attendance_grade_draft IS NOT NULL 
            AND edg.midterm_grade_draft IS NOT NULL 
            AND edg.final_grade_draft IS NOT NULL
        THEN ROUND(
            (edg.attendance_grade_draft * 0.1) + 
            (edg.midterm_grade_draft * 0.3) + 
            (edg.final_grade_draft * 0.6), 2)
        ELSE NULL
    END AS overall_grade_draft,
    edg.grade_note,
    edg.updated_at AS last_updated
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN subject subj ON c.subject_id = subj.subject_id
LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
WHERE se.student_id = @StudentId
    AND c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
ORDER BY subj.subject_code;

-- ============================================================
-- OFFICIAL GRADES (ALL VERSIONS)
-- ============================================================
SELECT 
    'OFFICIAL GRADES - ALL VERSIONS' AS section,
    subj.subject_code,
    subj.subject_name,
    subj.credits,
    egv.version_number,
    egv.version_status,
    egd.attendance_grade,
    egd.midterm_grade,
    egd.final_grade,
    -- Calculate overall official grade if all components exist
    CASE 
        WHEN egd.attendance_grade IS NOT NULL 
            AND egd.midterm_grade IS NOT NULL 
            AND egd.final_grade IS NOT NULL
        THEN ROUND(
            (egd.attendance_grade * 0.1) + 
            (egd.midterm_grade * 0.3) + 
            (egd.final_grade * 0.6), 2)
        ELSE NULL
    END AS overall_grade_official,
    egd.grade_note,
    egv.submitted_at,
    egv.approved_at,
    inst.full_name AS submitted_by_instructor,
    adm.full_name AS approved_by_admin
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN subject subj ON c.subject_id = subj.subject_id
LEFT JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
LEFT JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
    AND se.enrollment_id = egd.enrollment_id
LEFT JOIN instructor ins ON egv.submitted_by = ins.instructor_id
LEFT JOIN person inst ON ins.person_id = inst.person_id
LEFT JOIN admin a ON egv.approved_by = a.admin_id
LEFT JOIN person adm ON a.person_id = adm.person_id
WHERE se.student_id = @StudentId
    AND c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
ORDER BY subj.subject_code, egv.version_number;

-- ============================================================
-- LATEST APPROVED GRADES ONLY
-- ============================================================
SELECT 
    'LATEST APPROVED GRADES' AS section,
    subj.subject_code,
    subj.subject_name,
    subj.credits,
    egv.version_number,
    egd.attendance_grade,
    egd.midterm_grade,
    egd.final_grade,
    -- Calculate overall official grade
    CASE 
        WHEN egd.attendance_grade IS NOT NULL 
            AND egd.midterm_grade IS NOT NULL 
            AND egd.final_grade IS NOT NULL
        THEN ROUND(
            (egd.attendance_grade * 0.1) + 
            (egd.midterm_grade * 0.3) + 
            (egd.final_grade * 0.6), 2)
        ELSE NULL
    END AS overall_grade,
    egd.grade_note,
    egv.approved_at,
    adm.full_name AS approved_by
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
INNER JOIN subject subj ON c.subject_id = subj.subject_id
INNER JOIN enrollment_grade_version egv ON cc.course_class_id = egv.course_class_id
    AND egv.version_status = 'approved'
INNER JOIN enrollment_grade_detail egd ON egv.grade_version_id = egd.grade_version_id 
    AND se.enrollment_id = egd.enrollment_id
LEFT JOIN admin a ON egv.approved_by = a.admin_id
LEFT JOIN person adm ON a.person_id = adm.person_id
WHERE se.student_id = @StudentId
    AND c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed')
    AND egv.version_number = (
        SELECT MAX(egv2.version_number)
        FROM enrollment_grade_version egv2
        WHERE egv2.course_class_id = cc.course_class_id
            AND egv2.version_status = 'approved'
    )
ORDER BY subj.subject_code;

-- ============================================================
-- GRADE SUMMARY
-- ============================================================
SELECT 
    'GRADE SUMMARY' AS section,
    COUNT(*) AS total_courses_enrolled,
    COUNT(CASE 
        WHEN edg.attendance_grade_draft IS NOT NULL 
            AND edg.midterm_grade_draft IS NOT NULL 
        THEN 1 
    END) AS courses_with_draft_grades,
    COUNT(CASE 
        WHEN egd.attendance_grade IS NOT NULL 
            AND egd.midterm_grade IS NOT NULL 
        THEN 1 
    END) AS courses_with_official_grades,
    COUNT(CASE 
        WHEN (edg.attendance_grade_draft IS NULL OR edg.midterm_grade_draft IS NULL)
            AND (egd.attendance_grade IS NULL OR egd.midterm_grade IS NULL)
        THEN 1 
    END) AS courses_without_grades,
    -- Average grades (from approved versions only)
    ROUND(AVG(egd.attendance_grade), 2) AS avg_attendance_grade,
    ROUND(AVG(egd.midterm_grade), 2) AS avg_midterm_grade,
    ROUND(AVG(egd.final_grade), 2) AS avg_final_grade,
    -- Calculate GPA from approved grades
    ROUND(AVG(
        CASE 
            WHEN egd.attendance_grade IS NOT NULL 
                AND egd.midterm_grade IS NOT NULL 
                AND egd.final_grade IS NOT NULL
            THEN (egd.attendance_grade * 0.1) + 
                 (egd.midterm_grade * 0.3) + 
                 (egd.final_grade * 0.6)
            ELSE NULL
        END
    ), 2) AS semester_gpa
FROM student_enrollment se
INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
INNER JOIN course c ON cc.course_id = c.course_id
LEFT JOIN enrollment_draft_grade edg ON se.enrollment_id = edg.enrollment_id
LEFT JOIN (
    -- Get latest approved grades only
    SELECT egd.*, egv.course_class_id
    FROM enrollment_grade_detail egd
    INNER JOIN enrollment_grade_version egv ON egd.grade_version_id = egv.grade_version_id
    WHERE egv.version_status = 'approved'
        AND egv.version_number = (
            SELECT MAX(egv2.version_number)
            FROM enrollment_grade_version egv2
            WHERE egv2.course_class_id = egv.course_class_id
                AND egv2.version_status = 'approved'
        )
) egd ON cc.course_class_id = egd.course_class_id 
    AND se.enrollment_id = egd.enrollment_id
WHERE se.student_id = @StudentId
    AND c.semester_id = @SummerSemesterId
    AND se.is_deleted = 0
    AND se.is_active = 1
    AND se.enrollment_status IN ('registered', 'completed');