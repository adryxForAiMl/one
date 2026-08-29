#include <iostream>
#include <string>
using namespace std;

class Ticket {
private:
    string movieName;
    int seatNumber;
    string customerName;
    double ticketPrice;

public:
    // Function to book a ticket
    void bookTicket() {
        cin.ignore();

        cout << "Enter Movie Name: ";
        getline(cin, movieName);

        cout << "Enter Seat Number: ";
        cin >> seatNumber;
        cin.ignore();

        cout << "Enter Customer Name: ";
        getline(cin, customerName);

        cout << "Enter Ticket Price: ";
        cin >> ticketPrice;
    }

    // Function to print ticket details
    void printTicket() {
        cout << "\n==============================";
        cout << "\n      CINEMA TICKET";
        cout << "\n==============================";
        cout << "\nMovie Name    : " << movieName;
        cout << "\nCustomer Name : " << customerName;
        cout << "\nSeat Number   : " << seatNumber;
        cout << "\nTicket Price  : Rs. " << ticketPrice;
        cout << "\n==============================\n";
    }

    // Function to return ticket price
    double getPrice() {
        return ticketPrice;
    }
};

int main() {
    Ticket tickets[5];
    double totalRevenue = 0;

    cout << "===== Ticket Booking =====\n";

    // Read details of 5 tickets
    for (int i = 0; i < 5; i++) {
        cout << "\nBooking " << i + 1 << endl;
        tickets[i].bookTicket();
    }

    cout << "\n\n===== Ticket Receipts =====\n";

    // Display all tickets and calculate revenue
    for (int i = 0; i < 5; i++) {
        tickets[i].printTicket();
        totalRevenue += tickets[i].getPrice();
    }

    cout << "\nTotal Revenue Collected = Rs. " << totalRevenue << endl;

    return 0;
}