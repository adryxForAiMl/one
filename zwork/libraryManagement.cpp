#include <iostream>
#include <string>
#include <vector>
#include <memory>
#include <exception>
#include <utility>
using namespace std;

class Item {
    protected:
        string title;
        string itemId;
        bool isBorrowed;

    public:
        Item(string title, string itemId) {
            this->title = title;
            this->itemId = itemId;
            this->isBorrowed = false;
        }

        virtual void displayInfo() = 0;   // pure virtual — forces every item type to define its own

        virtual string getItemType() = 0; // pure virtual — "Book", "Magazine", etc.

        bool getIsBorrowed() { return isBorrowed; }
        string getItemId() { return itemId; }
        string getTitle() { return title; }

        void borrowItem() {
            isBorrowed = true;
        }

        void returnItem() {
            isBorrowed = false;
        }

        virtual ~Item() = default;
};
class Book : public Item {
    private:
        string author;

    public:
        Book(string title, string itemId, string author) : Item(title, itemId) {
            this->author = author;
        }

        void displayInfo() override {
            cout << "[Book] \"" << title << "\" by " << author 
                 << " (ID: " << itemId << ") - " 
                 << (isBorrowed ? "Borrowed" : "Available") << endl;
        }

        string getItemType() override {
            return "Book";
        }
};

class Magazine : public Item {
    private:
        int issueNumber;

    public:
        Magazine(string title, string itemId, int issueNumber) : Item(title, itemId) {
            this->issueNumber = issueNumber;
        }

        void displayInfo() override {
            cout << "[Magazine] \"" << title << "\" Issue #" << issueNumber 
                 << " (ID: " << itemId << ") - " 
                 << (isBorrowed ? "Borrowed" : "Available") << endl;
        }

        string getItemType() override {
            return "Magazine";
        }
};
class Member {
    private:
        string name;
        string memberId;
        vector<string> borrowedItemIds;

    public:
        Member(string name, string memberId)
            : name(std::move(name)), memberId(std::move(memberId)) {}

        string getMemberId() const { return memberId; }
        string getName() const { return name; }

        bool hasBorrowedItem(const string& itemId) const {
            for (const string& borrowedId : borrowedItemIds) {
                if (borrowedId == itemId) {
                    return true;
                }
            }
            return false;
        }

        void addBorrowedItem(const string& itemId) {
            borrowedItemIds.push_back(itemId);
        }

        void removeBorrowedItem(const string& itemId) {
            for (auto item = borrowedItemIds.begin(); item != borrowedItemIds.end(); ++item) {
                if (*item == itemId) {
                    borrowedItemIds.erase(item);
                    return;
                }
            }
        }

        void displayBorrowedItems() const {
            cout << "  Borrowed item IDs: ";
            if (borrowedItemIds.empty()) {
                cout << "None";
            } else {
                for (const string& id : borrowedItemIds) {
                    cout << id << " ";
                }
            }
            cout << endl;
        }
};
class Library {
    private:
        vector<unique_ptr<Item>> items;     // Library OWNS its items (unique_ptr = exclusive ownership)
        vector<Member> members;              // Library manages its members directly

    public:
        void addItem(unique_ptr<Item> item) {
            if (!item) {
                return;
            }
            if (findItem(item->getItemId())) {
                cout << "An item with that ID already exists.\n";
                return;
            }
            cout << "Added: " << item->getTitle() << " (" << item->getItemId() << ")\n";
            items.push_back(std::move(item));
        }

        void addMember(string name, string memberId) {
            if (findMember(memberId)) {
                cout << "A member with that ID already exists.\n";
                return;
            }
            members.push_back(Member(name, memberId));
            cout << "Registered member: " << name << " (" << memberId << ")\n";
        }

        Item* findItem(string itemId) {
            for (auto& item : items) {
                if (item->getItemId() == itemId) {
                    return item.get();       // .get() gives a raw pointer WITHOUT transferring ownership
                }
            }
            return nullptr;
        }

        Member* findMember(string memberId) {
            for (auto& member : members) {
                if (member.getMemberId() == memberId) {
                    return &member;
                }
            }
            return nullptr;
        }

        void borrowItem(string memberId, string itemId) {
            Item* item = findItem(itemId);
            Member* member = findMember(memberId);

            if (!item) {
                cout << "Item not found." << endl;
                return;
            }
            if (!member) {
                cout << "Member not found." << endl;
                return;
            }
            if (item->getIsBorrowed()) {
                cout << "Item already borrowed." << endl;
                return;
            }

            item->borrowItem();
            member->addBorrowedItem(itemId);
            cout << member->getName() << " borrowed \"" << item->getTitle() << "\"" << endl;
        }

        void returnItem(string memberId, string itemId) {
            Item* item = findItem(itemId);
            Member* member = findMember(memberId);

            if (!item) {
                cout << "Item not found.\n";
                return;
            }
            if (!member) {
                cout << "Member not found.\n";
                return;
            }
            if (!member->hasBorrowedItem(itemId)) {
                cout << "This member has not borrowed that item.\n";
                return;
            }

            item->returnItem();
            member->removeBorrowedItem(itemId);
            cout << member->getName() << " returned \"" << item->getTitle() << "\"" << endl;
        }

        void displayAllItems() {
            cout << "\n--- Library Catalog ---" << endl;
            if (items.empty()) {
                cout << "No items in the library yet.\n";
                return;
            }
            for (auto& item : items) {
                item->displayInfo();
            }
        }

        void displayMembers() {
            cout << "\n--- Library Members ---\n";
            if (members.empty()) {
                cout << "No members registered yet.\n";
                return;
            }
            for (const Member& member : members) {
                cout << member.getName() << " (" << member.getMemberId() << ")\n";
                member.displayBorrowedItems();
            }
        }

        void searchItems(const string& query) {
            bool found = false;
            for (const auto& item : items) {
                if (item->getItemId() == query || item->getTitle().find(query) != string::npos) {
                    item->displayInfo();
                    found = true;
                }
            }
            if (!found) {
                cout << "No matching items found.\n";
            }
        }
};

bool readText(const string& prompt, string& value) {
    cout << prompt;
    return static_cast<bool>(getline(cin, value));
}

bool readInteger(const string& prompt, int& value) {
    string input;
    while (readText(prompt, input)) {
        try {
            size_t parsedCharacters = 0;
            int parsedValue = stoi(input, &parsedCharacters);
            if (parsedCharacters == input.size()) {
                value = parsedValue;
                return true;
            }
        } catch (const exception&) {
        }
        cout << "Please enter a valid number.\n";
    }
    return false;
}

int main() {
    Library library;
    int choice;

    while (true) {
        cout << "\n===== Library Management System =====\n"
             << "1. Add book\n"
             << "2. Add magazine\n"
             << "3. Register member\n"
             << "4. Display catalog\n"
             << "5. Display members\n"
             << "6. Issue item\n"
             << "7. Return item\n"
             << "8. Search catalog\n"
             << "0. Exit\n";

        if (!readInteger("Choose an option: ", choice)) {
            cout << "\nInput ended. Exiting.\n";
            break;
        }

        string title;
        string itemId;
        string name;
        string memberId;
        string author;
        int issueNumber;

        switch (choice) {
            case 1:
                if (!readText("Book title: ", title) ||
                    !readText("Book ID: ", itemId) ||
                    !readText("Author: ", author)) {
                    return 0;
                }
                library.addItem(make_unique<Book>(title, itemId, author));
                break;
            case 2:
                if (!readText("Magazine title: ", title) ||
                    !readText("Magazine ID: ", itemId) ||
                    !readInteger("Issue number: ", issueNumber)) {
                    return 0;
                }
                if (issueNumber <= 0) {
                    cout << "Issue number must be positive.\n";
                    break;
                }
                library.addItem(make_unique<Magazine>(title, itemId, issueNumber));
                break;
            case 3:
                if (!readText("Member name: ", name) ||
                    !readText("Member ID: ", memberId)) {
                    return 0;
                }
                library.addMember(name, memberId);
                break;
            case 4:
                library.displayAllItems();
                break;
            case 5:
                library.displayMembers();
                break;
            case 6:
                if (!readText("Member ID: ", memberId) ||
                    !readText("Item ID: ", itemId)) {
                    return 0;
                }
                library.borrowItem(memberId, itemId);
                break;
            case 7:
                if (!readText("Member ID: ", memberId) ||
                    !readText("Item ID: ", itemId)) {
                    return 0;
                }
                library.returnItem(memberId, itemId);
                break;
            case 8:
                if (!readText("Search by title or item ID: ", title)) {
                    return 0;
                }
                library.searchItems(title);
                break;
            case 0:
                cout << "Goodbye.\n";
                return 0;
            default:
                cout << "Invalid option. Choose a number from 0 to 8.\n";
        }
    }

    return 0;
}