// #include<iostream>
// using namespace std;

// class Student{
//     private:
//         string name;
//         int age;
//         int rollNumber;
//     public:
//         Student(string name,int age,int r){
//             this->name=name;
//             this->age=age;
//             setRollNumber(r);
//             studentCount++;
//         }

//         static int studentCount;


//         void setRollNumber(int r){
//             if(r>0){
//                 rollNumber=r;
//             }
//             else{
//                 cout << "Invalid  Roll Number" << endl;
//             }
//         }

//         int getRollnumber(){
//             return rollNumber;
//         }

//         ~Student(){
//             cout << name <<"'s object is being destroyed" << endl;
//             studentCount--;
//         }

//         void displayInfo(){
//             cout<< "Name: " << name <<" Age: " <<age << " RollNumber:" << rollNumber <<endl;
//         }

// };
// int Student::studentCount=0;
// int main(){
    
//     Student s1("Aditya Kumar",19,213);
//     Student s2("Peter Parker",21,1);
//     cout<<"Total student: " << Student::studentCount << endl;
    
 
//     s1.displayInfo();
//     s2.displayInfo();

//     return 0;
// }

// #include <iostream>
// #include <string>
// using namespace std;

// class Ticket
// {
// private:
//     string movieName;
//     int seatNumber;
//     string customerName;
//     float ticketPrice;

// public:

//     void bookTicket()
//     {
//         cout << "Enter Movie Name: ";
//         getline(cin >> ws, movieName);

//         cout << "Enter Seat Number: ";
//         cin >> seatNumber;

//         cout << "Enter Customer Name: ";
//         getline(cin >> ws, customerName);

//         cout << "Enter Ticket Price: ";
//         cin >> ticketPrice;
//     }

//     void printTicket()
//     {
//         cout << " \n        CINEMA TICKET RECEIPT        \n";
//         cout << "Movie Name    : " << movieName << endl;
//         cout << "Seat Number   : " << seatNumber << endl;
//         cout << "Customer Name : " << customerName << endl;
//         cout << "Ticket Price  : Rs. " << ticketPrice << endl;
//         cout << "================================\n";
//     }

//     float getPrice()
//     {
//         return ticketPrice;
//     }
// };

// int main()
// {
//     Ticket tickets[5];
//     float totalRevenue = 0;

//     cout << "\n===== CINEMA TICKET BOOKING =====\n";

//     // Input for 5 tickets
//     for(int i = 0; i < 5; i++)
//     {
//         cout << "\nBooking " << i + 1 << endl;
//         tickets[i].bookTicket();
//     }

//     // Display receipts and calculate revenue
//     cout << "\n\n===== ALL TICKET RECEIPTS =====\n";

//     for(int i = 0; i < 5; i++)
//     {
//         tickets[i].printTicket();
//         totalRevenue = totalRevenue + tickets[i].getPrice();
//     }

//     cout << "\nTotal Revenue Collected = Rs. "
//          << totalRevenue << endl;

//     return 0;
// }
// ===

#include<iostream>
using namespace std;

class Account{
    public:
      int balance;

    Account(){
        balance=2000;
    }
    Account(int amount){
            balance=amount;
        }
    
    
};
int main(){
    Account a1,a2(3000);
    cout<< a1.balance << endl;
    cout<< a2.balance << endl;
    return 0;
}
