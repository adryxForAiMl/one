#include <iostream>
#include <string>
using namespace std;


// Function to split sentence into words
int splitIntoWords(string sentence, string words[])
{
    string currentWord = "";
    int wordCount = 0;

    for (int i = 0; i < sentence.length(); i++)
    {
        char ch = sentence[i];

        if (ch != ' ')
        {
            currentWord = currentWord + ch;
        }
        else
        {
            if (currentWord.length() > 0)
            {
                words[wordCount] = currentWord;
                wordCount++;

                currentWord = "";
            }
        }
    }

    // Store the last word
    if (currentWord.length() > 0)
    {
        words[wordCount] = currentWord;
        wordCount++;
    }

    return wordCount;
}


// Function to find the longest word
void findLongestWord(string words[], int n)
{
    if (n == 0)
    {
        cout << "No words found." << endl;
        return;
    }

    string longestWord = words[0];

    for (int i = 1; i < n; i++)
    {
        if (words[i].length() > longestWord.length())
        {
            longestWord = words[i];
        }
    }

    cout << "Longest Word: " << longestWord << endl;
    cout << "Length: " << longestWord.length() << endl;
}


int main()
{
    string sentence;
    string words[100];

    // Taking input from user
    cout << "Enter a sentence: ";
    getline(cin, sentence);

    // Calling first function
    int wordCount = splitIntoWords(sentence, words);

    cout << "\nTotal Words: " << wordCount << endl;

    cout << "\nWords are:" << endl;

    for (int i = 0; i < wordCount; i++)
    {
        cout << words[i] << endl;
    }

    // Calling second function
    cout << endl;
    findLongestWord(words, wordCount);

    return 0;
}