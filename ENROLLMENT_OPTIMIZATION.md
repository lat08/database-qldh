# Course Enrollment Optimization

## Problem Analysis: Course Classes with 0 Enrollments

### Root Causes Identified

#### 1. **Curriculum Mismatch Issue** ⚠️
**Before:**
- Course creation: Random 70% of ALL subjects each semester
- Course demand: Only calculated for subjects in student curricula
- **Result:** Many courses offered for subjects no student needs

**After:**
- Course creation: 80% curriculum subjects + 20% electives
- Course demand: Curriculum courses + 30% elective interest
- **Result:** Better alignment between offerings and student needs

#### 2. **Student Eligibility Restrictions** ⚠️
**Before:**
- Students could only enroll in subjects from their curriculum
- No flexibility for elective courses
- **Result:** Many course classes created but inaccessible to students

**After:**
- Students enroll in 100% curriculum courses + 20% elective courses
- More realistic academic behavior simulation
- **Result:** Higher enrollment rates across all courses

#### 3. **Semester/Year Filtering Misalignment** ⚠️
**Before:**
- Course classes created for all past years
- Students restricted from enrolling in courses before their start year
- **Result:** Historical courses with no eligible students

**After:**
- Maintained proper semester filtering
- Improved demand calculation considers student start years
- **Result:** Course classes only created when students can actually enroll

## Implementation Changes

### 1. **Course Creation (`courses.py`)**
```python
# BEFORE: Random selection
subjects_to_offer = random.sample(self.data['subjects'], num_to_offer)

# AFTER: Curriculum-priority selection
curriculum_to_offer = int(total_to_offer * 0.8)  # 80% curriculum
elective_to_offer = total_to_offer - curriculum_to_offer  # 20% electives
```

### 2. **Course Demand Calculation (`courses.py`)**
```python
# BEFORE: Only curriculum courses
if course['subject_id'] in curriculum_subject_ids:
    course_demand[course['course_id']].add(student['student_id'])

# AFTER: Curriculum + electives
if is_curriculum_course:
    should_add_demand = True
elif is_elective_course and random.random() < 0.3:  # 30% interest
    should_add_demand = True
```

### 3. **Student Enrollment (`enrollments.py`)**
```python
# BEFORE: Only curriculum courses
if course['subject_id'] not in curriculum_subject_ids:
    continue

# AFTER: Curriculum + electives
if is_curriculum_course:
    eligible_courses.append(course)
elif is_elective_course and random.random() < 0.2:  # 20% enrollment
    eligible_courses.append(course)
```

## Expected Outcomes

### ✅ **Significant Reduction in Zero-Enrollment Course Classes**
- **Before:** ~40-50% of course classes had 0 enrollments
- **After:** Expected ~5-10% of course classes with 0 enrollments

### ✅ **Better Academic Realism**
- Students take courses both in and outside their major
- More diverse enrollment patterns
- Better simulation of real university behavior

### ✅ **Improved Resource Utilization**
- Course classes are created based on actual demand
- Better instructor and room utilization
- More realistic enrollment distributions

### ✅ **Enhanced Payment Coverage**
- More enrollments = more payments (except Fall 2025)
- Better test data for payment verification
- More realistic financial scenarios

## Verification Strategy

### 1. **Check Zero-Enrollment Course Classes**
```sql
-- Run this query to verify improvement
SELECT COUNT(*) AS course_classes_with_zero_enrollments
FROM course_class cc
WHERE cc.is_deleted = 0 AND cc.is_active = 1
AND NOT EXISTS (
    SELECT 1 FROM student_enrollment se
    WHERE se.course_class_id = cc.course_class_id
    AND se.is_deleted = 0 AND se.is_active = 1
);
```

### 2. **Analyze Enrollment Distribution**
- Check enrollment counts per course class
- Verify curriculum vs elective enrollment rates
- Ensure test students have adequate enrollments

### 3. **Validate Payment Coverage**
- Confirm all non-Fall-2025 enrollments are paid
- Verify payment policy implementation
- Check overall payment statistics

## Long-term Benefits

1. **Better Data Quality:** More realistic test data for application development
2. **Improved Testing:** Better coverage of enrollment scenarios
3. **Enhanced Performance:** Fewer empty course classes reduce database bloat
4. **Realistic Scenarios:** More accurate simulation of university operations
5. **Automated Cleanup:** Empty course classes automatically removed (except upcoming semester)

## Automated Cleanup Process

### **Phase 12: Data Cleanup**
A new cleanup phase has been added that automatically removes course classes with 0 enrollments:

**✅ What Gets Deleted:**
- Course classes with no active student enrollments
- All related dependent records (grades, exams, schedule changes)
- Only applies to past and completed semesters

**🛡️ What Gets Preserved:**
- Fall 2025 (HK1 2025-2026) course classes - upcoming semester
- All course classes with active enrollments
- All related data for preserved course classes

**🔧 Constraint-Safe Deletion:**
The cleanup process follows proper deletion order to avoid constraint violations:
1. Delete `enrollment_grade_detail` records
2. Delete `enrollment_grade_version` records  
3. Delete `exam_entry` records (FIXED - was missing)
4. Delete `exam_class` records
5. Delete `schedule_change` records
6. Delete `change_schedule_request` records
7. Finally delete empty `course_class` records

### **Expected Cleanup Results:**
- **Before:** ~40-50% of course classes had 0 enrollments
- **After Optimization:** ~5-10% of course classes had 0 enrollments  
- **After Cleanup:** ~0-2% of course classes have 0 enrollments (only Fall 2025 if needed)

## Monitoring Recommendations

1. Track zero-enrollment course classes after each generation
2. Monitor curriculum vs elective enrollment ratios
3. Verify payment policy compliance
4. Check for any remaining enrollment gaps
5. **NEW:** Verify cleanup process completion and Fall 2025 preservation