#include<iostream>
using namespace std;

class Hospital{
public:
    string patientName;
    int age;
    string doctorName;
    int appointmentTime;
    int tokenNumber;


    Hospital(){
    patientName="Not available";
    age=0;
    doctorName= "Not available";
    appointmentTime=0;
    tokenNumber=0;
    }

    Hospital(string pName, int pAge, string dName, int time, int tNumber){
    patientName= pName;
    age=pAge;
    doctorName= dName;
    appointmentTime=time;
    tokenNumber=tNumber;
    }



    void BookAppointment(){
        cout<< "Enter patient name" <<endl;
        getline(cin >> ws,patientName);

        cout<< "Enter age" << endl;
        cin>> age ;

        cout<< "Enter doctor name" << endl;
        getline(cin >> ws , doctorName);

        cout<< "Enter appointment time " << endl;
        cin >> appointmentTime;

        cout<< "Enter token number" << endl;
        cin>> tokenNumber;


    }
    void Display(){
        cout<< "Patient name        : " << patientName << endl;
        cout<< "Age                 : " << age << endl;
        cout<< "Doctor Name         : " << doctorName << endl;
        cout<< "Appointment time    : " << appointmentTime << endl;
        cout<< "Token number        : " << tokenNumber << endl;
     

    }

    

};
int main(){

    Hospital p1, p2("Aditya", 17, "Dr ABC", 900, 12);
    p1.Display();
    p2.Display();

    
    return 0;
}
