-- ============================================================
-- VERIFY NOTIFICATIONS FOR TEST ACCOUNTS
-- ============================================================
-- Check notifications specifically targeted to test student and test instructor
-- Expected: 20 notifications each for student.test@edu.vn and instructor.test@edu.vn

USE EduManagement;
GO

PRINT '============================================================';
PRINT 'VERIFYING NOTIFICATIONS FOR TEST ACCOUNTS';
PRINT '============================================================';

-- Fixed test account IDs from specs
DECLARE @test_student_id UNIQUEIDENTIFIER = '00000000-0000-0000-0000-000000000003';
DECLARE @test_instructor_id UNIQUEIDENTIFIER = '00000000-0000-0000-0000-000000000013';

PRINT '';
PRINT '1. NOTIFICATIONS SPECIFICALLY FOR TEST STUDENT (student.test@edu.vn)';
PRINT '   Expected: 20 notifications with target_type=''student'' and target_id=test_student_id';
PRINT '   --------------------------------------------------------';

SELECT 
    ns.notification_type,
    ns.title,
    ns.content,
    ns.target_type,
    ns.target_id,
    ns.status,
    ns.scheduled_date,
    ns.visible_from,
    ns.event_location,
    ns.created_at
FROM notification_schedule ns
WHERE ns.target_type = 'student' 
  AND ns.target_id = @test_student_id
  AND ns.is_deleted = 0
ORDER BY ns.created_at DESC;

PRINT '';
PRINT 'COUNT: Notifications for test student:';
SELECT COUNT(*) as notification_count
FROM notification_schedule ns
WHERE ns.target_type = 'student' 
  AND ns.target_id = @test_student_id
  AND ns.is_deleted = 0;

PRINT '';
PRINT '2. NOTIFICATIONS SPECIFICALLY FOR TEST INSTRUCTOR (instructor.test@edu.vn)';
PRINT '   Expected: 20 notifications with target_type=''instructor'' and target_id=test_instructor_id';
PRINT '   --------------------------------------------------------';

SELECT 
    ns.notification_type,
    ns.title,
    ns.content,
    ns.target_type,
    ns.target_id,
    ns.status,
    ns.scheduled_date,
    ns.visible_from,
    ns.event_location,
    ns.created_at
FROM notification_schedule ns
WHERE ns.target_type = 'instructor' 
  AND ns.target_id = @test_instructor_id
  AND ns.is_deleted = 0
ORDER BY ns.created_at DESC;

PRINT '';
PRINT 'COUNT: Notifications for test instructor:';
SELECT COUNT(*) as notification_count
FROM notification_schedule ns
WHERE ns.target_type = 'instructor' 
  AND ns.target_id = @test_instructor_id
  AND ns.is_deleted = 0;

PRINT '';
PRINT '3. GENERAL NOTIFICATIONS THAT APPLY TO TEST ACCOUNTS';
PRINT '   (all, all_students, all_instructors, class-specific, faculty-specific)';
PRINT '   --------------------------------------------------------';

-- Get test student's class_id and faculty_id for context
DECLARE @test_student_class_id UNIQUEIDENTIFIER;
DECLARE @test_student_faculty_id UNIQUEIDENTIFIER;

SELECT @test_student_class_id = s.class_id
FROM student s
WHERE s.student_id = @test_student_id;

SELECT @test_student_faculty_id = d.faculty_id
FROM student s
JOIN class c ON s.class_id = c.class_id
JOIN department d ON c.department_id = d.department_id
WHERE s.student_id = @test_student_id;

-- Get test instructor's faculty_id
DECLARE @test_instructor_faculty_id UNIQUEIDENTIFIER;

SELECT @test_instructor_faculty_id = i.faculty_id
FROM instructor i
WHERE i.instructor_id = @test_instructor_id;

PRINT 'General notifications that TEST STUDENT would see:';
SELECT 
    ns.notification_type,
    ns.title,
    ns.target_type,
    ns.target_id,
    ns.status,
    ns.scheduled_date,
    CASE 
        WHEN ns.target_type = 'all' THEN 'Everyone'
        WHEN ns.target_type = 'all_students' THEN 'All Students'
        WHEN ns.target_type = 'class' AND ns.target_id = @test_student_class_id THEN 'Student''s Class'
        WHEN ns.target_type = 'faculty' AND ns.target_id = @test_student_faculty_id THEN 'Student''s Faculty'
        ELSE 'Other'
    END AS applies_to_test_student
FROM notification_schedule ns
WHERE ns.is_deleted = 0
  AND (
      ns.target_type = 'all' 
      OR ns.target_type = 'all_students'
      OR (ns.target_type = 'class' AND ns.target_id = @test_student_class_id)
      OR (ns.target_type = 'faculty' AND ns.target_id = @test_student_faculty_id)
  )
ORDER BY ns.created_at DESC;

PRINT '';
PRINT 'General notifications that TEST INSTRUCTOR would see:';
SELECT 
    ns.notification_type,
    ns.title,
    ns.target_type,
    ns.target_id,
    ns.status,
    ns.scheduled_date,
    CASE 
        WHEN ns.target_type = 'all' THEN 'Everyone'
        WHEN ns.target_type = 'all_instructors' THEN 'All Instructors'
        WHEN ns.target_type = 'faculty' AND ns.target_id = @test_instructor_faculty_id THEN 'Instructor''s Faculty'
        ELSE 'Other'
    END AS applies_to_test_instructor
FROM notification_schedule ns
WHERE ns.is_deleted = 0
  AND (
      ns.target_type = 'all' 
      OR ns.target_type = 'all_instructors'
      OR (ns.target_type = 'faculty' AND ns.target_id = @test_instructor_faculty_id)
  )
ORDER BY ns.created_at DESC;

PRINT '';
PRINT '4. NOTIFICATION READ STATUS FOR TEST ACCOUNTS';
PRINT '   --------------------------------------------------------';

-- Get test account user IDs
DECLARE @test_student_user_id UNIQUEIDENTIFIER;
DECLARE @test_instructor_user_id UNIQUEIDENTIFIER;

SELECT @test_student_user_id = ua.user_id
FROM user_account ua
JOIN person p ON ua.person_id = p.person_id
WHERE p.email = 'student.test@edu.vn';

SELECT @test_instructor_user_id = ua.user_id
FROM user_account ua
JOIN person p ON ua.person_id = p.person_id
WHERE p.email = 'instructor.test@edu.vn';

PRINT 'Read notifications for TEST STUDENT:';
SELECT 
    ns.notification_type,
    ns.title,
    ns.target_type,
    nur.read_at
FROM notification_user_read nur
JOIN notification_schedule ns ON nur.schedule_id = ns.schedule_id
WHERE nur.user_id = @test_student_user_id
ORDER BY nur.read_at DESC;

PRINT '';
PRINT 'Read notifications for TEST INSTRUCTOR:';
SELECT 
    ns.notification_type,
    ns.title,
    ns.target_type,
    nur.read_at
FROM notification_user_read nur
JOIN notification_schedule ns ON nur.schedule_id = ns.schedule_id
WHERE nur.user_id = @test_instructor_user_id
ORDER BY nur.read_at DESC;

PRINT '';
PRINT '5. SUMMARY';
PRINT '   --------------------------------------------------------';

SELECT 
    'Test Student Specific Notifications' as notification_category,
    COUNT(*) as count
FROM notification_schedule ns
WHERE ns.target_type = 'student' 
  AND ns.target_id = @test_student_id
  AND ns.is_deleted = 0

UNION ALL

SELECT 
    'Test Instructor Specific Notifications' as notification_category,
    COUNT(*) as count
FROM notification_schedule ns
WHERE ns.target_type = 'instructor' 
  AND ns.target_id = @test_instructor_id
  AND ns.is_deleted = 0

UNION ALL

SELECT 
    'Total General Notifications' as notification_category,
    COUNT(*) as count
FROM notification_schedule ns
WHERE ns.is_deleted = 0
  AND NOT (
      (ns.target_type = 'student' AND ns.target_id = @test_student_id)
      OR (ns.target_type = 'instructor' AND ns.target_id = @test_instructor_id)
  );

PRINT '';
PRINT 'Expected Results:';
PRINT '- Test Student Specific Notifications: 20';
PRINT '- Test Instructor Specific Notifications: 20';
PRINT '- Total General Notifications: 200';
PRINT '- Total Notifications: 240';

GO