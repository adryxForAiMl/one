#include<iostream>
using namespace std;

class Student{
    private:
        string name;
        int age;
        int rollNumber;
    public:
        Student(string name,int age,int r){
            this->name=name;
            this->age=age;
            setRollNumber(r);
            studentCount++;
        }

        static int studentCount;


        void setRollNumber(int r){
            if(r>0){
                rollNumber=r;
            }
            else{
                cout << "Invalid  Roll Number" << endl;
            }
        }

        int getRollnumber(){
            return rollNumber;
        }

        ~Student(){
            cout << name <<"'s object is being destroyed" << endl;
            studentCount--;
        }

        void displayInfo(){
            cout<< "Name: " << name <<" Age: " <<age << " RollNumber:" << rollNumber <<endl;
        }

};
int Student::studentCount=0;
int main(){
    
    Student s1("Aditya Kumar",19,213);
    Student s2("Peter Parker",21,1);
    cout<<"Total student: " << Student::studentCount << endl;
    
 
    s1.displayInfo();
    s2.displayInfo();

    return 0;
}

