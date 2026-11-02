
#include <iostream>
#include <string>
using namespace std;

class FoodOrder {
protected:
    int orderID;
    string customerName;
    int numberOfItems;

public:
    FoodOrder(int id, string name, int n) {
        orderID = id;
        customerName = name;
        numberOfItems = n;
    }
};

class RestaurantOrder : public FoodOrder {
private:
    string restaurantName;
    string itemName[5];
    int quantity[5];
    float price[5];

public:
    RestaurantOrder(int id, string name, int n, string restaurant)
        : FoodOrder(id, name, n) {
        restaurantName = restaurant;
    }

    void acceptDetails() {
        for (int i = 0; i < numberOfItems; i++) {
            cout << "\nEnter Food Item " << i + 1 << " Name: ";
            getline(cin >> ws, itemName[i]);

            cout << "Enter Quantity: ";
            cin >> quantity[i];

            cout << "Enter Price Per Item: ";
            cin >> price[i];
        }
    }

    void generateBill() {
        float totalFoodCost = 0;
        float itemCost[5];

        for (int i = 0; i < numberOfItems; i++) {
            itemCost[i] = quantity[i] * price[i];
            totalFoodCost += itemCost[i];
        }

        float deliveryCharge;

        if (totalFoodCost < 300) {
            deliveryCharge = 50;
        }
        else if (totalFoodCost < 700) {
            deliveryCharge = 30;
        }
        else {
            deliveryCharge = 0;
        }

        float discount = 0;

        if (numberOfItems > 3) {
            discount = 50;
        }

        float finalBill = totalFoodCost + deliveryCharge - discount;

        cout << "\n========== FOOD DELIVERY BILL ==========\n";

        cout << "Order ID      : " << orderID << endl;
        cout << "Customer Name : " << customerName << endl;
        cout << "Restaurant    : " << restaurantName << endl;

        cout << "\n----------- ITEM DETAILS ---------------\n";

        for (int i = 0; i < numberOfItems; i++) {
            cout << "\nFood Item : " << itemName[i] << endl;
            cout << "Quantity    : " << quantity[i] << endl;
            cout << "Price       : Rs. " << price[i] << endl;
            cout << "Item Cost   : Rs. " << itemCost[i] << endl;
        }

        cout << "\n----------------------------------------\n";

        cout << "Total Food Cost : Rs. " << totalFoodCost << endl;
        cout << "Delivery Charge : Rs. " << deliveryCharge << endl;
        cout << "Discount        : Rs. " << discount << endl;

        cout << "----------------------------------------\n";

        cout << "Final Bill      : Rs. " << finalBill << endl;

        cout << "========================================\n";
    }
};

int main() {
    int id, n;
    string name, restaurant;

    cout << "Enter Order ID: ";
    cin >> id;

    cout << "Enter Customer Name: ";
    getline(cin >> ws, name);

    cout << "Enter Restaurant Name: ";
    getline(cin, restaurant);

    cout << "Enter Number of Different Food Items (1-5): ";
    cin >> n;

    if (n < 1 || n > 5) {
        cout << "Invalid Number of Items!";
        return 0;
    }

    RestaurantOrder order(id, name, n, restaurant);

    order.acceptDetails();
    order.generateBill();

    return 0;
}
