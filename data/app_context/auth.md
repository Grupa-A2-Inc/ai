# Authentication & Account

## Login
- Users log in with email and password.
- On success, the server returns a JWT access token and user info (including role).
- After login, users are redirected to their role-specific dashboard: admin, teacher, or student.
- If credentials are wrong, an error is shown on the page.

## Register (Organization)
- Register creates a new organization AND the main admin account for it simultaneously.
- It is NOT a simple individual user registration.
- Teachers and students do NOT self-register — their accounts are created by the admin.
- Required fields: admin first name, last name, email, password, organization name, country, city, organization type.
- Optional fields: address, phone number.
- After successful registration, the user is logged in as admin and redirected to the Admin Dashboard.

## Forgot Password / Reset Password
- Users can request a password reset from the forgot password page.
- A reset link is sent to their email.
- The reset password page allows setting a new password using the link received.
- The set password page is used for first-time password setup (e.g. newly created accounts).

## Profile
- Users can view and edit their own profile (first name, last name, profile picture).
- Email is read-only and cannot be changed.
- Users can change their password by providing the current password and a new one.
- Admins can also edit other users' profiles.

## Roles
- STUDENT: accesses assigned and public courses, takes tests, views own progress.
- TEACHER: creates and manages courses, manages class assignments, views student progress.
- ORG_ADMIN: manages users (students and teachers) and classes within their organization.
- PLATFORM_ADMIN: full platform access.

## Common Issues
- Can't log in: check email and password, make sure the account is ACTIVE.
- Account inactive: contact your organization admin or platform support.
- Forgot password: use the "Forgot password" link on the login page to receive a reset email.
- First login with temporary password: use the set password page to set a permanent password.
- Teachers and students cannot register themselves — accounts are created by the organization admin.
