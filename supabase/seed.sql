-- ============================================================
-- Cortexia — Full Seed
-- Run AFTER schema.sql
-- Inserts: school, users, knowledge items, fees, admin
--          credentials, classes, student–class links,
--          and full Mon–Fri timetables for 9A and 10B
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- 1. SCHOOL + CORE USERS + KNOWLEDGE ITEMS
-- ──────────────────────────────────────────────────────────
with inserted_school as (
  insert into public.schools (name, slug, is_active)
  values ('Demo Public School', 'demo-public-school', true)
  on conflict (slug) do update set name = excluded.name
  returning id
),

inserted_student as (
  insert into public.users (school_id, role, name, adm_no)
  select id, 'student', 'Aarav Sharma', 'STU-1001'
  from inserted_school
  on conflict do nothing
  returning id
),

inserted_staff as (
  insert into public.users (school_id, role, name, staff_id)
  select id, 'staff', 'Ms. Iyer', 'STAFF-9001'
  from inserted_school
  on conflict do nothing
  returning id
)

insert into public.knowledge_items (school_id, access_level, category, title, content, source)
select s.id, v.access_level, v.category, v.title, v.content, v.source
from inserted_school s
cross join (values

  -- ================================================================
  -- VISITOR — TIMINGS
  -- ================================================================
  ('visitor', 'timings', 'School hours',
   'School is open Monday to Friday. Classes begin at 8:00 AM and end at 2:30 PM. Students should arrive by 7:50 AM. Gates close at 8:10 AM.',
   'Admin Office'),

  ('visitor', 'timings', 'Office hours',
   'The administrative office is open Monday to Friday from 8:00 AM to 4:00 PM. On Saturdays, the office operates from 9:00 AM to 12:00 PM for parent visits only.',
   'Admin Office'),

  ('visitor', 'timings', 'Library hours',
   'The school library is open Monday to Friday from 8:00 AM to 4:30 PM. Students can access the library during free periods and after school hours until 4:30 PM.',
   'Library'),

  ('visitor', 'timings', 'Lunch and break timings',
   'Morning break: 10:30 AM to 10:45 AM. Lunch break: 12:30 PM to 1:15 PM. Students must remain on school premises during all breaks.',
   'Admin Office'),

  ('visitor', 'timings', 'Early dismissal days',
   'On the last Saturday of each month, school ends at 12:00 PM. Parents are notified via the school app at least 3 days in advance.',
   'Admin Office'),

  ('visitor', 'timings', 'Parent visiting hours',
   'Parents may visit the school between 9:00 AM and 11:00 AM on weekdays without a prior appointment. For meetings with the Principal, appointments must be scheduled at least 2 working days in advance.',
   'Admin Office'),

  -- ================================================================
  -- VISITOR — FEES (GENERAL)
  -- ================================================================
  ('visitor', 'fees', 'General fee structure',
   'Fee structure for the current academic year 2025–26: Grade 1–5: ₹45,000/term. Grade 6–8: ₹55,000/term. Grade 9–10: ₹65,000/term. Grade 11–12 (Science/Commerce): ₹75,000/term. Fees are due in three terms: April, August, and January.',
   'Accounts Office'),

  ('visitor', 'fees', 'Admission fee',
   'A one-time non-refundable admission fee of ₹15,000 applies to all new students. This covers registration, ID card, almanac, and the school diary for the first year.',
   'Accounts Office'),

  ('visitor', 'fees', 'Fee payment methods',
   'Fees can be paid via: (1) Online portal at fees.demopublicschool.edu, (2) NEFT/RTGS to the school bank account (details at reception), (3) Demand Draft in favour of "Demo Public School". Cash payments are not accepted above ₹2,000.',
   'Accounts Office'),

  ('visitor', 'fees', 'Late fee penalty',
   'A late fee of ₹500 per month is charged if fees are not paid within 15 days of the due date. Students with outstanding fees for more than 45 days may be temporarily withheld from exams until dues are cleared.',
   'Accounts Office'),

  ('visitor', 'fees', 'Fee concession and scholarships',
   'Merit scholarships are available for students scoring above 90% in the previous annual exam — 25% fee waiver for 90–95%, and 50% fee waiver for above 95%. Sibling discount of 10% applies from the second child onwards. Financial hardship cases can apply to the Principal with supporting documents.',
   'Accounts Office'),

  ('visitor', 'fees', 'Refund policy',
   'If a student withdraws before the academic year begins, 75% of the term fee is refunded. No refund is issued after the first 30 days of the term. The admission fee is non-refundable under all circumstances.',
   'Accounts Office'),

  -- ================================================================
  -- VISITOR — POLICIES
  -- ================================================================
  ('visitor', 'policies', 'Attendance policy',
   'Students must maintain a minimum of 75% attendance per term to be eligible for terminal and annual examinations. Students with attendance below 65% will receive a warning letter sent to parents. Below 50% attendance requires a written explanation to the Principal.',
   'School Policy'),

  ('visitor', 'policies', 'Attendance policy — consequences',
   'Students failing to meet the 75% attendance threshold will not be permitted to sit for internal assessments or board-affiliated examinations. The school will not provide condonation letters for preventable absences. Medical leave requires a doctor''s certificate submitted within 3 days of return.',
   'School Policy'),

  ('visitor', 'policies', 'Late arrival policy',
   'Students arriving after 8:10 AM are marked late. Three late arrivals in a month count as one absent day. Parents are notified by SMS after the second late arrival in a week. Repeated lateness may result in a meeting with the class teacher and a note in the student''s conduct record.',
   'School Policy'),

  ('visitor', 'policies', 'Uniform policy',
   'Full school uniform is mandatory on all working days. Boys: white shirt, navy trousers, black shoes, school tie, school belt. Girls: white shirt, navy skirt/salwar, black shoes, school tie. House T-shirt and track pants are permitted only on declared sports days. No jewellery except small stud earrings for girls.',
   'School Policy'),

  ('visitor', 'policies', 'Uniform violation consequences',
   'First offence: verbal warning by class teacher. Second offence: written note in diary requiring parent signature. Third offence: student is sent to the Vice Principal and parents are called. Repeated violations are recorded in the conduct report submitted at year end.',
   'School Policy'),

  ('visitor', 'policies', 'Mobile phone policy',
   'Mobile phones are strictly prohibited inside school premises for students of Grade 1–8. Students of Grade 9–12 may carry phones but must keep them switched off and in their bags during school hours. Phones found in use during class will be confiscated and returned only to parents.',
   'School Policy'),

  ('visitor', 'policies', 'Mobile phone confiscation policy',
   'Confiscated phones are held in the office for 7 days on first offence, 30 days on second offence, and retained until end of term on third offence. The school is not responsible for damage to confiscated devices.',
   'School Policy'),

  ('visitor', 'policies', 'Discipline and conduct',
   'Students are expected to maintain respectful behaviour toward all staff, fellow students, and visitors. Bullying, ragging, use of abusive language, and vandalism are zero-tolerance offences. Any student found involved in such conduct will face suspension and a conduct committee review.',
   'School Policy'),

  ('visitor', 'policies', 'Discipline consequences',
   'Minor offences (dress code, late submission): recorded in diary, parent notification. Moderate offences (disruptive behaviour, cheating in class tests): detention, parent meeting, entry in conduct record. Serious offences (bullying, vandalism, substance use): suspension of 3–10 days, conduct committee review, possible expulsion for repeat offences.',
   'School Policy'),

  ('visitor', 'policies', 'Leave application process',
   'For planned leave, a written application must be submitted to the class teacher at least 2 days in advance. For medical leave, a doctor''s certificate must be submitted on the day of return. Leave of more than 5 consecutive days requires approval from the Vice Principal.',
   'School Policy'),

  ('visitor', 'policies', 'Exam and assessment policy',
   'The academic year has three terms. Each term includes: Periodic Test (20 marks), Mid-Term Exam (80 marks), and Term-End Exam (100 marks). Grades 9–12 follow the CBSE assessment pattern. Students must appear in all scheduled assessments; re-tests are only granted for medical emergencies with valid documentation.',
   'Academic Office'),

  ('visitor', 'policies', 'Academic integrity policy',
   'Copying, plagiarism, or use of unfair means during any assessment is a serious offence. First offence: zero in that paper and parent notification. Second offence: suspension and referral to the conduct committee. For board exams, the school follows CBSE''s unfair means policy strictly.',
   'Academic Office'),

  -- ================================================================
  -- VISITOR — FACILITIES
  -- ================================================================
  ('visitor', 'facilities', 'Library',
   'The school library houses over 12,000 books across fiction, non-fiction, reference, and curriculum sections. Students may borrow up to 2 books for 14 days. The library also has 10 digital reading stations with access to NCERT e-books and select online journals.',
   'Library'),

  ('visitor', 'facilities', 'Science labs',
   'The school has three fully equipped science labs: Physics Lab (Grade 9–12), Chemistry Lab (Grade 9–12), and a combined Biology/Environmental Science Lab (Grade 6–12). All labs follow strict safety protocols. Students must wear lab coats and safety goggles during practicals.',
   'Academic Office'),

  ('visitor', 'facilities', 'Computer lab',
   'The computer lab has 40 workstations with Windows 11 and internet access. It is used for IT classes (Grade 3–12) and is open for student projects after school hours until 4:00 PM on weekdays. Students must book slots via their class teacher for after-school access.',
   'IT Department'),

  ('visitor', 'facilities', 'Auditorium',
   'The school auditorium seats 600 and is equipped with a full sound system, LED stage lighting, and a projector screen. It is used for assemblies, annual day, competitions, and parent meetings. External bookings are not permitted.',
   'Admin Office'),

  ('visitor', 'facilities', 'Sports facilities',
   'The school has a full-size basketball court, a football ground, a cricket practice net, a 200m running track, and a badminton court. A dedicated sports teacher oversees all activities. Students are encouraged to represent the school in inter-school tournaments.',
   'Sports Department'),

  ('visitor', 'facilities', 'Infirmary',
   'A fully staffed infirmary is available on the ground floor (Block A). A qualified nurse is present Monday to Friday from 7:30 AM to 3:30 PM. A doctor visits every Wednesday from 10:00 AM to 12:00 PM. Parents are contacted immediately for any medical attention beyond first aid.',
   'Admin Office'),

  ('visitor', 'facilities', 'Counseling room',
   'The school has a trained counselor available Tuesday and Thursday from 9:00 AM to 2:00 PM. Students can request a session through their class teacher or directly at the counseling room (Room 14, Block B). All sessions are confidential.',
   'Student Welfare'),

  ('visitor', 'facilities', 'Canteen',
   'The school canteen operates from 10:00 AM to 2:30 PM. It serves vegetarian meals only. Menu is revised monthly and approved by a nutrition consultant. Outside food delivery is not permitted on school premises. Students with dietary requirements should inform the class teacher.',
   'Admin Office'),

  ('visitor', 'facilities', 'Transport',
   'The school operates 8 bus routes covering major residential areas. Monthly transport fee ranges from ₹1,800 to ₹2,500 depending on distance. Bus passes are issued at the start of each term. Parents must register at the transport office to avail bus service.',
   'Transport Office'),

  ('visitor', 'facilities', 'CCTV and security',
   'The school premises are under 24-hour CCTV surveillance. Security personnel are posted at all entry and exit points. Visitors must sign in at the reception and wear a visitor pass at all times. No individual is permitted entry without prior verification.',
   'Admin Office'),

  -- ================================================================
  -- VISITOR — CONTACT / ADMIN
  -- ================================================================
  ('visitor', 'contact_admin', 'Main reception',
   'Reception desk: +91-98100-00001. Open Monday to Saturday, 8:00 AM to 4:00 PM. For general inquiries, email: info@demopublicschool.edu. Response time for emails is 1–2 working days.',
   'School Directory'),

  ('visitor', 'contact_admin', 'Principal office',
   'Principal: Dr. Anita Menon. Office: Block A, Room 101. Contact: principal@demopublicschool.edu. Phone: +91-98100-00002. Appointments can be scheduled through reception or via email. Walk-in requests are accommodated subject to availability.',
   'School Directory'),

  ('visitor', 'contact_admin', 'Vice Principal',
   'Vice Principal (Academics): Mr. Ramesh Nair. Office: Block A, Room 102. Contact: vp.academics@demopublicschool.edu. Handles all academic grievances, timetable queries, and student performance concerns.',
   'School Directory'),

  ('visitor', 'contact_admin', 'Accounts office',
   'Accounts Office: Block C, Ground Floor. Contact: accounts@demopublicschool.edu. Phone: +91-98100-00003. For fee payment, receipts, and scholarship queries. Open Monday to Friday, 9:00 AM to 3:00 PM.',
   'School Directory'),

  ('visitor', 'contact_admin', 'Admission office',
   'Admissions Office: Block A, Room 103. Contact: admissions@demopublicschool.edu. Phone: +91-98100-00004. Admission season runs from January to March each year. Walk-in inquiries welcome during office hours.',
   'School Directory'),

  ('visitor', 'contact_admin', 'Transport office',
   'Transport Coordinator: Mr. Suresh Kumar. Contact: transport@demopublicschool.edu. Phone: +91-98100-00005. For bus route queries, pass renewal, and transport complaints.',
   'School Directory'),

  -- ================================================================
  -- VISITOR — EVENTS (PUBLIC)
  -- ================================================================
  ('visitor', 'events', 'Annual Day 2026',
   'Annual Day is scheduled for 15 March 2026 at 5:00 PM in the school auditorium. The event will feature cultural performances, award ceremonies, and a guest lecture. Parents and alumni are invited. Entry by invitation only — passes distributed through class teachers in February.',
   'Events Desk'),

  ('visitor', 'events', 'Parent-Teacher Meeting schedule',
   'PTMs are held at the end of each term. Term 1 PTM: 20 July 2025. Term 2 PTM: 15 November 2025. Term 3 PTM: 18 March 2026. Individual appointment slots can be pre-booked via the school app 48 hours before the PTM.',
   'Academic Office'),

  ('visitor', 'events', 'School Foundation Day',
   'Foundation Day is celebrated on 5 September each year (Teacher''s Day). The event includes student performances, felicitation of long-serving staff, and a cultural programme. School closes at 12:00 PM on this day.',
   'Events Desk'),

  ('visitor', 'events', 'Sports Day 2026',
   'Annual Sports Day is scheduled for 22 February 2026 on the school grounds. Events include track races, relay, shot put, and team sports. Students must register through their PE teacher by 10 February 2026.',
   'Sports Department'),

  -- ================================================================
  -- STUDENT — CLASS SCHEDULE
  -- ================================================================
  ('student', 'class_schedule', 'Grade 9 timetable — Week A',
   'Monday: Math, English, Physics, Lunch, History, PE. Tuesday: Chemistry, Math, English Lit, Lunch, Geography, Computer. Wednesday: Biology, Hindi, Math, Lunch, Physics Lab, Free. Thursday: English, Chemistry Lab, History, Lunch, Math, Art. Friday: PE, Biology, Hindi, Lunch, Computer Lab, English.',
   'Academic Office'),

  ('student', 'class_schedule', 'Grade 10 timetable — Week A',
   'Monday: Math, English, Chemistry, Lunch, Physics, Hindi. Tuesday: Biology, Math, English, Lunch, History, PE. Wednesday: Chemistry Lab, Hindi, Math, Lunch, Geography, Computer. Thursday: Physics Lab, English, Math, Lunch, Biology, Art. Friday: PE, Computer Lab, Hindi, Lunch, English Lit, Math.',
   'Academic Office'),

  ('student', 'class_schedule', 'Grade 11 Science timetable',
   'Monday: Physics, Chemistry, Math, Lunch, English, IP/CS. Tuesday: Math, Physics Lab, Chemistry, Lunch, English, Biology. Wednesday: Chemistry Lab, Math, Physics, Lunch, Biology Lab, English. Thursday: IP/CS, Math, Chemistry, Lunch, Physics, English. Friday: Biology, English, Math, Lunch, Physics, Chemistry.',
   'Academic Office'),

  ('student', 'class_schedule', 'Grade 6–8 period structure',
   'Grade 6–8 follow a 7-period day with 45-minute periods. Period 1–2: 8:00–9:30 AM. Break: 10:30–10:45 AM. Period 3–4: 10:45 AM–12:15 PM. Lunch: 12:30–1:15 PM. Period 5–7: 1:15–3:00 PM. Remedial classes available on Fridays from 3:00–4:00 PM.',
   'Academic Office'),

  ('student', 'class_schedule', 'Free period and library slots',
   'Each class has one designated library period per week and one free study period. Free periods must be spent in the classroom or library — students may not move to the canteen or corridors during free periods without a hall pass from the class teacher.',
   'Academic Office'),

  -- ================================================================
  -- STUDENT — EVENTS / COMPETITIONS
  -- ================================================================
  ('student', 'events', 'Techfest 2026',
   'Techfest is scheduled for 8–9 February 2026. Events include robotics, coding marathon, app development, and science model exhibition. Registrations open 10 January 2026 via the school portal. Teams of 2–4 students. Open to Grades 7–12.',
   'Events Desk'),

  ('student', 'events', 'Literary Week',
   'Literary Week runs from 3–7 November 2025. Events include debate, spell bee, creative writing, poetry slam, and quiz. Students can register for up to 2 events. Registration closes 25 October 2025. Contact the English department for details.',
   'Events Desk'),

  ('student', 'events', 'Science Exhibition',
   'Annual Science Exhibition: 14 January 2026. Students from Grade 6–12 can submit project proposals by 1 December 2025. Top 3 projects get nominated for the District Science Fair. Submission form available at the academic office.',
   'Science Department'),

  ('student', 'events', 'Inter-House cultural competition',
   'Inter-House cultural events are held in October. Events include dance, drama, singing, and fine arts. Each house fields one team per event. Students interested in participating must register with their House Captain by 30 September 2025.',
   'Events Desk'),

  ('student', 'competitions', 'Robotics Club tryouts',
   'Robotics Club tryouts for new members: every first Tuesday of the month at 2:45 PM in the Computer Lab (Room 22). Bring your student ID. No prior experience needed — aptitude and enthusiasm evaluated. Contact: robotics@demopublicschool.edu.',
   'Clubs Coordinator'),

  ('student', 'competitions', 'Debate team selections',
   'School debate team selections for inter-school competitions: held on the first Thursday after mid-terms. Open to Grade 8–12. Topics are assigned on the day. Selected students represent the school at district and state-level events. Contact the English department to register interest.',
   'English Department'),

  ('student', 'competitions', 'Sports team trials',
   'Basketball trials: every Wednesday 3:00–4:30 PM on the basketball court. Football trials: every Friday 3:00–4:30 PM on the main ground. Cricket trials: Saturdays 9:00–11:00 AM. All students from Grade 6–12 are eligible. Bring sports kit and valid student ID.',
   'Sports Department'),

  ('student', 'competitions', 'Olympiad registrations',
   'The school registers students for: SOF Science Olympiad (Grade 3–12), IMO Math Olympiad (Grade 1–12), and NSO National Science Olympiad (Grade 1–12). Registration opens in August each year. Fee: ₹150 per Olympiad. Contact the academic office to register.',
   'Academic Office'),

  -- ================================================================
  -- STUDENT — TEACHER CONTACTS
  -- ================================================================
  ('student', 'contact_teachers', 'How to contact teachers',
   'All teachers are reachable via official school email in the format: firstname.lastname@demopublicschool.edu. Email is the preferred contact channel. Teachers respond within 1 working day. For urgent academic queries, visit the staffroom (Block B, First Floor) between 8:00–8:30 AM or during lunch break.',
   'Academic Office'),

  ('student', 'contact_teachers', 'Class teachers by grade',
   'Grade 6A: Ms. Priya Nair. Grade 6B: Mr. Arun Kumar. Grade 7A: Ms. Sunita Rao. Grade 7B: Mr. Deepak Joshi. Grade 8A: Ms. Kavita Menon. Grade 8B: Mr. Rajan Pillai. Grade 9A: Ms. Meena Sharma. Grade 9B: Mr. Vinod Tiwari. Grade 10A: Ms. Rekha Das. Grade 10B: Mr. Sanjay Gupta.',
   'Academic Office'),

  ('student', 'contact_teachers', 'Subject heads',
   'Head of Math: Mr. Sanjay Gupta (sanjay.gupta@demopublicschool.edu). Head of Science: Ms. Meena Sharma. Head of English: Ms. Priya Nair. Head of Social Studies: Mr. Rajan Pillai. Head of Hindi: Ms. Rekha Das. Head of Computer Science: Mr. Arun Kumar. Head of PE: Mr. Deepak Joshi.',
   'Academic Office'),

  ('student', 'contact_teachers', 'Counselor contact',
   'School Counselor: Ms. Fatima Sheikh. Available Tuesday and Thursday, 9:00 AM–2:00 PM. Email: counselor@demopublicschool.edu. Room 14, Block B. For mental health support, academic stress, or personal concerns. Walk-ins welcome; pre-booking preferred.',
   'Student Welfare'),

  -- ================================================================
  -- STUDENT — FEE STATUS
  -- ================================================================
  ('student', 'fee_status', 'How to check fee status',
   'Log in to the student portal at portal.demopublicschool.edu using your admission number and date of birth. Go to "My Fees" to view term-wise payment history, outstanding dues, and download receipts.',
   'Accounts Office'),

  ('student', 'fee_status', 'Current term fee status — demo',
   'For demo student STU-1001 (Aarav Sharma, Grade 9): Term 1 (April 2025) — PAID ✅. Term 2 (August 2025) — PAID ✅. Term 3 (January 2026) — PENDING ⏳ (Due: 15 January 2026, Amount: ₹65,000).',
   'Accounts Office'),

  ('student', 'fee_status', 'Scholarship status',
   'Scholarship applications for 2025–26 are being processed. Results will be communicated by 30 June 2025 via email and the student portal. Students who applied for merit scholarship should check their portal under "My Applications".',
   'Accounts Office'),

  -- ================================================================
  -- STUDENT — ATTENDANCE (PERSONAL)
  -- ================================================================
  ('student', 'attendance', 'How to check personal attendance',
   'Personal attendance records are available on the student portal under "My Attendance". Records show subject-wise and overall attendance percentage updated daily by 6:00 PM. Parents can also view attendance via the parent login on the same portal.',
   'Academic Office'),

  ('student', 'attendance', 'Attendance shortage warning',
   'Students falling below 80% overall attendance receive an automated email and SMS alert to both student and parent. Students below 75% receive a formal warning letter. Students below 65% are required to meet the Vice Principal with their parents before the next exam.',
   'Academic Office'),

  ('student', 'attendance', 'Leave application — student process',
   'Submit leave applications via the student portal under "Apply for Leave" at least 2 days before planned absence. For medical leave, upload the doctor''s certificate within 3 days of return. Approved leave is reflected in the attendance record within 24 hours.',
   'Academic Office'),

  -- ================================================================
  -- STAFF — MEETINGS
  -- ================================================================
  ('staff', 'staff_meetings', 'Regular staff meetings',
   'Weekly staff briefing: Every Monday at 3:15 PM in the Main Staff Room (Block B, First Floor). Attendance is mandatory for all teaching staff. Minutes are circulated via the staff portal by Tuesday 10:00 AM.',
   'Admin'),

  ('staff', 'staff_meetings', 'Department meetings',
   'Department meetings are held on the last Friday of each month from 3:00–4:30 PM. Department heads must submit meeting minutes to the Vice Principal within 48 hours. Pending action items are reviewed at the next weekly briefing.',
   'Admin'),

  ('staff', 'staff_meetings', 'PTM preparation meeting',
   'A mandatory PTM preparation meeting is held 3 days before each Parent-Teacher Meeting. All class teachers and subject teachers of the respective classes must attend. Agenda includes: student performance review, attendance flags, and behavioural notes.',
   'Admin'),

  ('staff', 'staff_meetings', 'Emergency staff briefing protocol',
   'Emergency briefings are called by the Principal or Vice Principal via the staff WhatsApp group and email blast. All available staff must assemble in the auditorium within 10 minutes of notification. Duty teachers must ensure student supervision before leaving classrooms.',
   'Admin'),

  ('staff', 'staff_meetings', 'Examination coordination meeting',
   'Exam coordination meetings are held 2 weeks before each terminal exam. Attendees: Vice Principal, all subject heads, and exam committee members. Agenda: question paper submission deadlines, invigilation duty roster, hall allocation, and special needs arrangements.',
   'Exam Committee'),

  ('staff', 'staff_meetings', 'Professional development calendar',
   'Mandatory CPD sessions for 2025–26: (1) Classroom management workshop — 12 July 2025. (2) Digital tools in education — 23 August 2025. (3) NEP 2020 implementation update — 11 October 2025. (4) Assessment design — 17 January 2026. Attendance is recorded and forms part of the annual staff review.',
   'HR / Admin'),

  ('staff', 'staff_meetings', 'Appraisal and review process',
   'Annual staff appraisal cycle: Self-assessment submission by 28 February. Appraisal meeting with HOD/VP: first two weeks of March. Final appraisal letter issued by 31 March. Performance metrics include: attendance, student outcome data, peer feedback, and HOD evaluation.',
   'HR / Admin'),

  ('staff', 'staff_meetings', 'Leave and substitution policy for staff',
   'Staff are entitled to: 12 casual leaves, 10 medical leaves, and 30 earned leaves per academic year. Leave applications must be submitted on the staff portal at least 48 hours in advance (except emergencies). Medical leave beyond 3 days requires a doctor''s certificate. Unapproved absences are marked LWP (Leave Without Pay).',
   'HR / Admin'),

  -- ================================================================
  -- STAFF — TIMETABLE
  -- ================================================================
  ('staff', 'staff_timetable', 'How to access staff timetable',
   'Staff timetables are available on the staff portal at staff.demopublicschool.edu under "My Timetable". Log in with your staff ID and the password issued by the IT department. Timetables are updated at the start of each term. Contact the academic office for mid-term changes.',
   'Academic Office'),

  ('staff', 'staff_timetable', 'Substitute teacher protocol',
   'If a teacher is absent, notify the Vice Principal by 7:30 AM via phone and the staff portal. The duty teacher assigned for the day will cover the first period. Subsequent periods are covered per the substitute roster maintained by the academic office.',
   'Academic Office'),

  ('staff', 'staff_timetable', 'Free period responsibilities',
   'Staff free periods are not personal time. Teachers on free periods are expected to: (1) be available for student queries in the staffroom, (2) complete assessment work, or (3) cover for absent colleagues as directed by the VP. Free periods must not be spent outside school premises.',
   'Academic Office'),

  ('staff', 'staff_timetable', 'Extra duty and supervision roster',
   'Gate duty, lunch supervision, and exam invigilation rosters are published at the start of each month on the staff portal notice board. Staff must acknowledge their duty assignments within 48 hours. Swap requests must be approved by the VP at least 2 days in advance.',
   'Academic Office'),

  -- ================================================================
  -- STAFF — EMERGENCY
  -- ================================================================
  ('staff', 'emergency', 'Emergency contacts',
   'Security Desk (24/7): +91-98100-00010. School Doctor (on call): +91-98100-00011. Nearest hospital: City General Hospital, 1.2 km — Emergency: +91-11-2000-0001. Fire Station: +91-11-2000-0002 (4 km). Police: 100. Ambulance: 108.',
   'Admin'),

  ('staff', 'emergency', 'Fire evacuation procedure',
   'On fire alarm: (1) Stop all activity immediately. (2) Direct students to form a single-file line. (3) Exit via the nearest marked emergency exit — do NOT use elevators. (4) Assemble at the designated muster points: Block A staff/students → Football ground. Block B/C → Basketball court. (5) Take attendance and report to the designated area warden.',
   'Admin'),

  ('staff', 'emergency', 'Medical emergency protocol',
   'For a medical emergency: (1) Do not move the student if injury is suspected. (2) Call the infirmary nurse immediately at extension 201. (3) Call the school doctor on-call if nurse is unavailable. (4) Inform the VP and class teacher. (5) Contact parents immediately — parent contact details are in the staff portal under the student''s profile. (6) Complete an incident report form within 2 hours.',
   'Admin'),

  ('staff', 'emergency', 'Lockdown protocol',
   'Lockdown is announced via 3 short bell rings repeated twice. Action: (1) Lock or barricade the classroom door. (2) Move students away from windows and doors. (3) Silence all phones. (4) Do not open the door for anyone until the all-clear is given via PA system. (5) Take a headcount and report via WhatsApp group. Do NOT call the office as lines must be kept free.',
   'Admin'),

  ('staff', 'emergency', 'Child protection and safeguarding',
   'Any suspicion of abuse, neglect, or safeguarding concern must be reported immediately to the Designated Safeguarding Lead (DSL): Ms. Fatima Sheikh (counselor@demopublicschool.edu, +91-98100-00012). Do not investigate independently. Document observations factually and submit to DSL within the same working day.',
   'Admin')

) as v(access_level, category, title, content, source);

-- ──────────────────────────────────────────────────────────
-- 2. STUDENT FEES
-- ──────────────────────────────────────────────────────────
do $$
declare
  v_school_id uuid;
begin
  select id into v_school_id
  from public.schools
  where slug = 'demo-public-school'
  limit 1;

  if v_school_id is null then
    raise exception 'Demo school not found — run seed.sql from the top';
  end if;

  insert into public.student_fees (school_id, adm_no, total_fees, paid_amount, pending_amount, due_date)
  values (v_school_id, 'STU-1001', 120000.00, 80000.00, 40000.00, '2026-08-30')
  on conflict do nothing;
end $$;

-- ──────────────────────────────────────────────────────────
-- 3. ADMIN CREDENTIALS
--    Hash below = "admin1234" — CHANGE before going live
-- ──────────────────────────────────────────────────────────
insert into public.admin_credentials (school_id, username, password_hash, display_name)
select id, 'admin', '$2b$12$KIXSbvBBcSXsOtFRsHmNs.Q1lEpvGEo3z5JOEvZWM4T7gWcLEWlSy', 'School Administrator'
from public.schools
where slug = 'demo-public-school'
on conflict do nothing;

-- ──────────────────────────────────────────────────────────
-- 4. CLASSES, EXTRA USERS, STUDENT–CLASS LINKS, TIMETABLES
-- ──────────────────────────────────────────────────────────
do $$
declare
  v_school_id  uuid;
  v_class_9a   uuid;
  v_class_10b  uuid;
begin

  select id into v_school_id
  from public.schools
  where slug = 'demo-public-school'
  limit 1;

  if v_school_id is null then
    raise exception 'Demo school not found — run seed.sql from the top';
  end if;

  -- ── Classes ──────────────────────────────────────────────
  insert into public.classes (school_id, name, grade, section)
  values
    (v_school_id, '9A',  9,  'A'),
    (v_school_id, '10B', 10, 'B')
  on conflict (school_id, name) do nothing;

  select id into v_class_9a  from public.classes where school_id = v_school_id and name = '9A';
  select id into v_class_10b from public.classes where school_id = v_school_id and name = '10B';

  -- ── Extra users ───────────────────────────────────────────
  -- Aarav Sharma (STU-1001) already inserted above
  insert into public.users (school_id, role, name, adm_no)
  values (v_school_id, 'student', 'Priya Mehta', 'STU-1002')
  on conflict do nothing;

  insert into public.users (school_id, role, name, staff_id)
  values (v_school_id, 'staff', 'Mr. Kapoor', 'STAFF-9002')
  on conflict do nothing;

  -- ── Student–class links ───────────────────────────────────
  insert into public.student_classes (school_id, adm_no, class_id)
  values
    (v_school_id, 'STU-1001', v_class_9a),
    (v_school_id, 'STU-1002', v_class_10b)
  on conflict (school_id, adm_no) do nothing;

  -- ── Timetable — 9A ───────────────────────────────────────
  --  Period times:
  --    P1  08:00–08:45  P2  08:45–09:30  P3  09:30–10:15  P4  10:15–11:00
  --    Break (P5)  11:00–11:15
  --    P6  11:15–12:00  P7  12:00–12:45
  --    Lunch (P8) 12:45–14:00

  insert into public.timetable_slots
    (school_id, class_id, day, period_number, start_time, end_time, subject, teacher_staff_id, is_break)
  values
    -- MONDAY — 9A
    (v_school_id, v_class_9a, 'Monday', 1, '08:00', '08:45', 'Mathematics',        'STAFF-9001', false),
    (v_school_id, v_class_9a, 'Monday', 2, '08:45', '09:30', 'English',            'STAFF-9002', false),
    (v_school_id, v_class_9a, 'Monday', 3, '09:30', '10:15', 'Physics',            null,         false),
    (v_school_id, v_class_9a, 'Monday', 4, '10:15', '11:00', 'History',            null,         false),
    (v_school_id, v_class_9a, 'Monday', 5, '11:00', '11:15', 'Break',              null,         true ),
    (v_school_id, v_class_9a, 'Monday', 6, '11:15', '12:00', 'Hindi',              null,         false),
    (v_school_id, v_class_9a, 'Monday', 7, '12:00', '12:45', 'Physical Education', null,         false),
    (v_school_id, v_class_9a, 'Monday', 8, '12:45', '14:00', 'Lunch',              null,         true ),

    -- TUESDAY — 9A
    (v_school_id, v_class_9a, 'Tuesday', 1, '08:00', '08:45', 'Chemistry',         null,         false),
    (v_school_id, v_class_9a, 'Tuesday', 2, '08:45', '09:30', 'Mathematics',       'STAFF-9001', false),
    (v_school_id, v_class_9a, 'Tuesday', 3, '09:30', '10:15', 'English',           'STAFF-9002', false),
    (v_school_id, v_class_9a, 'Tuesday', 4, '10:15', '11:00', 'Geography',         null,         false),
    (v_school_id, v_class_9a, 'Tuesday', 5, '11:00', '11:15', 'Break',             null,         true ),
    (v_school_id, v_class_9a, 'Tuesday', 6, '11:15', '12:00', 'Computer Science',  null,         false),
    (v_school_id, v_class_9a, 'Tuesday', 7, '12:00', '12:45', 'Biology',           null,         false),
    (v_school_id, v_class_9a, 'Tuesday', 8, '12:45', '14:00', 'Lunch',             null,         true ),

    -- WEDNESDAY — 9A
    (v_school_id, v_class_9a, 'Wednesday', 1, '08:00', '08:45', 'Biology',          null,         false),
    (v_school_id, v_class_9a, 'Wednesday', 2, '08:45', '09:30', 'Hindi',            null,         false),
    (v_school_id, v_class_9a, 'Wednesday', 3, '09:30', '10:15', 'Mathematics',      'STAFF-9001', false),
    (v_school_id, v_class_9a, 'Wednesday', 4, '10:15', '11:00', 'Physics Lab',      null,         false),
    (v_school_id, v_class_9a, 'Wednesday', 5, '11:00', '11:15', 'Break',            null,         true ),
    (v_school_id, v_class_9a, 'Wednesday', 6, '11:15', '12:00', 'English',          'STAFF-9002', false),
    (v_school_id, v_class_9a, 'Wednesday', 7, '12:00', '12:45', 'Art',              null,         false),
    (v_school_id, v_class_9a, 'Wednesday', 8, '12:45', '14:00', 'Lunch',            null,         true ),

    -- THURSDAY — 9A
    (v_school_id, v_class_9a, 'Thursday', 1, '08:00', '08:45', 'English',           'STAFF-9002', false),
    (v_school_id, v_class_9a, 'Thursday', 2, '08:45', '09:30', 'Chemistry Lab',     null,         false),
    (v_school_id, v_class_9a, 'Thursday', 3, '09:30', '10:15', 'History',           null,         false),
    (v_school_id, v_class_9a, 'Thursday', 4, '10:15', '11:00', 'Mathematics',       'STAFF-9001', false),
    (v_school_id, v_class_9a, 'Thursday', 5, '11:00', '11:15', 'Break',             null,         true ),
    (v_school_id, v_class_9a, 'Thursday', 6, '11:15', '12:00', 'Biology',           null,         false),
    (v_school_id, v_class_9a, 'Thursday', 7, '12:00', '12:45', 'Geography',         null,         false),
    (v_school_id, v_class_9a, 'Thursday', 8, '12:45', '14:00', 'Lunch',             null,         true ),

    -- FRIDAY — 9A
    (v_school_id, v_class_9a, 'Friday', 1, '08:00', '08:45', 'Physical Education',  null,         false),
    (v_school_id, v_class_9a, 'Friday', 2, '08:45', '09:30', 'Biology',             null,         false),
    (v_school_id, v_class_9a, 'Friday', 3, '09:30', '10:15', 'Hindi',               null,         false),
    (v_school_id, v_class_9a, 'Friday', 4, '10:15', '11:00', 'Computer Science',    null,         false),
    (v_school_id, v_class_9a, 'Friday', 5, '11:00', '11:15', 'Break',               null,         true ),
    (v_school_id, v_class_9a, 'Friday', 6, '11:15', '12:00', 'Mathematics',         'STAFF-9001', false),
    (v_school_id, v_class_9a, 'Friday', 7, '12:00', '12:45', 'English',             'STAFF-9002', false),
    (v_school_id, v_class_9a, 'Friday', 8, '12:45', '14:00', 'Lunch',               null,         true ),

    -- MONDAY — 10B
    (v_school_id, v_class_10b, 'Monday', 1, '08:00', '08:45', 'Mathematics',        'STAFF-9001', false),
    (v_school_id, v_class_10b, 'Monday', 2, '08:45', '09:30', 'English',            'STAFF-9002', false),
    (v_school_id, v_class_10b, 'Monday', 3, '09:30', '10:15', 'Chemistry',          null,         false),
    (v_school_id, v_class_10b, 'Monday', 4, '10:15', '11:00', 'Physics',            null,         false),
    (v_school_id, v_class_10b, 'Monday', 5, '11:00', '11:15', 'Break',              null,         true ),
    (v_school_id, v_class_10b, 'Monday', 6, '11:15', '12:00', 'Hindi',              null,         false),
    (v_school_id, v_class_10b, 'Monday', 7, '12:00', '12:45', 'Biology',            null,         false),
    (v_school_id, v_class_10b, 'Monday', 8, '12:45', '14:00', 'Lunch',              null,         true ),

    -- TUESDAY — 10B
    (v_school_id, v_class_10b, 'Tuesday', 1, '08:00', '08:45', 'Biology',           null,         false),
    (v_school_id, v_class_10b, 'Tuesday', 2, '08:45', '09:30', 'Mathematics',       'STAFF-9001', false),
    (v_school_id, v_class_10b, 'Tuesday', 3, '09:30', '10:15', 'English',           'STAFF-9002', false),
    (v_school_id, v_class_10b, 'Tuesday', 4, '10:15', '11:00', 'History',           null,         false),
    (v_school_id, v_class_10b, 'Tuesday', 5, '11:00', '11:15', 'Break',             null,         true ),
    (v_school_id, v_class_10b, 'Tuesday', 6, '11:15', '12:00', 'Physical Education',null,         false),
    (v_school_id, v_class_10b, 'Tuesday', 7, '12:00', '12:45', 'Geography',         null,         false),
    (v_school_id, v_class_10b, 'Tuesday', 8, '12:45', '14:00', 'Lunch',             null,         true ),

    -- WEDNESDAY — 10B
    (v_school_id, v_class_10b, 'Wednesday', 1, '08:00', '08:45', 'Chemistry Lab',   null,         false),
    (v_school_id, v_class_10b, 'Wednesday', 2, '08:45', '09:30', 'Hindi',           null,         false),
    (v_school_id, v_class_10b, 'Wednesday', 3, '09:30', '10:15', 'Mathematics',     'STAFF-9001', false),
    (v_school_id, v_class_10b, 'Wednesday', 4, '10:15', '11:00', 'Geography',       null,         false),
    (v_school_id, v_class_10b, 'Wednesday', 5, '11:00', '11:15', 'Break',           null,         true ),
    (v_school_id, v_class_10b, 'Wednesday', 6, '11:15', '12:00', 'Computer Science',null,         false),
    (v_school_id, v_class_10b, 'Wednesday', 7, '12:00', '12:45', 'English',         'STAFF-9002', false),
    (v_school_id, v_class_10b, 'Wednesday', 8, '12:45', '14:00', 'Lunch',           null,         true ),

    -- THURSDAY — 10B
    (v_school_id, v_class_10b, 'Thursday', 1, '08:00', '08:45', 'Physics Lab',      null,         false),
    (v_school_id, v_class_10b, 'Thursday', 2, '08:45', '09:30', 'English',          'STAFF-9002', false),
    (v_school_id, v_class_10b, 'Thursday', 3, '09:30', '10:15', 'Mathematics',      'STAFF-9001', false),
    (v_school_id, v_class_10b, 'Thursday', 4, '10:15', '11:00', 'Biology',          null,         false),
    (v_school_id, v_class_10b, 'Thursday', 5, '11:00', '11:15', 'Break',            null,         true ),
    (v_school_id, v_class_10b, 'Thursday', 6, '11:15', '12:00', 'Art',              null,         false),
    (v_school_id, v_class_10b, 'Thursday', 7, '12:00', '12:45', 'History',          null,         false),
    (v_school_id, v_class_10b, 'Thursday', 8, '12:45', '14:00', 'Lunch',            null,         true ),

    -- FRIDAY — 10B
    (v_school_id, v_class_10b, 'Friday', 1, '08:00', '08:45', 'Computer Science',   null,         false),
    (v_school_id, v_class_10b, 'Friday', 2, '08:45', '09:30', 'Hindi',              null,         false),
    (v_school_id, v_class_10b, 'Friday', 3, '09:30', '10:15', 'Biology',            null,         false),
    (v_school_id, v_class_10b, 'Friday', 4, '10:15', '11:00', 'English',            'STAFF-9002', false),
    (v_school_id, v_class_10b, 'Friday', 5, '11:00', '11:15', 'Break',              null,         true ),
    (v_school_id, v_class_10b, 'Friday', 6, '11:15', '12:00', 'Mathematics',        'STAFF-9001', false),
    (v_school_id, v_class_10b, 'Friday', 7, '12:00', '12:45', 'Physical Education', null,         false),
    (v_school_id, v_class_10b, 'Friday', 8, '12:45', '14:00', 'Lunch',              null,         true );

end $$;

-- ──────────────────────────────────────────────────────────
-- SUMMARY
-- ──────────────────────────────────────────────────────────
select
  'Seed complete' as status,
  (select count(*) from public.knowledge_items) as knowledge_items,
  (select count(*) from public.timetable_slots) as timetable_slots,
  (select count(*) from public.classes)         as classes,
  (select count(*) from public.student_classes) as student_class_links,
  (select count(*) from public.student_fees)    as fee_records,
  (select count(*) from public.admin_credentials) as admin_accounts;
