#include <iostream>
using namespace std;

class Student
{
    int roll;
    string name;
    float marks;
  public:
    void input()
    {
        cout << "Enter Roll: ";
        cin >> roll;

        cout << "Enter Name: ";
        getline(cin>>ws,name);

        cout << "Enter Marks: ";
        cin >> marks;
    }

    void display()
    {
        cout << "\nStudent Details\n";
        cout << "Roll    : " << roll << endl;
        cout << "Name    : " << name << endl;
        cout << "Marks   : " << marks << endl;
    }
};

int main()
{
    Student s;
    s.input();
    s.display();

    return 0;
}