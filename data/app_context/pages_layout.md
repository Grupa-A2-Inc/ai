# Pages Layout by User Role

## Public (Unauthenticated)

### Landing Page `/`
- Hero, How It Works, Benefits by Role, Core Features, FAQ, Footer
- Actions: go to Login, go to Register

### Login `/login`
- Email + password form
- Links: Register, Forgot Password
- On success: redirect to role-specific dashboard

### Register `/register`
- Creates a new organization + admin account simultaneously
- Fields: admin name/email/password, organization name/country/city/type
- On success: redirect to Admin Dashboard

### Forgot Password `/forgot-password`
- Email input to request reset link

### Reset Password `/reset-password`
- New password form (via email link)

### Set Password `/set-password`
- First-time password setup for newly created accounts

---

## STUDENT — main entry: `/dashboard/student`

### Main Page — Courses `/dashboard/student`
Redirected here after login. Tabs:
- **Assigned** — courses assigned to student's class
- **Public** — open to everyone
- **Archived/Completed** — finished courses
- Search and filter available

### Course Study Page `/dashboard/student/courses/[courseId]`
- Course metadata + progress summary
- Content tree panel (sections + resources)
- Content viewer (text, PDF, video, link)
- Stable tests accessible from content tree
- "Add to test" selection for personalized test generation
- Navigate to: Test Generation, Test Runner, Progress

### Course Stats `/dashboard/student/courses/[courseId]/stats`
- Detailed progress for this course
- Content completion %, stable tests completed, average score, AI tests taken
- Attempt history list → open past attempt

### Course Tests `/dashboard/student/courses/[courseId]/tests`
- List of stable tests in this course

### Lesson `/dashboard/student/courses/[courseId]/lessons/[lessonId]`
- Individual lesson/resource viewer

### Tests List `/dashboard/student/tests`
- All tests available to the student

### Test Runner `/dashboard/student/tests/[testId]/take`
- One question at a time
- Answer selection + navigation between questions
- Optional timer
- Submit at the end

### Test Results `/dashboard/student/tests/[testId]/results`
- Score summary
- Per-question review: student answer vs correct answer
- Report question button (AI-generated tests only)

### Test History `/dashboard/student/tests/[testId]/history`
- Past attempts for this test

### Adaptive Test `/dashboard/student/adaptive`
- AI-adaptive exercise session

### Adaptive Test Runner `/dashboard/student/adaptive/test`
- Adaptive question flow

### Adaptive Results `/dashboard/student/adaptive/results`
- Results of adaptive session

### My Progress `/dashboard/student/progress`
- Summary stats: active courses, completed courses, total tests taken
- List of courses with progress → navigate to Course Stats

### Profile `/dashboard/student/profile`
- View/edit own name and profile picture
- Change password
- Mini stats: courses completed, tests taken

---

## TEACHER — main entry: `/dashboard/teacher`

### Main Page — My Courses `/dashboard/teacher`
Redirected here after login.
- List of own courses (title, status, visibility, last modified)
- Create new course
- Search and filter

### Course Management `/dashboard/teacher/courses/[courseId]`
Two tabs:
- **Content** — course metadata, content tree, stable tests
- **Students** — students enrolled (grouped by class), assignment controls
- Navigate to: Course Editor, Test Editor

### Course Editor `/dashboard/teacher/courses/[courseId]/edit`
- Edit course title, description, visibility
- Build/edit content tree: add/reorder/delete sections and resources (text, PDF, video, link)
- Add test nodes to the content tree

### New Course `/dashboard/teacher/courses/new`
- Create course form (title, description, visibility)

### Test Builder `/dashboard/teacher/courses/[courseId]/test-builder`
- Select course content nodes as source
- Set number of questions
- AI generates test draft
- Review, edit, regenerate questions
- Save as stable test in the course

### Test View `/dashboard/teacher/courses/[courseId]/tests/[testId]`
- View/edit a specific stable test

### Course Analytics `/dashboard/teacher/courses/[courseId]/analytics`
- Student performance analytics for this course

### Course Students `/dashboard/teacher/courses/[courseId]/students`
- Students enrolled in this course grouped by class
- Assignment controls (assign/unassign classes)

### Tests Overview `/dashboard/teacher/tests`
- All tests created by this teacher

### Students Overview `/dashboard/teacher/students`
- Students in courses taught by this teacher

### Profile `/dashboard/teacher/profile`
- View/edit own name and profile picture
- Change password
- Mini stats: courses created, tests created

---

## ORG_ADMIN — main entry: `/dashboard/admin`

### Main Page — Admin Dashboard `/dashboard/admin`
Redirected here after login.
- KPIs: total students, teachers, classes, courses
- Organization info (editable inline: name, type, country, city, address, phone)
- Quick links to User Management and Class Management
- Subscription info

### User Management `/dashboard/admin/users`
- Table of all users (students + teachers), filterable by role and status
- Search by name or email
- Create individual student/teacher account
- Bulk import via CSV
- Edit user details
- Activate / deactivate accounts
- Set teacher assignment scope: ALL_CLASSES or SELECTED_CLASSES
- If SELECTED_CLASSES: select allowed classes for that teacher

### Classes Page `/dashboard/admin/classes`
- List of all classes in the organization
- Create new class (name, academic year, description, optional teachers)
- Navigate to Class Management for each class

### Class Management `/dashboard/admin/classes/[classId]`
- Edit class details (name, academic year, description)
- View student list
- Add available students to class
- Remove students from class

### Courses Overview `/dashboard/admin/courses`
- View all courses in the organization

### Settings `/dashboard/admin/settings`
- Organization-level settings

### Profile `/dashboard/admin/profile`
- View/edit own name and profile picture
- Change password

---

## PLATFORM_ADMIN

Same layout as ORG_ADMIN but with cross-organization access.
- Can create users with any role including ORG_ADMIN and PLATFORM_ADMIN
- Dashboard shows platform-wide counts across all organizations

---

## Shared Layout — Dashboard `/dashboard/layout`

All authenticated users share a common dashboard shell:
- **Sidebar** with role-specific navigation links
- **Navbar** with profile menu, theme toggle
- **Customer Support Chat** widget (AI-powered, available to all roles)
- Role-based redirect on login:
  - STUDENT → `/dashboard/student`
  - TEACHER → `/dashboard/teacher`
  - ORG_ADMIN / PLATFORM_ADMIN → `/dashboard/admin`
