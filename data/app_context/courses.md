# Courses

## Browsing Courses (Students)
- Students see courses on their main page after login.
- Tabs: Assigned (courses assigned to their class), Public (open to everyone), Archived/Completed.
- Courses can be searched and filtered.

## Course Visibility
- PRIVATE: only the creator can see it.
- CLASS_ASSIGNED: visible to students in assigned classes.
- ORGANIZATION_WIDE: visible to all members of the organization.
- PUBLIC: visible to everyone.

## Course Status
- DRAFT: not yet published, not visible to students.
- PUBLISHED: active and accessible to students.
- ARCHIVED: no longer active.

## Course Structure
- A course is a tree of nodes: SECTION (container/chapter) and RESOURCE (actual content).
- Resource types: PDF, VIDEO, MARKDOWN, TEXT, LINK.
- Courses also contain stable tests as nodes in the content tree.

## For Teachers — My Courses
- Teachers see their own courses on their main page after login.
- Teachers can create new courses, set title, description, and visibility.
- Teachers can publish or archive courses.
- A course must be published before students can access it.

## Course Editor
- Teachers build and edit the course content tree in the Course Editor.
- They can add chapters (sections) and resources (text, PDF, video, link).
- Nodes can be reordered, edited, and deleted.
- Text nodes support hyperlinks.
- The Course Editor is also where teachers add test nodes to the course.

## Course Study Page (Students)
- Students open a course to study its content.
- They can navigate the content tree, open resources, and track their progress.
- Students can select content nodes to generate a personalized test based on that content.
- Progress is updated as students complete resources.

## Course Assignment
- Teachers assign courses to classes.
- Teachers with SELECTED_CLASSES scope can only assign to specific classes configured by the admin.
- Teachers with ALL_CLASSES scope can assign to any class in the organization.

## Common Issues
- Course not visible: it must be PUBLISHED and assigned to your class, or set to PUBLIC.
- Can't access a course: check if it's assigned to your class or if it's public.
- Course content not loading: try refreshing the page.
- Progress not updating: make sure you are opening and completing the resources.
