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

    // Function to book a ticket
    void bookTicket()
    {
        cout << "\nEnter Movie Name: ";
        cin >> ws;
        getline(cin, movieName);

        cout << "Enter Seat Number (A1-J30): ";
        cin >> seatNumber;

        // Extract row letter
        char row = seatNumber[0];

        // Extract seat number
        int seatNo = stoi(seatNumber.substr(1));

        // Convert row letter into row number
        int rowNumber = row - 'A' + 1;

        // Validate seat number
        if (rowNumber < 1 || rowNumber > 10 ||
            seatNo < 1 || seatNo > 30)
        {
            cout << "Invalid Seat Number!" << endl;
            ticketPrice = 0;
            return;
        }

        // Calculate ticket price according to row
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
        cin >> ws;
        getline(cin, customerName);
    }

    // Function to display ticket details
    void printTicket()
    {
        cout << "\n========================================";
        cout << "\n          CINEMA TICKET RECEIPT";
        cout << "\n========================================";
        cout << "\nMovie Name    : " << movieName;
        cout << "\nSeat Number   : " << seatNumber;
        cout << "\nCustomer Name : " << customerName;
        cout << "\nTicket Price  : Rs. " << ticketPrice;
        cout << "\n========================================\n";
    }

    // Function to return ticket price
    int getPrice()
    {
        return ticketPrice;
    }
};

int main()
{
    // Array of 5 Ticket objects
    Ticket tickets[5];

    int totalRevenue = 0;

    cout << "========================================";
    cout << "\n     CINEMA TICKET BOOKING SYSTEM";
    cout << "\n========================================\n";

    // Booking 5 tickets
    for (int i = 0; i < 5; i++)
    {
        cout << "\n--------- Booking " << i + 1 << " ---------\n";

        tickets[i].bookTicket();

        // If invalid seat is entered
        if (tickets[i].getPrice() == 0)
        {
            cout << "Booking failed. Please enter a valid seat.\n";
            i--;
        }
    }

    // Display all ticket receipts
    cout << "\n\n******** ALL TICKET RECEIPTS ********\n";

    for (int i = 0; i < 5; i++)
    {
        tickets[i].printTicket();

        // Calculate total revenue
        totalRevenue += tickets[i].getPrice();
    }

    // Display total revenue
    cout << "\n========================================";
    cout << "\nTotal Revenue from 5 Bookings: Rs. "
         << totalRevenue;
    cout << "\n========================================\n";

    return 0;
}