from datetime import datetime

import mysql.connector as mysql

db = mysql.connect(
    host="localhost",
    user="root",
    password="",
    port="3308",
    database="ce201"
)

command_handler = db.cursor(buffered=True)

if db and db.is_connected():
    print("Successfully connected to DB!")
else:
    print("Could not connect to DB")


def create_account():
    print("Create a new account ")
    name = input("Enter your name: ")
    username = input("Enter username: ")
    password = input("Enter password: ")
    role = input("Enter role (staff, hrofficer, hrsupervisor): ")
    print("1. Human Resources\n2. Marketing\n3. Finance\n4. Customer Support\n5. Information Technology\n6. Operations")

    # ask for department input only for staff and hrofficer roles
    department = None
    if role in ["staff", "hrofficer"]:
        department = input("Enter department: ")

    def register_user_in_db(username, password, role, name, department):
        try:
            # insert user data into users table
            command_handler.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                                    (username, password, role))
            db.commit()
            user_id = command_handler.lastrowid
            if role == "staff":
                # insert staff data into staff table
                command_handler.execute("INSERT INTO staff (user_id, name, department_id) VALUES (%s, %s, %s)",
                                        (user_id, name, department))
            elif role == "hrofficer":
                # insert hrofficer data into hrofficers table
                command_handler.execute("INSERT INTO hrofficers (user_id, name, department_id) VALUES (%s, %s, %s)",
                                        (user_id, name, department))
            elif role == "hrsupervisor":
                # insert hrsupervisor data into hrsupervisors table
                command_handler.execute("INSERT INTO hrsupervisors (user_id, name) VALUES (%s, %s)", (user_id, name))
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
    command_handler.execute("""
        SELECT u.user_id, u.username, u.role,
               CASE
                 WHEN u.role = 'staff' THEN s.name
                 WHEN u.role = 'hrofficer' THEN ho.name
                 WHEN u.role = 'hrsupervisor' THEN hs.name
               END AS user_name,
               s.department_id,
               s.staff_id
        FROM users u
        LEFT JOIN staff s ON u.user_id = s.user_id
        LEFT JOIN hrofficers ho ON u.user_id = ho.user_id
        LEFT JOIN hrsupervisors hs ON u.user_id = hs.user_id
        WHERE u.username = %s AND u.password = %s
    """, (username, password))

    user_data = command_handler.fetchone()

    if user_data:
        # fetch user data
        user_id, username, role, name, department, staff_id = user_data

        # open specific menu for each role
        if role == "staff":
            staff_menu(user_id, name, department, staff_id)
        elif role == "hrofficer":
            hrofficer_menu(user_id, name)
        elif role == "hrsupervisor":
            hrsupervisor_menu(user_id, name)
        else:
            print("Invalid role")
    else:
        print("Invalid username or password")


def apply_for_course(user_id, course_id, start_date):
    try:
        # fetch staff_id associated with the user_id
        command_handler.execute("SELECT staff_id FROM staff WHERE user_id = %s", (user_id,))
        result = command_handler.fetchone()

        if result:
            staff_id = result[0]

            # insert the course into the applied_courses table
            command_handler.execute(
                "INSERT INTO applied_courses (staff_id, course_id, startdate) VALUES (%s, %s, %s)",
                (staff_id, course_id, start_date)
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


def create_course():
    print("Create a new course ")
    name = input("Enter course name: ")
    category = input("Enter category (Core or Soft): ")
    hours = input("Enter hours: ")
    print("1. Human Resources\n2. Marketing\n3. Finance\n4. Customer Support\n5. Information Technology\n6. Operations")
    department = input("\nEnter department: ")

    def add_course_in_db(name, category, hours, department):
        try:
            command_handler.execute(
                "INSERT INTO courses (name, category, hours, department_id) VALUES (%s, %s, %s, %s)",
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


# role-specific menu functions
def staff_menu(user_id, name, department, staff_id):
    while True:
        # fetch department name based on the department_id
        command_handler.execute("SELECT name FROM departments WHERE department_id = %s", (department,))
        department_name = command_handler.fetchone()[0]

        # fetch relevant courses
        command_handler.execute("""
            SELECT c.course_id, c.name AS course_name, c.category, c.hours
            FROM courses c
            WHERE c.department_id = %s
        """, (department,))
        courses = command_handler.fetchall()

        print(f"\nWelcome to the Staff menu, {name}!")
        print("What would you like to do?")
        print("1. Apply for a course")
        print("2. Attend course")
        print("3. View training hours")
        print("4. Exit")

        user_option = input("\nOption: ")

        if user_option == "1":
            print(f"\nThese are the courses available for your department, {department_name}:")
            for i, course in enumerate(courses, start=1):
                print(f"{i}. {course[1]}, Category: {course[2]} Skills, Hours: {course[3]}")

            course_selection = input("\nWhich course would you like to apply for? (Enter '0' to go back): ")

            if course_selection == '0':
                continue

            try:
                selected_course = courses[int(course_selection) - 1]
                print(f"You have selected: {selected_course[1]}")

                # prompt user for commencement date
                date_input = input("Enter the date you want to attend the course (YYYY-MM-DD): ")
                try:
                    date = datetime.strptime(date_input, "%Y-%m-%d")
                    success = apply_for_course(user_id, selected_course[0], date)
                    if success:
                        print(f"You have successfully applied for the course {selected_course[1]}, scheduled on {date}")
                    else:
                        print("Failed to apply for the course. Please try again.")
                except ValueError:
                    print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

            except (ValueError, IndexError):
                print("Invalid input. Please enter a valid course number.")

        elif user_option == "2":
            try:
                # fetch the user's applied courses
                command_handler.execute("""
                    SELECT c.name AS course_name, c.category, c.hours, ac.startdate
                    FROM applied_courses ac
                    JOIN courses c ON ac.course_id = c.course_id
                    WHERE ac.staff_id = %s
                """, (staff_id,))
                applied_courses = command_handler.fetchall()

                if applied_courses:
                    print("You have currently applied for these courses:")
                    for i, course in enumerate(applied_courses, start=1):
                        print(
                            f"{i}. {course[0]}, Category: {course[1]} Skills, Hours: {course[2]}, Start Date: {course[3]}")
                    attend_course = input("\nWhich course would you like to attend?")
                else:
                    print("You are not currently attending any courses.")

            except Exception as e:
                print(f"Error fetching applied courses: {e}")

        elif user_option == "3":
            print("Your current total training hours for the year are:")

        elif user_option == "4":
            break

        else:
            print("Invalid option.")


def hrofficer_menu(user_id, name):
    print(f"\nWelcome to the HR Officer menu, {name}!")
    print("What would you like to do?")
    print("1. Adjust training hours")
    print("2. Generate department report")
    print("3. Generate staff report")

    user_option = input("\nOption: ")


def hrsupervisor_menu(user_id, name):
    print(f"\nWelcome to the HR Supervisor menu, {name}")
    print("What would you like to do?")
    print("1. Manage HR Officers")
    print("2. Adjust training hours")
    print("3. Add new course")
    print("4. Create new user account")

    user_option = input("\nOption: ")
    if user_option == "1":
        print("")
    elif user_option == "2":
        print("")
    elif user_option == "3":
        create_course()
    elif user_option == "4":
        create_account()


def main():
    while 1:
        print("Welcome to STRAITS!\n")
        print("Login as: ")
        print("1. Staff")
        print("2. HR Officer")
        print("3. HR Supervisor")

        user_option = input("Option: ")
        if user_option == "1":
            login()
        elif user_option == "2":
            login()
        elif user_option == "3":
            login()
        else:
            print("Invalid option.")


main()
