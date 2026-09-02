#include <iostream>
#include <string>
#include <iomanip>
using namespace std;

class Appointment
{
public:
    string patientName;
    int age;
    string doctorName;
    int appointmentTime;
    int tokenNumber;

    // Default Constructor
    Appointment()
    {
        patientName = "Not Available";
        age = 0;
        doctorName = "Not Available";
        appointmentTime = 0;
        tokenNumber = 0;
    }

    // Parameterized Constructor
    Appointment(string pName, int pAge, string dName, int time, int tNumber)
    {
        patientName = pName;
        age = pAge;
        doctorName = dName;
        appointmentTime = time;
        tokenNumber = tNumber;
    }

    // Schedule Appointment
    void scheduleAppointment()
    {
        cout << "\nEnter patient name: ";
        getline(cin >> ws, patientName);

        cout << "Enter age: ";
        cin >> age;

        cout << "Enter doctor name: ";
        getline(cin >> ws, doctorName);

        cout << "Enter appointment time (e.g. 900 for 9:00): ";
        cin >> appointmentTime;

        cout << "Enter token number: ";
        cin >> tokenNumber;
    }

    // Display Appointment
    void displayAppointment()
    {
        cout << "Patient Name     : " << patientName << endl;
        cout << "Age              : " << age << endl;
        cout << "Doctor Name      : " << doctorName << endl;
        cout << "Appointment Time : " << appointmentTime << endl;
        cout << "Token Number     : " << tokenNumber << endl;
    }

    // Check Appointment Conflict
    bool isConflict(Appointment other)
    {
        if (doctorName == other.doctorName &&
            appointmentTime == other.appointmentTime)
        {
            return true;
        }

        return false;
    }
};

int main()
{
    // Create an array of 8 Appointment objects
    Appointment appointments[8] =
    {
        Appointment("Aditya", 19, "Dr. ABC", 900, 1),
        Appointment("Sadie", 19, "Dr. ABC", 1030, 2),
        Appointment("Peter", 21, "Dr. XYZ", 1200, 3),
        Appointment("Alice", 20, "Dr. DEF", 1100, 4),
        Appointment(),
        Appointment(),
        Appointment(),
        Appointment()
    };

    // Input remaining four appointments
    for (int i = 4; i < 8; i++)
    {
        cout << "\nEnter details for Appointment " << i + 1;
        appointments[i].scheduleAppointment();

        // Check conflict with previous appointments
        for (int j = 0; j < i; j++)
        {
            if (appointments[i].isConflict(appointments[j]))
            {
                cout << "\n*** APPOINTMENT CONFLICT FOUND ***\n";
                cout << "New Appointment     : "
                     << appointments[i].patientName << endl;

                cout << "Previous Appointment : "
                     << appointments[j].patientName << endl;

                cout << "Doctor               : "
                     << appointments[i].doctorName << endl;

                cout << "Appointment Time     : "
                     << appointments[i].appointmentTime << endl;
            }
        }
    }

    // Bubble Sort appointments by appointment time
    for (int i = 0; i < 7; i++)
    {
        for (int j = 0; j < 7 - i; j++)
        {
            if (appointments[j].appointmentTime >
                appointments[j + 1].appointmentTime)
            {
                Appointment temp = appointments[j];

                appointments[j] = appointments[j + 1];

                appointments[j + 1] = temp;
            }
        }
    }

    // Display final appointment schedule
    cout << "\n                 FINAL APPOINTMENT SCHEDULE\n\n";

    cout << left
         << setw(18) << "Patient Name"
         << setw(8) << "Age"
         << setw(18) << "Doctor Name"
         << setw(18) << "Appointment Time"
         << setw(12) << "Token"
         << endl;

    cout << "------------------------------------------------------------------\n";

    for (int i = 0; i < 8; i++)
    {
        cout << left
             << setw(18) << appointments[i].patientName
             << setw(8) << appointments[i].age
             << setw(18) << appointments[i].doctorName
             << setw(18) << appointments[i].appointmentTime
             << setw(12) << appointments[i].tokenNumber
             << endl;
    }

    cout << "\n----------------------------------------------------------------\n";

    return 0;
}