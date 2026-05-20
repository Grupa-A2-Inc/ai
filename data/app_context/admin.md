# Admin

## Admin Dashboard
- The admin's main page after login.
- Shows KPIs: total students, total teachers, total classes, total courses.
- Shows organization info: name, type, country, city.
- Admins can edit basic organization info directly from the dashboard (name, type, country, city, address, phone).
- Quick links to User Management and Class Management.

## User Management
- Admins manage all user accounts in their organization from this page.
- Users are shown in a table, filterable by role (STUDENT, TEACHER) and status (ACTIVE, INACTIVE).
- Admins can search users by name or email.
- Admins can create individual student or teacher accounts.
- Admins can bulk import users via CSV.
- When a new account is created, the system sends a temporary password to the user's email.
- Admins can edit user details (name, etc.).
- Admins can activate or deactivate accounts.
- For teachers, admins set the assignment scope: ALL_CLASSES or SELECTED_CLASSES.
- If SELECTED_CLASSES, the admin selects which classes the teacher is allowed to assign courses to.

## Class Management
- Admins manage classes from the Classes Page and Class Management Page.
- See the Classes section for details.

## Platform Admin
- Platform admins have full access across all organizations.
- They can create users with any role including ORG_ADMIN and PLATFORM_ADMIN.
- Admin dashboard shows platform-wide counts.

## Common Issues
- User can't log in after being created: check if the account status is ACTIVE; also check if the user has set their password from the temporary one sent by email.
- User not visible in admin panel: check the role and status filters.
- Teacher can't assign to a class: check the teacher's assignment scope in User Management.
- Need to reset a user's password: deactivate and recreate the account, or contact platform support.
