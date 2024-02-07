import mysql.connector as mysql

db = mysql.connect(
    host="localhost",
    user="root",
    password="",
    port="3308",
    database="ce201"
)
#testtest

command_handler = db.cursor(buffered=True)

if db and db.is_connected():
    print("Successfully connected to DB!")
else:
    print("Could not connect to DB")


def create_account():
    print("Create a new account: ")
    name = input("Enter your name: ")
    username = input("Enter username: ")
    password = input("Enter password: ")
    role = input("Enter role: ")

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
        print("Account created successfully")
    else:
        print("Account creation failed.")


def login():
    print("Login:")
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
               s.department_id  # Fetch department_id for staff
        FROM users u
        LEFT JOIN staff s ON u.user_id = s.user_id
        LEFT JOIN hrofficers ho ON u.user_id = ho.user_id
        LEFT JOIN hrsupervisors hs ON u.user_id = hs.user_id
        WHERE u.username = %s AND u.password = %s
    """, (username, password))

    user_data = command_handler.fetchone()

    if user_data:
        # fetch user data
        user_id, username, role, name, department = user_data

        # open specific menu for each role
        if role == "staff":
            staff_menu(user_id, name, department)
        elif role == "hrofficer":
            hrofficer_menu(user_id, name)
        elif role == "hrsupervisor":
            hrsupervisor_menu(user_id, name)
        else:
            print("Invalid role")
    else:
        print("Invalid username or password")


# role-specific menu functions
def staff_menu(user_id, name, department):
    print(f"Welcome to the Staff menu, {name}!")
    print("What would you like to do?")
    print("1. Apply for a course")
    print("2. Attend course")
    print("3. View training hours")

    # fetch department name based on the department ID
    command_handler.execute("SELECT name FROM departments WHERE department_id = %s", (department,))
    department_name = command_handler.fetchone()[0]

    # fetch relevant courses
    command_handler.execute("""
        SELECT c.name AS course_name, c.category, c.hours
        FROM courses c
        WHERE c.department_id = %s
    """, (department,))
    courses = command_handler.fetchall()

    user_option = input("Option: ")
    if user_option == "1":
        print(f"These are the courses available for your department, {department_name}:")
        for i, course in enumerate(courses, start=1):
            print(f"{i}. {course[0]} - {course[1]} skills - {course[2]} hours")
        print("\nWhich course would you like to apply for?")

    elif user_option == "2":
        print("Which course would you like to attend?")
    elif user_option == "3":
        print("Your current total training hours for the year are:")





def hrofficer_menu(user_id, name):
    print(f"Welcome to the HR Officer menu, {name}!")
    print("What would you like to do?")
    print("1. Adjust training hours")
    print("2. Generate department report")
    print("3. Generate staff report")

    user_option = input("Option: ")


def hrsupervisor_menu(user_id, name):
    print(f"Welcome to the HR Supervisor menu, {name}")
    print("What would you like to do?")
    print("1. Manage HR Officers")
    print("2. Adjust training hours")
    print("3. Add new course")
    print("4. Create new user account")

    user_option = input("Option: ")
    if user_option == "1":
        print("")
    elif user_option == "2":
        print("")
    elif user_option == "3":
        print("")
    elif user_option == "4":
        create_account()


def main():
    while 1:
        print("Welcome to STRAITS!\n")
        print("Log in: ")
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
            print("Not valid option")


main()
