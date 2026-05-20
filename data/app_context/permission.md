# Roles & Permissions

## Platform Roles

### Student
- Views courses assigned to their class and public courses.
- Browses course content (text, PDF, video, links).
- Takes stable tests from courses.
- Generates personalized tests based on selected course content.
- Views own progress and test history.
- Cannot create courses, tests, or classes.
- Cannot view other students' progress.

### Teacher
- Creates and edits their own courses.
- Adds content to courses: chapters, resources (text, PDF, video, link), tests.
- Generates tests with AI based on course content.
- Publishes and archives courses.
- Assigns courses to classes (within the scope set by the admin).
- Views progress of students in their courses.
- Cannot create user accounts.
- Cannot create or edit classes.
- Cannot see other teachers' courses unless they are public.

### Organization Admin (ORG_ADMIN)
- Creates student and teacher accounts (individually or via bulk CSV import).
- Activates and deactivates accounts.
- Creates and manages classes.
- Adds and removes students from classes.
- Sets teacher assignment scope: ALL_CLASSES or SELECTED_CLASSES.
- Edits organization info (name, type, country, city).
- Views progress of any student in the organization.
- Manages the organization's subscription.
- Cannot access or edit other organizations.

### Platform Admin (PLATFORM_ADMIN)
- Full access across all organizations and users.
- Can create users with any role, including ORG_ADMIN and PLATFORM_ADMIN.
- Can deactivate any account.

## Granting or Revoking Teacher Permissions

### Changing assignment scope
- Admin goes to User Management.
- Selects the teacher and edits their assignment scope.
- ALL_CLASSES: teacher can assign courses to any class in the organization.
- SELECTED_CLASSES: teacher can only assign courses to the classes selected by the admin.

### Deactivating a teacher account
- Admin goes to User Management, finds the teacher, and deactivates the account.
- A deactivated account cannot log in.
- Courses created by the teacher remain on the platform.

### Reactivating an account
- Admin goes to User Management, filters by status INACTIVE, and reactivates the account.

## Common Permission Questions

- "Why can't I create a test?" — Only teachers can create tests. Students do not have this option.
- "Why can't I see course X?" — The course must be PUBLISHED and assigned to your class, or set to PUBLIC.
- "Why can't I assign my course to class Y?" — You likely have SELECTED_CLASSES scope and class Y is not in your allowed list. Contact your admin.
- "Why can't I add students to a class?" — Only admins can manage class membership.
- "How do I become a teacher?" — Teacher accounts are created by the organization admin, there is no self-registration for teachers.
