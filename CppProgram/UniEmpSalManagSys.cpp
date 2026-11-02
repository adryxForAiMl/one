
#include <iostream>
#include <string>
using namespace std;

// Base Class
class Person {
protected:
    string name;
    int employeeID;

public:
    Person(string n, int id) {
        name = n;
        employeeID = id;
    }

    void displayPerson() {
        cout << "Name        : " << name << endl;
        cout << "Employee ID : " << employeeID << endl;
    }

    string getName() {
        return name;
    }
};

// First Derived Class
class TeachingStaff : virtual public Person {
protected:
    string subject;

public:
    TeachingStaff(string n, int id, string sub)
        : Person(n, id) {
        subject = sub;
    }

    void displayTeaching() {
        cout << "Subject     : " << subject << endl;
    }
};

// Second Derived Class
class ResearchStaff : virtual public Person {
protected:
    string researchArea;

public:
    ResearchStaff(string n, int id, string area)
        : Person(n, id) {
        researchArea = area;
    }

    void displayResearch() {
        cout << "Research Area : " << researchArea << endl;
    }
};

// Derived Class using Multiple Inheritance
class Professor : public TeachingStaff, public ResearchStaff {
private:
    float monthlySalary;

public:
    Professor(string n, int id, string sub,
              string area, float salary)
        : Person(n, id),
          TeachingStaff(n, id, sub),
          ResearchStaff(n, id, area) {

        monthlySalary = salary;
    }

    void displayProfessor() {
        cout << "\n----- PROFESSOR DETAILS -----\n";

        displayPerson();
        displayTeaching();
        displayResearch();

        cout << "Monthly Salary : Rs. "
             << monthlySalary << endl;
    }

    // Friend Function
    friend void compareSalary(Professor p1, Professor p2);
};

// Friend Function Definition
void compareSalary(Professor p1, Professor p2) {

    cout << "\n====== SALARY COMPARISON ======\n";

    if (p1.monthlySalary > p2.monthlySalary) {

        cout << p1.getName() << " earns more salary.\n";
        cout << "Salary : Rs. " << p1.monthlySalary << endl;

    }
    else if (p2.monthlySalary > p1.monthlySalary) {

        cout << p2.getName() << " earns more salary.\n";
        cout << "Salary : Rs. " << p2.monthlySalary << endl;

    }
    else {

        cout << "Both professors have equal salaries.\n";
        cout << "Salary : Rs. " << p1.monthlySalary << endl;
    }

    cout << "===============================\n";
}

// Main Function
int main() {

    Professor p1("Peter Parker", 101,
                 "Computer Science",
                 "Artificial Intelligence",
                 85000);

    Professor p2("Deamon", 102,
                 "Mathematics",
                 "Machine Learning",
                 95000);

    cout << "\n===== UNIVERSITY PROFESSOR RECORDS =====\n";

    p1.displayProfessor();

    p2.displayProfessor();

    compareSalary(p1, p2);

    return 0;
}
