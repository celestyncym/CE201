# class User:
#     def __init__(self, user_id, username, password, role):
#         self.user_id = user_id
#         self.username = username
#         self.password = password
#         self.role = role
#
#
# # subclasses(child) of User class so in order to call the constructor of User (parent) class use super().__init__
# class Staff(User):
#     def __init__(self, username, password, staff_id, name, department, core_skills_hours, soft_skills_hours):
#         super().__init__(username, password, role="staff")
#         self.staff_id = staff_id
#         self.name = name
#         self.department = department
#         self.core_skills_hours = core_skills_hours
#         self.soft_skills_hours = soft_skills_hours
#         self.applied_courses = []
#         self.attended_courses = []
#
#     def apply_course(self, course):
#         if course not in self.applied_courses and course not in self.attended_courses:
#             self.applied_courses.append(course)
#             print(f"Successfully applied for the course: {course.name}")
#         else:
#             print("You have already applied for or attended this course.")
#
#     def attend_course(self, course):
#         if course in self.applied_courses:
#             self.applied_courses.remove(course)
#             self.attended_courses.append(course)
#             if course.category == "core":
#                 self.core_skills_hours += course.duration
#             elif course.category == "soft":
#                 self.soft_skills_hours += course.duration
#             print(f"Successfully attended the course: {course.name}!")
#         elif course in self.attended_courses:
#             print(f"You have already attended the course: {course.name}. No additional hours will be added.")
#         else:
#             print("You can only attend a course you have applied for!")
#
#
# class HROfficer(User):
#     def __init__(self, username, password):
#         super().__init__(username, password)
#
#     def adjust_training_hours(self, staff, total_hours):
#         staff.core_skills_hours = total_hours // 2
#         staff.soft_skills_hours = total_hours // 2
#         print(f"Successfully adjusted training hours for {staff.name}.")
#
#     def generate_department_report(self, department):
#         print(f"Department Report for {department}")
#         for staff in department.staff_members:
#             print(f"{staff.name}: \n Core Skills - {staff.core_skills_hours} \n Soft Skills - {staff.soft_skills_hours}")
#
# class HRSupervisor(User):
#     def __init__(self, username, password):
#         super().__init__(username, password)
#
#     def assign_department(self, hr_officer, department):
#         department.assign_hr_officer(hr_officer)
#         print(f"Assigned HR Officer {hr_officer.name} to {department}.name")
#
#     def add_course(self, course):
#         system_courses.append(course)
#         print(f"Added a new course: {course.name}")
#
#     def adjust_training_hours(self, staff, total_hours):
#         staff.core_skills_hours = total_hours // 2
#         staff.soft_skills_hours = total_hours // 2
#         print(f"Successfully adjusted training hours for {staff.name}.")
#
#     def generate_department_report(self, department):
#         print(f"Department Report for {department}")
#         for staff in department.staff_members:
#             print(f"{staff.name}: \n Core Skills - {staff.core_skills_hours} \n Soft Skills - {staff.soft_skills_hours}")
#
# class Department:
#     def __init__(self, department_id, name):
#         self.department_id = department_id
#         self.name = name
#         self.staff_members = []