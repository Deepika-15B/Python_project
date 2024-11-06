import sqlite3
from datetime import datetime

ADMIN_PASSWORD = "1234"

class AttendanceTracker:
    def __init__(self):  
        self.conn, self.c = self.connect_db()
        self.students = self.load_students()

    def connect_db(self):
        conn = sqlite3.connect('attendance_tracker.db')
        c = conn.cursor()
        
        # Create tables if they don't exist
        c.execute('''CREATE TABLE IF NOT EXISTS students (id TEXT PRIMARY KEY, name TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS attendance (date TEXT, student_id TEXT, status TEXT, session TEXT)''')
        
        # Ensure the session column exists in the attendance table
        c.execute("PRAGMA table_info(attendance)")
        columns = [column[1] for column in c.fetchall()]
        if "session" not in columns:
            c.execute("ALTER TABLE attendance ADD COLUMN session TEXT")
        
        conn.commit()
        return conn, c

    def load_students(self):
        self.c.execute("SELECT * FROM students")
        return {row[0]: row[1] for row in self.c.fetchall()}

    def is_valid_student_id(self, student_id):
        return student_id.isdigit() and len(student_id) == 3

    def authenticate(self):
        password = input("Enter admin password: ")
        return password == ADMIN_PASSWORD

    def add_student(self, student_id, student_name):
        if not self.is_valid_student_id(student_id):
            print("Invalid ID format. Please enter a 3-digit numeric ID.")
            return

        if student_id in self.students:
            print("Student ID already exists. Please enter a unique ID.")
            return

        self.c.execute("INSERT INTO students (id, name) VALUES (?, ?)", (student_id, student_name))
        self.conn.commit()
        self.students[student_id] = student_name
        print(f"Student '{student_name}' with ID '{student_id}' has been added.")

    def mark_attendance(self):
        date = input("Enter the date for attendance (YYYY-MM-DD): ")
        if not self.validate_date(date):
            print("Invalid date format. Please enter a valid date in YYYY-MM-DD format.")
            return

        session = input("Enter session (forenoon or afternoon): ").strip().lower()
        if session not in ['forenoon', 'afternoon']:
            print("Invalid session. Please enter 'forenoon' or 'afternoon'.")
            return

        # Check if attendance has already been marked for this date and session
        self.c.execute("SELECT COUNT(*) FROM attendance WHERE date = ? AND session = ?", (date, session))
        attendance_count = self.c.fetchone()[0]

        if attendance_count > 0:
            print(f"Attendance has already been marked for {date} ({session}) session. Please choose another date or session.")
            return

        if not self.students:
            print("No students found! Add students first.")
            return

        attendance_data = {}
        print("\nMark attendance (p = present, a = absent):")
        for student_id, student_name in self.students.items():
            while True:
                status = input(f"Student: {student_name} (ID: {student_id}) - Present (p) or Absent (a): ").lower()
                if status in ['p', 'a']:
                    attendance_data[student_id] = 'Present' if status == 'p' else 'Absent'
                    self.c.execute("INSERT INTO attendance (date, student_id, status, session) VALUES (?, ?, ?, ?)", (date, student_id, attendance_data[student_id], session))
                    break
                else:
                    print("Invalid input. Please enter 'p' for present or 'a' for absent.")

        self.conn.commit()
        print(f"Attendance for {date} ({session} session) has been marked.")

    def view_attendance_statistics(self):
        student_stats = {}
        self.c.execute("SELECT student_id, status, COUNT(*) FROM attendance GROUP BY student_id, status")
        stats = self.c.fetchall()

        for student_id, status, count in stats:
            if student_id not in student_stats:
                student_stats[student_id] = {"Present": 0, "Absent": 0}
            student_stats[student_id][status] += count

        print("\n--- Attendance Statistics ---")
        for student_id, stats in student_stats.items():
            print(f"Student ID: {student_id} - Present: {stats['Present']} days, Absent: {stats['Absent']} days")

    def edit_student_info(self):
        student_id = input("Enter the student ID of the student to edit: ")
        if student_id not in self.students:
            print("Student not found.")
            return

        new_name = input("Enter the new name (leave blank to keep the current name): ")
        new_id = input("Enter the new ID (leave blank to keep the current ID): ")

        if new_name:
            self.c.execute("UPDATE students SET name = ? WHERE id = ?", (new_name, student_id))
            self.conn.commit()
            self.students[student_id] = new_name
        if new_id and new_id != student_id:
            if new_id in self.students:
                print("New ID already exists. Please choose a unique ID.")
                return
            self.c.execute("UPDATE students SET id = ? WHERE id = ?", (new_id, student_id))
            self.conn.commit()
            self.students[new_id] = self.students.pop(student_id)

        print("Student information updated.")

    def remove_student(self):
        if not self.authenticate():
            print("Incorrect password. Access denied.")
            return

        student_id = input("Enter the student ID of the student to remove: ")
        if student_id not in self.students:
            print("Student not found.")
            return

        self.c.execute("DELETE FROM students WHERE id = ?", (student_id,))
        self.conn.commit()
        del self.students[student_id]
        print(f"Student with ID '{student_id}' has been removed.")

    def delete_all_students(self):
        if not self.authenticate():
            print("Incorrect password. Access denied.")
            return
        self.c.execute("DELETE FROM students")
        self.conn.commit()
        self.students.clear()
        print("All student records have been deleted.")

    def delete_all_attendance_records(self):
        if not self.authenticate():
            print("Incorrect password. Access denied.")
            return
        self.c.execute("DELETE FROM attendance")
        self.conn.commit()
        print("All attendance records have been deleted.")

    def validate_date(self, date_text):
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def view_all_students(self):
        print("\n--- All Students ---")
        for student_id, student_name in self.students.items():
            print(f"ID: {student_id}, Name: {student_name}")

    def main_menu(self):
        while True:
            print("\n--- Attendance Tracker ---")
            print("1. Add Student")
            print("2. Mark Attendance")
            print("3. View Attendance Statistics")
            print("4. Edit Student Information")
            print("5. View All Students")
            print("6. Remove Student")
            print("7. Delete All Students")
            print("8. Delete All Attendance Records")
            print("9. Exit")

            choice = input("Choose an option: ")

            if choice == '1':
                student_id = input("Enter student ID (3 digits): ")
                student_name = input("Enter student name: ")
                self.add_student(student_id, student_name)
            elif choice == '2':
                self.mark_attendance()
            elif choice == '3':
                self.view_attendance_statistics()
            elif choice == '4':
                self.edit_student_info()
            elif choice == '5':
                self.view_all_students()
            elif choice == '6':
                self.remove_student()
            elif choice == '7':
                self.delete_all_students()
            elif choice == '8':
                self.delete_all_attendance_records()
            elif choice == '9':
                print("Exiting...")
                self.conn.close()
                break
            else:
                print("Invalid option. Please try again.")

if __name__ == "__main__":
    tracker = AttendanceTracker()
    tracker.main_menu()