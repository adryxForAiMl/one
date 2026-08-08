#include <iostream>
#include <string>
#include <vector>
#include <memory>
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

        virtual ~Item() {
            cout << "Item destroyed: " << title << endl;
        }
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
        vector<string> borrowedItemIds;   // tracks which item IDs this member has borrowed

    public:
        Member(string name, string memberId) {
            this->name = name;
            this->memberId = memberId;
        }

        string getMemberId() { return memberId; }
        string getName() { return name; }

        void addBorrowedItem(string itemId) {
            borrowedItemIds.push_back(itemId);
        }

        void removeBorrowedItem(string itemId) {
            for (int i = 0; i < borrowedItemIds.size(); i++) {
                if (borrowedItemIds[i] == itemId) {
                    borrowedItemIds.erase(borrowedItemIds.begin() + i);
                    break;
                }
            }
        }

        void displayBorrowedItems() {
            cout << name << "'s borrowed items: ";
            if (borrowedItemIds.empty()) {
                cout << "None";
            }
            for (string id : borrowedItemIds) {
                cout << id << " ";
            }
            cout << endl;
        }
};
class Library {
    private:
        vector<unique_ptr<Item>> items;     // Library OWNS its items (unique_ptr = exclusive ownership)
        vector<Member> members;              // Library manages its members directly

    public:
        // Add a new item to the library — takes ownership via move
        void addItem(unique_ptr<Item> item) {
            cout << "Added: " << item->getTitle() << endl;
            items.push_back(std::move(item));     // MOVE, not copy — unique_ptr can't be copied
        }

        void addMember(string name, string memberId) {
            members.push_back(Member(name, memberId));
        }

        // Find item by ID — returns raw pointer (non-owning, just for use)
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

            if (!item || !member) {
                cout << "Invalid item or member." << endl;
                return;
            }

            item->returnItem();
            member->removeBorrowedItem(itemId);
            cout << member->getName() << " returned \"" << item->getTitle() << "\"" << endl;
        }

        void displayAllItems() {
            cout << "\n--- Library Catalog ---" << endl;
            for (auto& item : items) {
                item->displayInfo();     // POLYMORPHISM — calls Book's or Magazine's version automatically
            }
        }
};
int main() {
    Library library;

    library.addItem(make_unique<Book>("The Hobbit", "B001", "J.R.R. Tolkien"));
    library.addItem(make_unique<Book>("1984", "B002", "George Orwell"));
    library.addItem(make_unique<Magazine>("National Geographic", "M001", 245));

    library.addMember("Aditya Kumar", "MEM001");

    library.displayAllItems();

    cout << endl;
    library.borrowItem("MEM001", "B001");
    library.borrowItem("MEM001", "M001");

    cout << endl;
    library.displayAllItems();

    Member* m = library.findMember("MEM001");
    if (m) m->displayBorrowedItems();

    cout << endl;
    library.returnItem("MEM001", "B001");
    library.displayAllItems();

    return 0;
}