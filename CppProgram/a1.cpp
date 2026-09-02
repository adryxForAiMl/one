#include <iostream>
#include <string>
using namespace std;

class Ticket
{
private:
    string movieName;
    string seatNumber;
    string customerName;
    int ticketPrice;

public:
    void bookTicket()
    {
        cout << "Enter Movie Name: ";
        getline(cin >> ws, movieName);

        while (true)
        {
            cout << "Enter Seat Number (A1 - J30): ";
            cin >> seatNumber;

            char row = seatNumber[0];
            int seatNo = stoi(seatNumber.substr(1));
            int rowNumber = row - 'A' + 1;

            if (rowNumber < 1 || rowNumber > 10 || seatNo < 1 || seatNo > 30)
            {
                cout << "Invalid seat no.! Please enter again.\n";
            }
            else
            {
                break;
            }
        }

        char row = seatNumber[0];
        int rowNumber = row - 'A' + 1;

        if (rowNumber >= 1 && rowNumber <= 3)
        {
            ticketPrice = 2500;
        }
        else if (rowNumber >= 4 && rowNumber <= 6)
        {
            ticketPrice = 3000;
        }
        else
        {
            ticketPrice = 4000;
        }

        cout << "Enter Customer Name: ";
        getline(cin >> ws, customerName);
    }

    void printTicket()
    {
        cout << "\n ~ CINEMA TICKET RECEIPT ~ \n" << endl;
        cout << "Movie Name: " << movieName << endl;
        cout << "Seat Number: " << seatNumber << endl;
        cout << "Customer Name: " << customerName << endl;
        cout << "Ticket Price: " << ticketPrice << endl;
    }

    int getPrice()
    {
        return ticketPrice;
    }
};

int main()
{
    Ticket tickets[5];
    int totalRevenue = 0;

    cout << " ~ CINEMA TICKET BOOKING SYSTEM ~ \n" << endl;

    for (int i = 0; i < 5; i++)
    {
        cout << "    Booking " << i + 1 << endl;
        tickets[i].bookTicket();
    }

    cout << "All Tickets Receipts" << endl;

    for (int i = 0; i < 5; i++)
    {
        tickets[i].printTicket();
        totalRevenue += tickets[i].getPrice();
    }

    cout << "Revenue from 5 bookings: " << totalRevenue << endl;

    return 0;
}