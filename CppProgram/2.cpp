#include <iostream>
#include <string>
using namespace std;

class BankAccount {
public:
    int accountNo;
    string customerName;
    double balance;

    void createAccount(int actNum, string cusNam, double amt) {
        accountNo = actNum;
        customerName = cusNam;
        balance = amt;
    }

    void display() {
        cout << "Customer Name: " << customerName << endl;
        cout << "Account No.: " << accountNo << endl;
        cout << "Balance: " << balance << endl;
    }

    void withdraw() {
        double amount;
        cout << "Enter the amount to withdraw: ";
        cin >> amount;

        if (amount <= balance) {
            balance -= amount;
            cout << "Net Balance: " << balance << endl;
        } else {
            cout << "Insufficient balance!" << endl;
            cout << "Available Balance: " << balance << endl;
        }
    }

    void deposit() {
        double amount;
        cout << "Enter the amount to deposit: ";
        cin >> amount;

        balance += amount;
        cout << "Net Balance: " << balance << endl;
    }
};

int main() {
    BankAccount c1;
    int account_num;
    double amount;
    string customer_name;

    cout << "Enter the Account No.: ";
    cin >> account_num;
    cin.ignore();

    cout << "Enter the Customer Name: ";
    getline(cin, customer_name);

    cout << "Enter Initial Amount: ";
    cin >> amount;

    c1.createAccount(account_num, customer_name, amount);

    c1.display();

    // Example operations
    c1.deposit();
    c1.withdraw();

    cout << "\nUpdated Account Details:\n";
    c1.display();

    return 0;
}