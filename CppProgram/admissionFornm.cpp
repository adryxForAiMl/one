#include<iostream>
using namespace std;

class student{
    public:
    int roll;
    string name;
    float marks;

    void input(){
        cout<<"Enter the roll number: " ;
        cin>>roll;
        cin.ignore();
        cout<<"Enter Name: ";
        getline(cin,name);
        cout<<"Enter marks:";
        cin>>marks;

    }

    void display(){
        cout <<"\n---Student details---"<<endl;
        cout<<"Roll number:"<<roll<<endl;
        cout<<"Name:"<<name<<endl;
        cout<<"Marks: "<<marks<<endl;



    }
};

int main(){
    student s1;
    s1.input();
    s1.display();
    return 0;

}