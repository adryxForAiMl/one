#include <iostream>
using namespace std;

class student{
    public:
    int rollNo;
    float marks;
    string name;

    void display(){
        cout<<"Roll Number: "<<rollNo<<endl;
        cout<<"Marks: "<<marks<<endl;
        cout<<"Name: "<<name<<endl;
    }

};

int main(){
    student s1;
    s1.name="Aditya";
    s1.marks=100;
    s1.rollNo=213;

    s1.display();

    return 0;

}
