#!/usr/bin/env python3
"""
Test script to verify that test students don't get enrolled in multiple courses of the same subject.
"""

import sys
sys.path.append('.')

from modules.base_generator import SQLDataGenerator

def test_duplicate_enrollments():
    """Test that test students don't have duplicate subject enrollments"""
    
    # Generate a small dataset to test
    generator = SQLDataGenerator('specs.txt', 'test_output.sql')
    
    # Create basic data structure
    generator.parse_specifications()
    generator.create_divisions()
    generator.create_faculties_departments()
    generator.create_training_systems()
    generator.create_subjects()
    generator.create_curricula()
    generator.create_academic_years()
    generator.create_semesters()
    generator.create_buildings_rooms()
    generator.create_classes()
    generator.create_people()
    generator.create_users()
    generator.create_roles()
    generator.create_permissions()
    generator.create_role_permissions()
    generator.create_user_roles()
    generator.create_courses()
    generator.create_course_classes()
    
    # Create enrollments (this is where our fix should work)
    generator.create_student_enrollments()
    
    # Test: Check for duplicate subject enrollments for test students
    print("Checking for duplicate subject enrollments...")
    
    test_student_issues = []
    
    # Get all test student IDs
    test_student_ids = []
    for account_name, account_data in generator.data.get('fixed_accounts', {}).items():
        if account_name.startswith('student'):
            test_student_id = account_data.get('student_id')
            if test_student_id:
                test_student_ids.append(test_student_id)
    
    print(f"Found {len(test_student_ids)} test students")
    
    # Check each test student
    for test_student_id in test_student_ids:
        student_enrollments = [e for e in generator.data['enrollments'] if e['student_id'] == test_student_id]
        
        # Group enrollments by subject
        subjects_enrolled = {}
        for enrollment in student_enrollments:
            course_id = enrollment['course_id']
            course = next((c for c in generator.data['courses'] if c['course_id'] == course_id), None)
            if course:
                subject_id = course['subject_id']
                if subject_id not in subjects_enrolled:
                    subjects_enrolled[subject_id] = []
                subjects_enrolled[subject_id].append(enrollment)
        
        # Check for duplicates
        duplicate_subjects = []
        for subject_id, enrollments in subjects_enrolled.items():
            if len(enrollments) > 1:
                duplicate_subjects.append({
                    'subject_id': subject_id,
                    'enrollment_count': len(enrollments),
                    'enrollments': enrollments
                })
        
        if duplicate_subjects:
            test_student_issues.append({
                'student_id': test_student_id,
                'duplicate_subjects': duplicate_subjects
            })
        
        print(f"Test student {test_student_id[:8]}: {len(student_enrollments)} enrollments, {len(subjects_enrolled)} unique subjects")
        if duplicate_subjects:
            print(f"  WARNING: Found {len(duplicate_subjects)} subjects with multiple enrollments")
            for dup in duplicate_subjects:
                print(f"    Subject {dup['subject_id'][:8]}: {dup['enrollment_count']} enrollments")
    
    # Summary
    print(f"\nSummary:")
    print(f"Test students checked: {len(test_student_ids)}")
    print(f"Students with duplicate subject enrollments: {len(test_student_issues)}")
    
    if test_student_issues:
        print("FAILED: Found duplicate subject enrollments!")
        for issue in test_student_issues:
            print(f"  Student {issue['student_id'][:8]} has duplicates in {len(issue['duplicate_subjects'])} subjects")
        return False
    else:
        print("PASSED: No duplicate subject enrollments found!")
        return True

if __name__ == "__main__":
    success = test_duplicate_enrollments()
    sys.exit(0 if success else 1)