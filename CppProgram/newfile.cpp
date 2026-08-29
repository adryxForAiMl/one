#include<iostream>
#include<string>
using namespace std;

class WordAnalyser
{
    string sentence;

public:
    WordAnalyser(string s)
    {
        cout << "Enter the sentence to calculate the words: ";
        getline(cin >> ws, sentence);

    }

    void splitIntoWords(string sentence,string words[])
    {

    }
    void foundLongestWord(string words[],int n)
    {

    }
};
int main()
{
    WordAnalyser w1 ;
    return 0;


}
