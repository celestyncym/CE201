from datetime import datetime

import mysql.connector as mysql

db = mysql.connect(
    host="straits-system.c9m4skkmarao.ap-southeast-1.rds.amazonaws.com",
    user="admin",
    password="ce201team2",
    port="3306",
    database="straits_system"
)

query = db.cursor(buffered=True)

if db and db.is_connected():
    print("Successfully connected to DB!")
else:
    print("Could not connect to DB")


def create_account():
    print("Create a new account ")
    name = input("Enter your name (Enter '0' to go back): ")
    if name == '0':
        return
    username = input("Enter username: ")
    password = input("Enter password: ")
    print("1. Staff\n2. HR Officer\n3. HR Supervisor")
    role_option = input("Enter role: ")
    role_mapping = {
        "1": "Staff",
        "2": "HR Officer",
        "3": "HR Supervisor"
    }
    role = role_mapping.get(role_option)
    if role is None:
        print("Invalid option!")
        return

    print("1. Human Resources\n2. Marketing\n3. Finance\n4. Customer Support\n5. Information Technology\n6. Operations")

    # ask for department input only for staff and hrofficer roles
    department = None
    if role in ["Staff", "HR Officer"]:
        department = input("Enter department: ")

    def register_user_in_db(username, password, role, name, department):
        try:
            # insert user data into users table
            query.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                          (username, password, role))
            db.commit()
            user_id = query.lastrowid
            if role == "Staff":
                # insert staff data into staff table
                query.execute("INSERT INTO staff (user_id, name, department_id) VALUES (%s, %s, %s)",
                              (user_id, name, department))
            elif role == "HR Officer":
                # insert hrofficer data into hrofficers table
                query.execute("INSERT INTO hrofficers (user_id, name, department_id) VALUES (%s, %s, %s)",
                              (user_id, name, department))
            elif role == "HR Supervisor":
                # insert hrsupervisor data into hrsupervisors table
                query.execute("INSERT INTO hrsupervisors (user_id, name) VALUES (%s, %s)", (user_id, name))
            db.commit()

            return True
        except Exception as e:
            print(f"Error: {e}")
            db.rollback()
            return False

    success = register_user_in_db(username, password, role, name, department)

    if success:
        print("Account created successfully!")
    else:
        print("Account creation failed.")


def login():
    print("\nLogin")
    username = input("Enter username: ")
    password = input("Enter password: ")

    # query db to check user data and fetch data accordingly
    query.execute("""
        SELECT u.user_id, u.username, u.role,
               CASE
                 WHEN u.role = 'Staff' THEN s.name
                 WHEN u.role = 'HR Officer' THEN ho.name
                 WHEN u.role = 'HR Supervisor' THEN hs.name
               END AS user_name,
               s.department_id,
               s.staff_id
        FROM users u
        LEFT JOIN staff s ON u.user_id = s.user_id
        LEFT JOIN hrofficers ho ON u.user_id = ho.user_id
        LEFT JOIN hrsupervisors hs ON u.user_id = hs.user_id
        WHERE u.username = %s AND u.password = %s
    """, (username, password))

    user_data = query.fetchone()

    if user_data:
        # fetch user data
        user_id, username, role, name, department, staff_id = user_data

        # open specific menu for each role
        if role == "Staff":
            staff_menu(user_id, name, department, staff_id)
        elif role == "HR Officer":
            hrofficer_menu(name)
        elif role == "HR Supervisor":
            hrsupervisor_menu(name)
        else:
            print("Invalid role")
    else:
        print("Invalid username or password")


def apply_for_course(user_id, name, department, staff_id):
    # fetch department name based on the department_id
    query.execute("SELECT department_name FROM departments WHERE department_id = %s", (department,))
    department_name = query.fetchone()[0]

    # fetch relevant courses
    query.execute("""
         SELECT c.course_id, c.course_name, c.category, c.hours
         FROM courses AS c
         WHERE c.department_id = %s
     """, (department,))
    courses = query.fetchall()
    print(f"\nThese are the courses available for your department, {department_name}:")
    for i, course in enumerate(courses, start=1):
        print(f"{i}. {course[1]} | Category: {course[2]} Skills | Hours: {course[3]}")

    course_selection = input("\nWhich course would you like to apply for? (Enter '0' to go back): ")

    if course_selection == '0':
        return

    try:
        selected_course = courses[int(course_selection) - 1]
        print(f"You have selected: {selected_course[1]}")

        # check if staff has already attended the selected course
        query.execute("""
                            SELECT * FROM staffCourses 
                            WHERE staff_id = %s AND course_id = %s AND attended = 'yes'
                        """, (staff_id, selected_course[0]))
        already_attended = query.fetchone()

        if already_attended:
            print("You have already attended this course before, you will not be rewarded any hours even if "
                  "you attend it again!")
            proceed = input("Would you still like to proceed? y/n: ")
            if proceed.lower() != "y":
                return
        else:
            # prompt staff for commencement date
            date_input = input("Enter the date you want to attend the course (YYYY-MM-DD): ")
            try:
                date = datetime.strptime(date_input, "%Y-%m-%d")
                success = save_course_to_db(user_id, selected_course[0], date)
                if success:
                    print(
                        f"You have successfully applied for the course {selected_course[1]}, scheduled on {date}")
                else:
                    print("Failed to apply for the course. Please try again.")
            except ValueError:
                print("Invalid date format! Please enter the date in YYYY-MM-DD format.")

    except (ValueError, IndexError):
        print("Invalid input! Please enter a valid number.")


def save_course_to_db(user_id, course_id, date_enrolled):
    try:
        # fetch staff_id associated with the user_id
        query.execute("SELECT staff_id FROM staff WHERE user_id = %s", (user_id,))
        result = query.fetchone()

        if result:
            staff_id = result[0]

            # insert the course into the staffCourses table
            query.execute(
                "INSERT INTO staffCourses (staff_id, course_id, date_enrolled) VALUES (%s, %s, %s)",
                (staff_id, course_id, date_enrolled)
            )
            db.commit()

            return True
        else:
            print("User is not associated with any staff record.")
            return False
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False


def attend_course(staff_id):
    try:
        # fetch staff's applied courses from staffCourses table
        query.execute("""
                SELECT c.course_name, c.category, c.hours, sc.date_enrolled, sc.attended, sc.course_id
                FROM staffCourses AS sc
                JOIN courses c ON sc.course_id = c.course_id
                WHERE sc.staff_id = %s
            """, (staff_id,))

        applied_courses = query.fetchall()

        if applied_courses:
            print("You have currently applied for these courses:")

            for i, course in enumerate(applied_courses, start=1):
                print(
                    f"{i}. {course[0]}, Category: {course[1]} Skills, Hours: {course[2]}, Start Date: {course[3]}, Attended: {course[4]}")

            course_selection = input("\nWhich course would you like to attend? (Enter '0' to go back): ")

            if course_selection == '0':
                return

            try:
                selected_index = int(course_selection)

                if 1 <= selected_index <= len(applied_courses):
                    selected_course = applied_courses[selected_index - 1]
                    print(f"You have selected: {selected_course[0]}")

                    # check if course has already been attended
                    if selected_course[4] == 'yes':
                        print("You have already attended this course!")

                    else:
                        # update attended status to yes
                        query.execute("""
                                UPDATE staffCourses 
                                SET attended = 'yes'
                                WHERE staff_id = %s AND course_id = %s
                            """, (staff_id, selected_course[5]))
                        db.commit()
                        print(f"You have successfully attended the course: {selected_course[0]}!")
                else:
                    print("Invalid input! Please enter a valid number.")

            except ValueError:
                print("Invalid input! Please enter a valid number.")

        else:
            print("You have not applied to any courses!")

    except Exception as e:
        print(f"Error fetching applied courses: {e}")


def view_hours(staff_id):
    try:
        # fetch staff's attended courses with details
        query.execute("""
                SELECT c.course_name, c.hours, c.category
                FROM staffCourses AS sc 
                JOIN courses c ON sc.course_id = c.course_id 
                WHERE sc.staff_id = %s AND sc.attended = 'yes'
            """, (staff_id,))
        attended_courses = query.fetchall()

        if attended_courses:
            # initialise dictionaries to store total hours and unique course names for each category
            total_hours = {"Core": 0, "Soft": 0}
            unique_courses = {"Core": set(), "Soft": set()}

            # iterate through attended courses to calculate the total hours for respective skill category
            for course in attended_courses:
                course_name, hours, category = course
                unique_courses[category].add(course_name)
                total_hours[category] += hours

            # print total training hours
            print("The total training hours for the year are...")
            for category, total in total_hours.items():
                print(f"{category} Skills: {total}")

            # calculate remaining hours needed
            remaining_hours = {}
            for category, total in total_hours.items():
                remaining_hours[category] = max(total_hours_required * (default_ratios[category] / 100) - total, 0)

            # print remaining hours needed
            print(f"\nTotal Hours Required: {total_hours_required}")
            print("Current Ratio Split (Core/Soft): {}/{}".format(default_core_ratio, default_soft_ratio))
            print("\nRemaining Hours Needed:")
            for category, remaining in remaining_hours.items():
                print(f"{category} Skill Hours Needed: {remaining}")

            # check if all hours are completed
            if all(remaining_hours[category] == 0 for category in ["Core", "Soft"]):
                print(f"\nTraining hours completed!")

            go_back = input("\nEnter '0' to go back: ")
            if go_back == '0':
                return
        else:
            print("No courses attended yet!")

            # print total training hours
            print("\nThe total training hours for the year are...")
            for category in ["Core", "Soft"]:
                print(f"{category} Skills: 0")

            # calculate and print remaining hours needed (based on default ratios)
            print(f"\nTotal Hours Required: {total_hours_required}")
            print("Current Ratio Split (Core/Soft): {}/{}\n".format(default_core_ratio, default_soft_ratio))
            for category in ["Core", "Soft"]:
                remaining = max(total_hours_required * (default_ratios[category] / 100), 0)
                print(f"Remaining {category} Skill Hours Needed: {remaining}")

            go_back = input("\nEnter '0' to go back: ")
            if go_back == '0':
                return

    except Exception as e:
        print(f"Error fetching attended courses: {e}")


def generate_department_report():
    try:
        # fetch departments from db
        query.execute("SELECT department_id, department_name FROM departments")
        departments = query.fetchall()

        for i, department in enumerate(departments, start=1):
            print(f"{i}. {department[1]}")
        department_index = input("\nChoose department: ")

        # validate user input
        try:
            department_index = int(department_index) - 1
            if department_index < 0 or department_index >= len(departments):
                raise ValueError
        except ValueError:
            print("Invalid input! Please enter a valid number.")
            return

        selected_department_id = departments[department_index][0]
        selected_department_name = departments[department_index][1]

        # fetch staff from the selected department
        query.execute("""
            SELECT s.staff_id, s.name
            FROM staff AS s
            WHERE s.department_id = %s
        """, (selected_department_id,))
        department_staff = query.fetchall()

        # print department staff list
        print(f"\n{selected_department_name} Staff:")
        for i, staff in enumerate(department_staff, start=1):
            print(f"{i}. {staff[1]}")

        # check and display hours for each staff member
        print(f"\nReport of {selected_department_name} Department:")
        for staff_id, staff_name in department_staff:
            try:
                # fetch staff's attended courses with details
                query.execute("""
                        SELECT c.course_name, c.hours, c.category
                        FROM staffCourses AS sc 
                        JOIN courses c ON sc.course_id = c.course_id 
                        WHERE sc.staff_id = %s AND sc.attended = 'yes'
                    """, (staff_id,))
                attended_courses = query.fetchall()

                if attended_courses:
                    # initialise dictionaries to store total hours and UNIQUE course names
                    total_hours = {"Core": 0, "Soft": 0}
                    unique_courses = {"Core": set(), "Soft": set()}

                    # iterate through attended courses to calculate the total hours for respective skill category
                    for course_name, hours, category in attended_courses:
                        unique_courses[category].add(course_name)
                        total_hours[category] += hours

                    # print total training hours
                    print(f"\n{staff_name}'s Training Hours:")
                    for category, total in total_hours.items():
                        print(f"{category} Skills: {total}")

                    # calculate and print remaining hours needed
                    remaining_hours = {}
                    for category, total in total_hours.items():
                        remaining_hours[category] = max(total_hours_required * (default_ratios[category] / 100) - total,
                                                        0)
                    for category, remaining in remaining_hours.items():
                        print(f"Remaining {category} Skill Hours Needed: {remaining}")

                    # check if all hours are completed
                    if all(remaining_hours[category] == 0 for category in ["Core", "Soft"]):
                        print(f"{staff_name} has completed their training hours!")
                else:
                    print(f"\n{staff_name} has not attended any courses yet!")

            except Exception as e:
                print(f"Error fetching attended courses for {staff_name}: {e}")

        go_back = input("\nEnter '0' to go back: ")
        if go_back == '0':
            return

    except Exception as e:
        print(f"Error generating department report: {e}")


def generate_staff_report():
    try:
        # fetch departments from db
        query.execute("SELECT department_id, department_name FROM departments")
        departments = query.fetchall()

        for i, department in enumerate(departments, start=1):
            print(f"{i}. {department[1]}")
        department_index = input("\nChoose department: ")

        # validate user input
        try:
            department_index = int(department_index) - 1
            if department_index < 0 or department_index >= len(departments):
                raise ValueError
        except ValueError:
            print("Invalid input! Please enter a valid number.")
            return

        selected_department_id = departments[department_index][0]
        selected_department_name = departments[department_index][1]

        # fetch staff from the selected department
        query.execute("""
            SELECT s.staff_id, s.name
            FROM staff AS s
            WHERE s.department_id = %s
        """, (selected_department_id,))
        department_staff = query.fetchall()

        # print department staff list
        print(f"\n{selected_department_name} Staff:")
        for i, staff in enumerate(department_staff, start=1):
            print(f"{i}. {staff[1]}")

        # let the user select a staff member to view their hours
        staff_index = input("\nSelect staff member to view their hours: ")

        # validate user input
        try:
            staff_index = int(staff_index) - 1
            if staff_index < 0 or staff_index >= len(department_staff):
                raise ValueError
        except ValueError:
            print("Invalid input! Please enter a valid number.")
            return

        selected_staff_id = department_staff[staff_index][0]
        selected_staff_name = department_staff[staff_index][1]

        # display the hours for the selected staff member using view_hours() function
        print(f"\n{selected_staff_name}'s Report: ")
        view_hours(selected_staff_id)

    except Exception as e:
        print(f"Error generating staff report: {e}")


def create_course():
    print("Create a new course ")
    name = input("Enter course name (Enter '0' to go back): ")
    if name == '0':
        return
    print("1. Core\n2. Soft")
    category_option = input("Choose category: ")
    category_mapping = {
        "1": "Core",
        "2": "Soft"
    }
    category = category_mapping.get(category_option)
    if category is None:
        print("Invalid option!")
        return
    hours = input("Enter hours: ")
    print("1. Human Resources\n2. Marketing\n3. Finance\n4. Customer Support\n5. Information Technology\n6. Operations")
    department = input("\nEnter department: ")

    def add_course_in_db(name, category, hours, department):
        try:
            query.execute(
                "INSERT INTO courses (course_name, category, hours, department_id) VALUES (%s, %s, %s, %s)",
                (name, category, hours, department))
            db.commit()

            return True
        except Exception as e:
            print(f"Error: {e}")
            db.rollback()
            return False

    success = add_course_in_db(name, category, hours, department)

    if success:
        print("\nCourse added successfully!")
    else:
        print("Failed to add course.")


# declare global values
total_hours_required = 100
default_core_ratio = 50
default_soft_ratio = 50
default_ratios = {"Core": default_core_ratio, "Soft": default_soft_ratio}


def adjust_training_hours():
    while True:
        print("\nWhat would you like to adjust?")
        print("1. Course Training Hours")
        print("2. Split Ratio")
        print("3. Total Hours Required")
        print("4. Exit")

        user_option = input("\nOption: ")

        if user_option == "1":
            try:
                # fetch all courses from db
                query.execute("""
                        SELECT c.course_id, c.course_name, c.category, c.hours, d.department_name 
                        FROM courses AS c 
                        JOIN departments AS d ON c.department_id = d.department_id
                    """)
                courses = query.fetchall()

                # display courses
                print("List of all available courses:")
                for i, course in enumerate(courses, start=1):
                    print(
                        f"{i}. {course[1]} | Department: {course[4]} | Category: {course[2]} Skills | Hours: {course[3]}")

                course_selection = input("\nWhich course would you like to adjust? (Enter '0' to go back): ")

                if course_selection == '0':
                    return

                # validate user input
                try:
                    course_index = int(course_selection) - 1
                    if course_index < 0 or course_index >= len(courses):
                        raise ValueError
                except ValueError:
                    print("Invalid input! Please enter a valid number.")
                    return

                selected_course = courses[course_index]
                selected_course_id = selected_course[0]
                selected_course_name = selected_course[1]

                # prompt user for new training hours
                new_hours = input(f"Enter new training hours for '{selected_course_name}': ")

                # validate input
                try:
                    new_hours = int(new_hours)
                    if new_hours < 0:
                        raise ValueError
                except ValueError:
                    print("Invalid input! Please enter a positive integer.")
                    return

                # update course with new training hours
                query.execute("UPDATE courses SET hours = %s WHERE course_id = %s", (new_hours, selected_course_id))
                db.commit()

                print(
                    f"Training hours for '{selected_course_name}' have been successfully adjusted to {new_hours} hours.")

            except Exception as e:
                print(f"Error adjusting training hours: {e}")

        elif user_option == "2":
            global default_core_ratio, default_soft_ratio
            try:
                print(f"Current Split Ratio: Core Skills: {default_core_ratio}, Soft Skills: {default_soft_ratio}")

                # prompt user for new ratio
                new_core_ratio = input(
                    "Enter the new ratio for Core Skills (between 0 and 100) (Enter '0' to go back): ")
                new_soft_ratio = 100 - int(new_core_ratio)

                if new_core_ratio == '0':
                    return

                # validate input
                try:
                    new_core_ratio = float(new_core_ratio)
                    new_soft_ratio = float(new_soft_ratio)
                    if not 0 <= new_core_ratio <= 100 or not 0 <= new_soft_ratio <= 100 or new_core_ratio + new_soft_ratio != 100:
                        raise ValueError
                except ValueError:
                    print("Invalid input! Value must be between 0 and 100, and have a sum of 100.")
                    return

                # update default
                default_core_ratio = new_core_ratio
                default_soft_ratio = new_soft_ratio

                print("Successfully updated ratio.")

            except Exception as e:
                print(f"Error adjusting ratio split: {e}")

        elif user_option == "3":
            global total_hours_required
            try:
                print(f"Current Total Hours Required: {total_hours_required}")

                # prompt for new total hours required
                new_total_hours_required = input("Enter the new total hours required (Enter '0' to go back): ")

                if new_total_hours_required == '0':
                    return

                # validate input
                try:
                    new_total_hours_required = int(new_total_hours_required)
                    if new_total_hours_required <= 0:
                        raise ValueError
                except ValueError:
                    print("Invalid input! Value must be a positive integer.")
                    return

                # update total hours required
                total_hours_required = new_total_hours_required
                print("Successfully updated the total hours required.")

            except Exception as e:
                print(f"Error adjusting total hours required: {e}")

        elif user_option == "4":
            return
        else:
            print("Invalid option!")


def manage_staff():
    while True:
        print("\nWhat would you like to do?")
        print("1. Manage HR Officers")
        print("2. Manage Staff")
        print("3. Exit")

        user_option = input("\nOption: ")

        # fetch all HR officers from db
        query.execute("""
              SELECT ho.officer_id, ho.name, d.department_name, u.role, ho.user_id, d.department_id
              FROM hrofficers AS ho
              JOIN departments AS d ON ho.department_id = d.department_id
              JOIN users AS u ON ho.user_id = u.user_id
          """)
        officers = query.fetchall()

        # fetch all departments from db
        query.execute("SELECT department_id, department_name FROM departments")
        departments = query.fetchall()

        # fetch all staff from db
        query.execute("""
                   SELECT s.staff_id, s.name, s.user_id, d.department_name, u.role, d.department_id
                   FROM staff AS s
                   JOIN departments AS d ON s.department_id = d.department_id
                   JOIN users AS u ON s.user_id = u.user_id    
               """)
        staffs = query.fetchall()

        if user_option == "1":
            try:
                # display list of officers
                print("\nList of HR Officers:")
                for i, officer in enumerate(officers, start=1):
                    print(
                        f"{i}. {officer[1]} | Department: {officer[2]} | Role: {officer[3]}")

                officer_selection = input("\nWhich HR Officer would you like to manage? (Enter '0' to go back) ")

                if officer_selection == '0':
                    return

                # validate user input
                try:
                    officer_index = int(officer_selection) - 1
                    if officer_index < 0 or officer_index >= len(officers):
                        raise ValueError
                except ValueError:
                    print("Invalid input! Please enter a valid number.")
                    return

                selected_officer = officers[officer_index]

                print("\n1. Change department")
                print("2. Change role")

                choice_selection = input("\nWhat would you like to do next? (Enter '0' to go back) ")

                if choice_selection == "0":
                    return
                elif choice_selection == "1":
                    for j, department in enumerate(departments, start=1):
                        print(f"{j}. {department[1]}")
                    new_department_index = input("\nChoose new department: ")

                    # validate user input
                    try:
                        new_department_index = int(new_department_index) - 1
                        if new_department_index < 0 or new_department_index >= len(departments):
                            raise ValueError
                    except ValueError:
                        print("Invalid input! Please enter a valid number.")
                        return

                    new_department_id = departments[new_department_index][0]

                    # update hr officer with new department
                    query.execute("""
                            UPDATE hrofficers SET department_id = %s WHERE officer_id = %s
                        """, (new_department_id, selected_officer[0]))
                    db.commit()
                    print(f"Successfully updated {selected_officer[1]}'s department!")

                elif choice_selection == "2":
                    # fetch the user_id of the selected HR officer
                    user_id = selected_officer[4]

                    print("\n1. Staff\n2. HR Officer")
                    role_option = input("\nEnter role: ")
                    role_mapping = {
                        "1": "Staff",
                        "2": "HR Officer",
                    }
                    new_role = role_mapping.get(role_option)
                    if new_role is None:
                        print("Invalid option!")
                        return

                    # update the role in the users table
                    query.execute("UPDATE users SET role = %s WHERE user_id = %s", (new_role, user_id))
                    db.commit()

                    if new_role == "Staff":
                        # insert user's data into the staff table
                        query.execute("INSERT INTO staff (user_id, name, department_id) VALUES (%s, %s, %s)",
                                      (selected_officer[4], selected_officer[1], selected_officer[5]))
                        db.commit()
                        # delete user's data from previous role (hr officer)'s table
                        query.execute("DELETE FROM hrofficers WHERE user_id = %s", (user_id,))
                        db.commit()
                        print(f"Successfully updated {selected_officer[1]}'s role to {new_role}!")
                else:
                    print("Invalid option!")

            except Exception as e:
                print(f"Error managing HR Officers: {e}")

        elif user_option == "2":
            try:
                # display list of staff
                print("\nList of Staff:")
                for i, staff in enumerate(staffs, start=1):
                    print(f"{i}. {staff[1]} | Department: {staff[3]} | Role: {staff[4]}")

                staff_selection = input("\nWhich staff would you like to manage? (Enter '0' to go back) ")

                if staff_selection == '0':
                    return

                # validate user input
                try:
                    staff_index = int(staff_selection) - 1
                    if staff_index < 0 or staff_index >= len(staffs):
                        raise ValueError
                except ValueError:
                    print("Invalid input! Please enter a valid number.")
                    return

                selected_staff = staffs[staff_index]

                print("\n1. Change department")
                print("2. Change role")

                choice_selection = input("\nWhat would you like to do next? (Enter '0' to go back) ")

                if choice_selection == "0":
                    return
                elif choice_selection == "1":
                    for j, department in enumerate(departments, start=1):
                        print(f"{j}. {department[1]}")
                    new_department_index = input("\nChoose new department: ")

                    # validate user input
                    try:
                        new_department_index = int(new_department_index) - 1
                        if new_department_index < 0 or new_department_index >= len(departments):
                            raise ValueError
                    except ValueError:
                        print("Invalid input! Please enter a valid number.")
                        return

                    new_department_id = departments[new_department_index][0]

                    # update staff with new department
                    query.execute("""
                            UPDATE staff SET department_id = %s WHERE staff_id = %s
                        """, (new_department_id, selected_staff[0]))
                    db.commit()
                    print(f"Successfully updated {selected_staff[1]}'s department!")

                elif choice_selection == "2":
                    # fetch the user_id of the selected staff
                    user_id = selected_staff[2]

                    print("1. Staff\n2. HR Officer")
                    role_option = input("\nEnter role: ")
                    role_mapping = {
                        "1": "Staff",
                        "2": "HR Officer",
                    }
                    new_role = role_mapping.get(role_option)
                    if new_role is None:
                        print("Invalid option!")
                        return

                    # update the role in the users table
                    query.execute("UPDATE users SET role = %s WHERE user_id = %s", (new_role, user_id))
                    db.commit()

                    if new_role == "HR Officer":
                        # insert user's data into the hrofficers table
                        query.execute("INSERT INTO hrofficers (user_id, name, department_id) VALUES (%s, %s, %s)",
                                      (selected_staff[2], selected_staff[1], selected_staff[5]))
                        db.commit()
                        # delete user's data from previous role (hr officer)'s table
                        query.execute("DELETE FROM staff WHERE user_id = %s", (user_id,))
                        db.commit()
                        print(f"Successfully updated {selected_staff[1]}'s role to {new_role}!")

            except Exception as e:
                print(f"Error managing Staff: {e}")
        elif user_option == "3":
            return
        else:
            print("Invalid option!")


# role-specific menu functions
def staff_menu(user_id, name, department, staff_id):
    while True:
        print(f"\nWelcome to the Staff menu, {name}!")
        print("What would you like to do?")
        print("1. Apply for a course")
        print("2. Attend course")
        print("3. View training hours")
        print("4. Exit")

        user_option = input("\nOption: ")

        if user_option == "1":
            apply_for_course(user_id, name, department, staff_id)
        elif user_option == "2":
            attend_course(staff_id)
        elif user_option == "3":
            view_hours(staff_id)
        elif user_option == "4":
            break
        else:
            print("Invalid option!")


def hrofficer_menu(name):
    while True:
        print(f"\nWelcome to the HR Officer menu, {name}!")
        print("What would you like to do?")
        print("1. Adjust training hours")
        print("2. Generate department report")
        print("3. Generate staff report")
        print("4. Exit")

        user_option = input("\nOption: ")
        if user_option == "1":
            adjust_training_hours()
        elif user_option == "2":
            generate_department_report()
        elif user_option == "3":
            generate_staff_report()
        elif user_option == "4":
            break
        else:
            print("Invalid option!")


def hrsupervisor_menu(name):
    while True:
        print(f"\nWelcome to the HR Supervisor menu, {name}")
        print("What would you like to do?")
        print("1. Manage Staff")
        print("2. Adjust training hours")
        print("3. Add new course")
        print("4. Create new user account")
        print("5. Exit")

        user_option = input("\nOption: ")
        if user_option == "1":
            manage_staff()
        elif user_option == "2":
            adjust_training_hours()
        elif user_option == "3":
            create_course()
        elif user_option == "4":
            create_account()
        elif user_option == "5":
            break
        else:
            print("Invalid option!")


def main():
    while 1:
        print("Welcome to STRAITS!\n")
        print("Login as: ")
        print("1. Staff")
        print("2. HR Officer")
        print("3. HR Supervisor")

        user_option = input("Option: ")
        if user_option == "1" or user_option == "2" or user_option == "3":
            login()
        else:
            print("Invalid option.")


main()
