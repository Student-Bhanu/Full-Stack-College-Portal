use college_db;

-- Teacher Data
INSERT INTO teacher (username, password, name, email, department) VALUES
('manoj_cse', 'pass123', 'Prof. Manoj Kumar', 'mkumarg@dce.ac.in', 'Computer Science & Engineering'),
('dinesh_it', 'pass123', 'Prof. Dinesh K. Vishwakarma', 'dinesh@dtu.ac.in', 'Information Technology'),
('ruchika_se', 'pass123', 'Prof. Ruchika Malhotra', 'ruchikamalhotra@dtu.ac.in', 'Software Engineering'),
('neeta_ece', 'pass123', 'Prof. Neeta Pandey', 'neetapandey@dce.ac.in', 'Electronics and Communication Engineering'),
('bbarora_me', 'pass123', 'Prof. B B Arora', 'bbarora@dce.ac.in', 'Mechanical & Production Engineering'),
('rachna_ee', 'pass123', 'Prof. Rachna Garg', 'rachnagarg@dtu.ac.in', 'Electrical Engineering'),
('kc_civil', 'pass123', 'Prof. K C Tiwari', 'hod.ce@dtu.ac.in', 'Civil Engineering'),
('haritash_env', 'pass123', 'Anil Kumar Haritash', 'akharitash@dce.ac.in', 'Environmental Engineering'),
('yasha_bt', 'pass123', 'Prof. Yasha Hasija', 'yashahasija@dtu.ac.in', 'Bio Technology'),
('vinod_phy', 'pass123', 'Prof. Vinod Singh', 'vinodsingh@dtu.ac.in', 'Applied Physics'),
('srivastava_math', 'pass123', 'Prof. R. Srivastava', 'rsrivastava@dce.ac.in', 'Applied Mathematics'),
('anil_chem', 'pass123', 'Dr. Anil Kumar', 'anil_kumar@dce.ac.in', 'Applied Chemistry');


-- Student Data 
INSERT INTO student (username, password, name, email, roll_number, semester, department) VALUES
('aaditya001','pass123','AADITYA JAIN','aaditya001@dtu.ac.in','24/B04/001',3,'Computer Science & Engineering'),
('aarush002','pass123','AARUSH BHARADWAJ','aarush002@dtu.ac.in','24/B04/002',3,'Information Technology'),
('aarushi003','pass123','AARUSHI SINGH','aarushi003@dtu.ac.in','24/B04/003',3,'Software Engineering'),
('abhijai005','pass123','ABHIJAI DAGAR','abhijai005@dtu.ac.in','24/B04/005',3,'Civil Engineering'),
('abhijeet006','pass123','ABHIJEET SINHA','abhijeet006@dtu.ac.in','24/B04/006',3,'Electrical Engineering'),
('abhishek009','pass123','ABHISHEK SINGH','abhishek009@dtu.ac.in','24/B04/009',1,'Mechanical Engineering'),
('adarsh010','pass123','ADARSH','adarsh010@dtu.ac.in','24/B04/010',1,'Electronics & Communication Engineering'),
('aditya011','pass123','ADITYA GUPTA','aditya011@dtu.ac.in','24/B04/011',1,'Applied Mathematics'),
('aditya012','pass123','ADITYA RAJ','aditya012@dtu.ac.in','24/B04/012',1,'Applied Physics'),
('adityas013','pass123','ADITYA S NAIR','adityas013@dtu.ac.in','24/A11/018',1,'Environmental Engineering'),

('afzal014','pass123','AFZAL','afzal014@dtu.ac.in','24/B04/014',1,'Bio Technology'),
('akshansh016','pass123','AKSHANSH','akshansh016@dtu.ac.in','24/B04/016',1,'Humanities'),
('akshat017','pass123','AKSHAT JAIN','akshat017@dtu.ac.in','24/B04/017',1,'Applied Chemistry'),
('akshay018','pass123','AKSHAY','akshay018@dtu.ac.in','24/B04/018',1,'Design'),
('akshayk019','pass123','AKSHAY KAUSHAL','akshayk019@dtu.ac.in','24/B04/019',1,'Computer Centre'),

('ali021','pass123','ALI KHAN','ali021@dtu.ac.in','24/B04/021',1,'Information Technology'),
('amit022','pass123','AMIT KUMAR','amit022@dtu.ac.in','24/B04/022',1,'Software Engineering'),
('amlan023','pass123','AMLAN NANDI','amlan023@dtu.ac.in','24/B04/023',1,'Mechanical Engineering'),
('ankit024','pass123','ANKIT','ankit024@dtu.ac.in','24/B04/024',1,'Civil Engineering'),
('ankitp025','pass123','ANKIT PANDEY','ankitp025@dtu.ac.in','24/B04/025',1,'Computer Science & Engineering');

-- Course Data
INSERT INTO course (course_code, course_name, department, credits, semester) VALUES 
-- Computer Science Courses
('CO201', 'Data Structures', 'Computer Science', 4, 2),
('CO202', 'Database Management Systems', 'Computer Science', 4, 2),
('CO203', 'Object Oriented Programming', 'Computer Science', 4, 2),
('CO204', 'Operating Systems Design', 'Computer Science', 4, 4),
('CO208', 'Algorithm Design & Analysis', 'Computer Science', 4, 4),
('CO301', 'Software Engineering', 'Computer Science', 4, 6),
('CO304', 'Artificial Intelligence', 'Computer Science', 4, 6),
('CO306', 'Computer Networks', 'Computer Science', 4, 6),
('CO327', 'Machine Learning', 'Computer Science', 4, 6),
('CO313', 'Computer Graphics', 'Computer Science', 4, 5),

-- Software Engineering Courses
('SE201', 'Data Structures', 'Software Engineering', 4, 2),
('SE202', 'Object Oriented Software Engineering', 'Software Engineering', 4, 2),
('SE206', 'Database Management Systems', 'Software Engineering', 4, 2),
('SE207', 'Software Engineering', 'Software Engineering', 4, 4),
('SE301', 'Software Testing', 'Software Engineering', 4, 4),
('SE302', 'Empirical Software Engineering', 'Software Engineering', 4, 6),
('SE406', 'Advances in Software Engineering', 'Software Engineering', 4, 6),
('SE326', 'Machine Learning', 'Software Engineering', 4, 6),

-- Information Technology Courses
('IT201', 'Data Structures', 'Information Technology', 4, 2),
('IT204', 'Operating System', 'Information Technology', 4, 2),
('IT208', 'Algorithm Design and Analysis', 'Information Technology', 4, 2),
('IT303', 'Computer Networks', 'Information Technology', 4, 4),
('IT304', 'Software Engineering', 'Information Technology', 4, 4),
('IT351', 'Artificial Intelligence and Machine Learning', 'Information Technology', 4, 6),
('IT404', 'Big Data Analytics', 'Information Technology', 4, 6),
('IT407', 'Information and Network Security', 'Information Technology', 4, 6),

-- Electronics Courses
('EC201', 'Analog Electronics-I', 'Electronics', 4, 2),
('EC203', 'Digital Design-I', 'Electronics', 4, 2),
('EC205', 'Signal and Systems', 'Electronics', 4, 2),
('EC302', 'VLSI Design', 'Electronics', 4, 4),
('EC304', 'Digital Signal Processing', 'Electronics', 4, 4),
('EC306', 'Embedded Systems', 'Electronics', 4, 6),
('EC330', 'Digital Image Processing', 'Electronics', 4, 6),
('EC409', 'Computer Vision', 'Electronics', 4, 6),

-- Mechanical Courses
('ME201', 'Mechanics of Solids', 'Mechanical', 4, 2),
('ME208', 'Manufacturing Technology-I', 'Mechanical', 4, 2),
('ME302', 'Heat and Mass Transfer', 'Mechanical', 4, 4),
('ME307', 'Manufacturing Technology-II', 'Mechanical', 4, 4),
('ME305', 'Design of Machine Elements', 'Mechanical', 4, 6),
('ME316', 'Power Plant Engineering', 'Mechanical', 4, 6),
('ME411', 'I C Engines', 'Mechanical', 4, 6),

-- Civil Courses
('CE202', 'Mechanics of Solid', 'Civil', 4, 2),
('CE206', 'Soil Mechanics', 'Civil', 4, 2),
('CE207', 'Engineering Analysis and Design', 'Civil', 4, 2),
('CE301', 'Analysis of Determinate Structure', 'Civil', 4, 4),
('CE304', 'Geotechnical Engineering', 'Civil', 4, 4),
('CE303', 'Design of RCC Structure', 'Civil', 4, 6),
('CE306', 'Transportation Engineering', 'Civil', 4, 6),
('CE308', 'Disaster Management', 'Civil', 4, 6),

-- Mathematics Courses
('MC205', 'Probability and Statistics', 'Mathematics', 4, 2),
('MC207', 'Engineering Analysis & Design', 'Mathematics', 4, 2),
('MC208', 'Linear Algebra', 'Mathematics', 4, 2);

-- Teacher-Course Mapping
INSERT INTO teacher_course (teacher_id, course_id) VALUES 
(1, 3), (1, 5), 
(2, 6), (2, 7),
(3, 11), (3, 14),
(4, 18), (4, 20),
(5, 23), (5, 26),
(6, 2), (6, 4),
(7, 27), (7, 28),
(8, 12), (8, 13);

-- Student-Course Mapping (enrolling students in their semester courses)
INSERT INTO student_course (student_id, course_id, enrollment_date) VALUES
(1, 6, '2024-08-01'), (1, 7, '2024-08-01'),
(2, 6, '2024-08-01'), (2, 7, '2024-08-01'),
(3, 4, '2024-08-01'), (3, 3, '2024-08-01'),
(4, 4, '2024-08-01'), (4, 3, '2024-08-01'),
(5, 2, '2024-08-01'), (5, 28, '2024-08-01'),
(6, 2, '2024-08-01'), (6, 28, '2024-08-01'),
(13, 2, '2024-08-01'), (13, 28, '2024-08-01'),
(7, 14, '2024-08-01'), (7, 13, '2024-08-01'),
(8, 12, '2024-08-01'), (8, 11, '2024-08-01'),
(14, 10, '2024-08-01'), (14, 28, '2024-08-01'),
(9, 20, '2024-08-01'), (9, 19, '2024-08-01'),
(10, 18, '2024-08-01'), (10, 17, '2024-08-01'),
(15, 16, '2024-08-01'), (15, 28, '2024-08-01'),
(11, 26, '2024-08-01'), (11, 25, '2024-08-01'),
(12, 24, '2024-08-01'), (12, 23, '2024-08-01');

-- Attendance Data (Recent attendance for November 2024)
INSERT INTO attendance (student_id, course_id, teacher_id, attendance_date, status) VALUES 
(1, 6, 2, '2024-11-01', 'Present'),
(2, 6, 2, '2024-11-01', 'Present'),
(1, 6, 2, '2024-11-04', 'Present'),
(2, 6, 2, '2024-11-04', 'Absent'),
(1, 6, 2, '2024-11-08', 'Present'),
(2, 6, 2, '2024-11-08', 'Present'),
(1, 6, 2, '2024-11-11', 'Absent'),
(2, 6, 2, '2024-11-11', 'Present'),
(1, 7, 2, '2024-11-02', 'Present'),
(2, 7, 2, '2024-11-02', 'Present'),
(1, 7, 2, '2024-11-05', 'Present'),
(2, 7, 2, '2024-11-05', 'Present'),
(3, 3, 1, '2024-11-01', 'Present'),
(4, 3, 1, '2024-11-01', 'Present'),
(3, 3, 1, '2024-11-06', 'Absent'),
(4, 3, 1, '2024-11-06', 'Present'),
(5, 2, 6, '2024-11-03', 'Present'),
(6, 2, 6, '2024-11-03', 'Present'),
(13, 2, 6, '2024-11-03', 'Present'),
(5, 2, 6, '2024-11-07', 'Present'),
(6, 2, 6, '2024-11-07', 'Absent'),
(13, 2, 6, '2024-11-07', 'Present');

-- Assignment Data
INSERT INTO assignment (course_id, teacher_id, title, description, due_date) VALUES 
(6, 2, 'Software Development Life Cycle Analysis', 'Analyze and compare different SDLC models with real-world examples', '2024-11-20'),
(7, 2, 'Linear Regression Implementation', 'Implement linear regression from scratch using Python/NumPy', '2024-11-25'),
(3, 1, 'Database Normalization Project', 'Design and normalize a database for an e-commerce system', '2024-11-18'),
(2, 6, 'Binary Search Tree Operations', 'Implement insertion, deletion, and traversal in BST', '2024-11-22'),
(14, 3, 'Embedded System Design', 'Design a temperature monitoring system using Arduino', '2024-11-28'),
(20, 4, 'Heat Exchanger Design', 'Calculate heat transfer coefficients for shell and tube heat exchanger', '2024-11-24'),
(26, 5, 'Water Treatment Plant Design', 'Design a basic water treatment plant for a small town', '2024-11-30');

-- Assignment Submission Data
INSERT INTO assignment_submission (assignment_id, student_id, file_path, submitted_at, status, grade, max_grade, feedback, graded_by, graded_at) VALUES 
(1, 1, '/uploads/assignments/rahul_sdlc_analysis.pdf', '2024-11-18 14:30:00', 'Graded', 42.50, 50.00, 'Excellent analysis of Agile and Waterfall models. Good use of examples.', 2, '2024-11-19 10:00:00'),
(1, 2, '/uploads/assignments/pooja_sdlc_analysis.pdf', '2024-11-19 23:45:00', 'Graded', 38.00, 50.00, 'Good work but comparison could be more detailed.', 2, '2024-11-20 11:30:00'),
(2, 1, '/uploads/assignments/rahul_linear_regression.py', '2024-11-20 10:15:00', 'Submitted', NULL, 50.00, NULL, NULL, NULL),
(3, 3, '/uploads/assignments/arjun_db_normalization.pdf', '2024-11-17 16:20:00', 'Graded', 45.00, 50.00, 'Very well done! Clear understanding of 3NF and BCNF.', 1, '2024-11-18 09:00:00'),
(3, 4, '/uploads/assignments/sneha_db_normalization.pdf', '2024-11-18 09:30:00', 'Graded', 47.50, 50.00, 'Outstanding work with comprehensive ER diagram.', 1, '2024-11-18 14:00:00'),
(4, 5, '/uploads/assignments/karan_bst.cpp', '2024-11-21 18:00:00', 'Submitted', NULL, 50.00, NULL, NULL, NULL),
(4, 6, '/uploads/assignments/ananya_bst.cpp', '2024-11-22 08:30:00', 'Submitted', NULL, 50.00, NULL, NULL, NULL);

-- Exam Score Data
INSERT INTO exam_score (student_id, course_id, semester, exam_type, score, max_score, exam_date) VALUES 
-- Semester 6 Students
(1, 6, 6, 'Mid-Term', 78.50, 100.00, '2024-10-15'),
(1, 7, 6, 'Mid-Term', 82.00, 100.00, '2024-10-18'),
(2, 6, 6, 'Mid-Term', 72.00, 100.00, '2024-10-15'),
(2, 7, 6, 'Mid-Term', 85.50, 100.00, '2024-10-18'),
-- Semester 4 Students
(3, 3, 4, 'Mid-Term', 88.00, 100.00, '2024-10-12'),
(3, 4, 4, 'Mid-Term', 76.50, 100.00, '2024-10-14'),
(4, 3, 4, 'Mid-Term', 91.50, 100.00, '2024-10-12'),
(4, 4, 4, 'Mid-Term', 79.00, 100.00, '2024-10-14'),
-- Semester 2 Students
(5, 2, 2, 'Mid-Term', 68.00, 100.00, '2024-10-10'),
(5, 28, 2, 'Mid-Term', 74.50, 100.00, '2024-10-16'),
(6, 2, 2, 'Mid-Term', 81.00, 100.00, '2024-10-10'),
(6, 28, 2, 'Mid-Term', 77.00, 100.00, '2024-10-16'),
(13, 2, 2, 'Mid-Term', 73.50, 100.00, '2024-10-10'),
-- Electronics Students
(7, 14, 6, 'Mid-Term', 84.00, 100.00, '2024-10-17'),
(8, 12, 4, 'Mid-Term', 79.50, 100.00, '2024-10-13'),
(14, 10, 2, 'Mid-Term', 70.00, 100.00, '2024-10-11'),
-- Mechanical Students
(9, 20, 6, 'Mid-Term', 75.50, 100.00, '2024-10-19'),
(10, 18, 4, 'Mid-Term', 82.00, 100.00, '2024-10-15'),
(15, 16, 2, 'Mid-Term', 67.00, 100.00, '2024-10-12'),
-- Civil Students
(11, 26, 6, 'Mid-Term', 80.00, 100.00, '2024-10-20'),
(12, 24, 4, 'Mid-Term', 86.50, 100.00, '2024-10-16');