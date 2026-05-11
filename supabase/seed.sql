-- Cortexia demo seed (run AFTER schema.sql)
-- Creates:
-- - 1 school
-- - 1 student + 1 staff credential
-- - sample knowledge items for visitor/student/staff

with inserted_school as (
  insert into public.schools (name, slug, is_active)
  values ('Demo Public School', 'demo-public-school', true)
  returning id
),
inserted_student as (
  insert into public.users (school_id, role, name, adm_no)
  select id, 'student', 'Aarav Sharma', 'STU-1001'
  from inserted_school
  returning id
),
inserted_staff as (
  insert into public.users (school_id, role, name, staff_id)
  select id, 'staff', 'Ms. Iyer', 'STAFF-9001'
  from inserted_school
  returning id
)
insert into public.knowledge_items (school_id, access_level, category, title, content, source)
select s.id, v.access_level, v.category, v.title, v.content, v.source
from inserted_school s
cross join (
  values
    -- Visitor
    ('visitor','timings','School timings','School hours are Monday–Friday 8:00 AM–2:30 PM. Office hours are 8:00 AM–4:00 PM.','Admin Office'),
    ('visitor','policies','Attendance policy','Students must maintain at least 75% attendance. Late arrivals beyond 10 minutes are marked late.','School Policy'),
    ('visitor','policies','Uniform policy','Uniform is mandatory on all working days. House T-shirt is allowed on sports days as announced.','School Policy'),
    ('visitor','facilities','Facilities available','Library, Science Labs, Computer Lab, Auditorium, Basketball court, Infirmary, Counseling room.','School Overview'),
    ('visitor','fees','Fee structure overview','Fee structure varies by grade. For exact fee details and status, Student login is required.','Accounts Office'),
    ('visitor','contact_admin','Contact details','Reception: +91-00000-00000. Admin Office: admin@example.com. Principal Office: principal@example.com.','School Directory'),

    -- Student
    ('student','class_schedule','Class schedules','Class timetables are published weekly. Ask: \"Timetable for Class 9A\".','Academic Office'),
    ('student','events','Upcoming events','Techfest prep meet: Friday 1:30 PM (Auditorium). Science exhibition submissions due next Wednesday.','Events Desk'),
    ('student','competitions','Competitions','Robotics tryouts next Tuesday 2:45 PM in the Computer Lab. Debate selections on Thursday.','Clubs Coordinator'),
    ('student','contact_teachers','Teacher contacts','For official queries, contact teachers via the school email format: firstname.lastname@school.edu.','Academic Office'),
    ('student','fee_status','Fees status','Fees status is available after student verification. (Demo: pending for Term 2).','Accounts Office'),

    -- Staff
    ('staff','staff_meetings','Upcoming staff meetings','Staff meeting every Monday 3:15 PM (Staff Room). Emergency briefing as needed.','Admin'),
    ('staff','staff_timetable','Staff timetable access','Staff timetables are available by staff ID. Ask: \"My timetable\".','Academic Office'),
    ('staff','emergency','Emergency info','Emergency contacts: Security Desk +91-00000-00001. Nearest clinic: City Clinic (10 min).','Admin')
) as v(access_level, category, title, content, source);

-- Quick peek
select 'Seed complete' as status;

