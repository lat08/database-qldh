SET NOCOUNT ON;
DECLARE @test_student_id UNIQUEIDENTIFIER = '00000000-0000-0000-0000-000000000003';

-- =================================================================
-- QUERY 1: ALL COURSES OPEN FOR REGISTRATION (FALL 2025-2026)
-- =================================================================
SELECT 
    'OPEN_FOR_REGISTRATION' AS tag,
    cc.course_class_id,
    s.subject_id,
    s.subject_code,
    s.subject_name,
    sem.semester_name,
    cc.max_students,
    cc.day_of_week,
    cc.start_period,
    cc.end_period
FROM course_class cc
JOIN course c ON cc.course_id = c.course_id
JOIN subject s ON c.subject_id = s.subject_id
JOIN semester sem ON c.semester_id = sem.semester_id
WHERE cc.course_class_status = 'active'
  AND YEAR(sem.start_date) = 2025 
  AND sem.semester_type = 'fall'
ORDER BY s.subject_code;

-- =================================================================
-- QUERY 2: ALL SUBJECTS STUDENT HAS ENROLLED IN
-- =================================================================
SELECT 
    'STUDENT_ENROLLED' AS tag,
    s.subject_id,
    s.subject_code,
    s.subject_name,
    COUNT(*) AS times_enrolled
FROM student_enrollment se
JOIN course_class cc ON se.course_class_id = cc.course_class_id
JOIN course c ON cc.course_id = c.course_id
JOIN subject s ON c.subject_id = s.subject_id
WHERE se.student_id = @test_student_id
GROUP BY s.subject_id, s.subject_code, s.subject_name
ORDER BY s.subject_code;

-- =================================================================
-- QUERY 3: QUERY 1 MINUS QUERY 2 (AVAILABLE COURSES - NOT ENROLLED)
-- =================================================================
SELECT 
    'AVAILABLE_TO_REGISTER' AS tag,
    cc.course_class_id,
    s.subject_id,
    s.subject_code,
    s.subject_name,
    sem.semester_name,
    cc.max_students,
    cc.day_of_week,
    cc.start_period,
    cc.end_period
FROM course_class cc
JOIN course c ON cc.course_id = c.course_id
JOIN subject s ON c.subject_id = s.subject_id
JOIN semester sem ON c.semester_id = sem.semester_id
WHERE cc.course_class_status = 'active'
  AND YEAR(sem.start_date) = 2025 
  AND sem.semester_type = 'fall'
  -- MINUS: Subject NOT in enrolled list (using NOT EXISTS to avoid NULL issues)
  AND NOT EXISTS (
      SELECT 1
      FROM student_enrollment se
      JOIN course_class cc2 ON se.course_class_id = cc2.course_class_id
      JOIN course c2 ON cc2.course_id = c2.course_id
      WHERE c2.subject_id = s.subject_id
        AND se.student_id = @test_student_id
        AND se.enrollment_status IN ('enrolled', 'completed', 'passed')
  )
ORDER BY s.subject_code;

-- =================================================================
-- QUERY 4: COURSES IN STUDENT'S CURRICULUM (AVAILABLE FOR REGISTRATION)
-- =================================================================
SELECT 
    'IN_CURRICULUM_AVAILABLE' AS tag,
    cc.course_class_id,
    s.subject_id,
    s.subject_code,
    s.subject_name,
    sem.semester_name,
    cc.max_students,
    cc.day_of_week,
    cc.start_period,
    cc.end_period,
    cd.academic_year_index,
    cd.semester_index
FROM course_class cc
JOIN course c ON cc.course_id = c.course_id
JOIN subject s ON c.subject_id = s.subject_id
JOIN semester sem ON c.semester_id = sem.semester_id
-- Join to student's curriculum through their class
JOIN student st ON st.student_id = @test_student_id
JOIN class cl ON cl.class_id = st.class_id
JOIN curriculum cur ON cur.curriculum_id = cl.curriculum_id
JOIN curriculum_detail cd ON cd.curriculum_id = cur.curriculum_id AND cd.subject_id = s.subject_id
WHERE cc.course_class_status = 'active'
  AND YEAR(sem.start_date) = 2025 
  AND sem.semester_type = 'fall'
  -- NOT already enrolled (using NOT EXISTS to avoid NULL issues)
  AND NOT EXISTS (
      SELECT 1
      FROM student_enrollment se
      JOIN course_class cc2 ON se.course_class_id = cc2.course_class_id
      JOIN course c2 ON cc2.course_id = c2.course_id
      WHERE c2.subject_id = s.subject_id
        AND se.student_id = @test_student_id
        AND se.enrollment_status IN ('enrolled', 'completed', 'passed')
  )
ORDER BY cd.academic_year_index, cd.semester_index, s.subject_code;

-- =================================================================
-- QUERY 5: GENERAL SUBJECTS (AVAILABLE FOR REGISTRATION)
-- =================================================================
SELECT 
    'GENERAL_SUBJECTS_AVAILABLE' AS tag,
    cc.course_class_id,
    s.subject_id,
    s.subject_code,
    s.subject_name,
    sem.semester_name,
    cc.max_students,
    cc.day_of_week,
    cc.start_period,
    cc.end_period
FROM course_class cc
JOIN course c ON cc.course_id = c.course_id
JOIN subject s ON c.subject_id = s.subject_id
JOIN semester sem ON c.semester_id = sem.semester_id
WHERE cc.course_class_status = 'active'
  AND YEAR(sem.start_date) = 2025 
  AND sem.semester_type = 'fall'
  AND s.is_general = 1  -- General subjects only
  -- NOT already enrolled (using NOT EXISTS to avoid NULL issues)
  AND NOT EXISTS (
      SELECT 1
      FROM student_enrollment se
      JOIN course_class cc2 ON se.course_class_id = cc2.course_class_id
      JOIN course c2 ON cc2.course_id = c2.course_id
      WHERE c2.subject_id = s.subject_id
        AND se.student_id = @test_student_id
        AND se.enrollment_status IN ('enrolled', 'completed', 'passed')
  )
ORDER BY s.subject_code;