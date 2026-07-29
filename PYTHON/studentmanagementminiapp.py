students=[]
def add_student():
    try:
        name=input("Enter the student name: ")
        marks=int(input("Enter marks: "))
        students.append({"name":name,"marks":marks})
        print("Student added successfully")
    except ValueError:
        print("Marks musdt be a number")

def view_student():
    if not students:
        print("No student available")
    else:
        for s in students:
            print(s["name"],"->",s["marks"])

def search_student():
    name=input("Enter name to search")
    for s in students:
        if s["name"].lower()==name.lower():
            print("Found: ",s["name"],s["marks"])
            return
        print("Student not found")

def avg_marks():
    if not students:
        print("No data to calculate average marks")
        return
    total=sum(s["marks"] for s in students)
    average=total/len(students)
    print("Average marks: ",average)

while True:
    print("\n 1. Add Students")
    print("\n 2. View Students")
    print("\n 3. Search Students")
    print("\n 4. AverageStudents")
    print("\n 5. Exit")

    choice=input("enter choice: ")

    match choice:
        case "1":
            add_student()
        case "2":
            view_student()
        case "3":
            search_student()
        case "4":
            avg_marks()
        case "5":
            print("existing the program,Bye")
            break
        case _:
            print("Invalid choice")
        
