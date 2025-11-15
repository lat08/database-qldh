-- ============================================================
-- DELETE CONFLICTING ENTRIES - HARD DELETE VERSION
-- ============================================================

USE EduManagement;
GO

BEGIN TRANSACTION;

PRINT 'Deleting conflicts...';

DECLARE @StudentTestEmail VARCHAR(255) = 'student.test@edu.vn';
DECLARE @InstructorTestEmail VARCHAR(255) = 'instructor.test@edu.vn';

DECLARE @StudentId UNIQUEIDENTIFIER;
SELECT @StudentId = s.student_id 
FROM student s
INNER JOIN person p ON s.person_id = p.person_id 
WHERE p.email = @StudentTestEmail;

DECLARE @InstructorId UNIQUEIDENTIFIER;
SELECT @InstructorId = i.instructor_id 
FROM instructor i
INNER JOIN person p ON i.person_id = p.person_id 
WHERE p.email = @InstructorTestEmail;

-- Delete student course-exam conflicts (HARD DELETE)
IF @StudentId IS NOT NULL
BEGIN
    WITH StudentCourseSchedule AS (
        SELECT 
            se.enrollment_id,
            cc.course_class_id,
            s.subject_code,
            cc.day_of_week,
            cc.start_period,
            cc.end_period,
            cc.date_start,
            cc.date_end,
            CASE 
                WHEN cc.start_period BETWEEN 1 AND 5 THEN 'Morning'
                WHEN cc.start_period BETWEEN 6 AND 9 THEN 'Afternoon'  
                WHEN cc.start_period BETWEEN 10 AND 12 THEN 'Evening'
            END AS time_block
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN subject s ON c.subject_id = s.subject_id
        WHERE se.student_id = @StudentId 
            AND se.is_active = 1 
            AND se.enrollment_status = 'registered'
    ),
    StudentExamSchedule AS (
        SELECT 
            ec.exam_class_id,
            s.subject_code,
            CAST(ec.start_time AS DATE) AS exam_date,
            DATEPART(dw, ec.start_time) + 1 AS day_of_week,
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
        WHERE se.student_id = @StudentId 
            AND se.is_active = 1 
            AND se.enrollment_status = 'registered'
            AND ec.exam_status = 'scheduled'
    )
    DELETE FROM exam_class
    WHERE exam_class_id IN (
        SELECT e.exam_class_id
        FROM StudentCourseSchedule c
        INNER JOIN StudentExamSchedule e ON 
            c.day_of_week = e.day_of_week
            AND c.time_block = e.time_block
            AND e.exam_date BETWEEN c.date_start AND c.date_end
    );
    
    PRINT 'Student course-exam conflicts deleted: ' + CAST(@@ROWCOUNT AS VARCHAR);

    -- Additional step: remove student exam-exam overlapping exams
    -- Some exams may be scheduled at the exam->course level (exam_class.exam_id -> exam.course_id)
    -- and not linked directly via course_class_id. The previous delete only removed exam_class
    -- rows that were attached to the course_class. This block finds overlapping exam_class rows
    -- for the student's enrolled courses (via exam->course) and deletes both sides of any overlap.
    WITH StudentExams AS (
        SELECT 
            ec.exam_class_id,
            CAST(ec.start_time AS DATE) AS exam_date,
            ec.start_time,
            DATEADD(MINUTE, ec.duration_minutes, ec.start_time) AS end_time
        FROM student_enrollment se
        INNER JOIN course_class cc ON se.course_class_id = cc.course_class_id
        INNER JOIN course c ON cc.course_id = c.course_id
        INNER JOIN exam e ON e.course_id = c.course_id
        INNER JOIN exam_class ec ON ec.exam_id = e.exam_id
        WHERE se.student_id = @StudentId
            AND se.is_active = 1
            AND se.enrollment_status = 'registered'
            AND ec.is_active = 1
            AND ec.exam_status = 'scheduled'
    ),
    Overlaps AS (
        SELECT s1.exam_class_id AS id1, s2.exam_class_id AS id2
        FROM StudentExams s1
        INNER JOIN StudentExams s2 ON 
            s1.exam_class_id < s2.exam_class_id
            AND s1.exam_date = s2.exam_date
            AND s1.start_time < s2.end_time
            AND s1.end_time > s2.start_time
    )
    DELETE FROM exam_class
    WHERE exam_class_id IN (
        SELECT id1 FROM Overlaps
        UNION
        SELECT id2 FROM Overlaps
    );

    PRINT 'Student exam-exam overlapping conflicts deleted: ' + CAST(@@ROWCOUNT AS VARCHAR);
END

-- Delete instructor course-exam conflicts (HARD DELETE)
IF @InstructorId IS NOT NULL
BEGIN
    WITH InstructorCourseSchedule AS (
        SELECT 
            cc.course_class_id,
            cc.day_of_week,
            cc.start_period,
            cc.end_period,
            cc.date_start,
            cc.date_end,
            CASE 
                WHEN cc.start_period BETWEEN 1 AND 5 THEN 'Morning'
                WHEN cc.start_period BETWEEN 6 AND 9 THEN 'Afternoon'  
                WHEN cc.start_period BETWEEN 10 AND 12 THEN 'Evening'
            END AS time_block
        FROM course_class cc
        WHERE cc.instructor_id = @InstructorId
            AND cc.is_active = 1 
            AND cc.course_class_status = 'active'
    ),
    InstructorExamSchedule AS (
        SELECT 
            ec.exam_class_id,
            CAST(ec.start_time AS DATE) AS exam_date,
            DATEPART(dw, ec.start_time) + 1 AS day_of_week,
            CASE 
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 6 AND 11 THEN 'Morning'
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 12 AND 17 THEN 'Afternoon'
                WHEN DATEPART(HOUR, ec.start_time) BETWEEN 18 AND 23 THEN 'Evening'
                ELSE 'Night'
            END AS time_block
        FROM exam_class ec
        WHERE ec.monitor_instructor_id = @InstructorId
            AND ec.is_active = 1 
            AND ec.exam_status = 'scheduled'
    )
    DELETE FROM exam_class
    WHERE exam_class_id IN (
        SELECT e.exam_class_id
        FROM InstructorCourseSchedule c
        INNER JOIN InstructorExamSchedule e ON 
            c.day_of_week = e.day_of_week
            AND c.time_block = e.time_block
            AND e.exam_date BETWEEN c.date_start AND c.date_end
    );
    
    PRINT 'Instructor course-exam conflicts deleted: ' + CAST(@@ROWCOUNT AS VARCHAR);

    -- Delete instructor exam-exam conflicts (HARD DELETE)
    WITH InstructorExamSchedule AS (
        SELECT 
            ec.exam_class_id,
            ec.start_time,
            DATEADD(MINUTE, ec.duration_minutes, ec.start_time) AS end_time,
            CAST(ec.start_time AS DATE) AS exam_date
        FROM exam_class ec
        WHERE ec.monitor_instructor_id = @InstructorId
            AND ec.is_active = 1 
            AND ec.exam_status = 'scheduled'
    )
    DELETE FROM exam_class
    WHERE exam_class_id IN (
        SELECT e1.exam_class_id
        FROM InstructorExamSchedule e1
        INNER JOIN InstructorExamSchedule e2 ON 
            e1.exam_class_id < e2.exam_class_id
            AND e1.exam_date = e2.exam_date
            AND e1.start_time < e2.end_time 
            AND e1.end_time > e2.start_time
    );
    
    PRINT 'Instructor exam-exam conflicts deleted: ' + CAST(@@ROWCOUNT AS VARCHAR);
END

COMMIT TRANSACTION;
PRINT 'Done - conflicts permanently deleted.';