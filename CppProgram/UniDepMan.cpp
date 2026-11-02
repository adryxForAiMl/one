
#include <iostream>
#include <string>
using namespace std;

// Faculty Class
class Faculty {
private:
    string facultyName;
    int facultyID;

public:
    Faculty(string name, int id) {
        facultyName = name;
        facultyID = id;
    }

    void displayFaculty() {
        cout << "\nFaculty Name : " << facultyName << endl;
        cout << "Faculty ID     : " << facultyID << endl;
    }
};

// Office Class
class Office {
private:
    int roomNumber;
    int capacity;

public:
    Office(int room, int cap) {
        roomNumber = room;
        capacity = cap;
    }

    void displayOffice() {
        cout << "\nOffice Room Number : " << roomNumber << endl;
        cout << "Office Capacity      : " << capacity << endl;
    }
};

// Department Class
class Department {
private:
    string departmentName;

    // Aggregation
    Faculty *faculty;

    // Composition
    Office office;

    // Nested Class
    class DepartmentInfo {
    private:
        string buildingName;
        int floorNumber;

    public:
        DepartmentInfo(string building, int floor)
            : buildingName(building), floorNumber(floor) {
        }

        void displayBuilding() {
            cout << "\nBuilding Name : " << buildingName << endl;
            cout << "Floor Number    : " << floorNumber << endl;
        }
    };

    DepartmentInfo info;

public:
    // Member Initializer List
    Department(string dept, Faculty *f, int room, int cap,
               string building, int floor)
        : departmentName(dept),
          faculty(f),
          office(room, cap),
          info(building, floor) {
    }

    void displayDepartment() {
        cout << "\n====== UNIVERSITY DEPARTMENT DETAILS ======\n";

        cout << "Department Name : " << departmentName << endl;

        cout << "\n----- Faculty Details -----";
        faculty->displayFaculty();

        cout << "\n----- Office Details -----";
        office.displayOffice();

        cout << "\n----- Building Information -----";
        info.displayBuilding();

        cout << "\n===========================================\n";
    }
};

// Main Function
int main() {

    // Creating Faculty Object Independently
    Faculty f1("Aditya Kumar", 23);

    // Creating Department Object
    Department d1("Computer Science", &f1, 257, 50,
                  "Academic Block A", 2);

    // Displaying Department Details
    d1.displayDepartment();

    return 0;
}
