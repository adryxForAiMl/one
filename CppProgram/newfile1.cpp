#include<iostream>
#include<string>
using namespace std;

string words[100];


int split(){
    string currentword="";
    int wordcount=0;
    char ch;
    string sentence;
    for(int i=0; i<sentence.length();i++){
        ch = sentence[i];
        if(ch!= ' '){
            currentword = currentword + ch;
        }
        else{
            if(currentword.length()>0){
                words[wordcount]=currentword;
                wordcount++;
                currentword="";
            }
        }
    }
    if(currentword.length()>0){
        words[wordcount]=currentword;
        wordcount++;
    }
    return wordcount;

};

int main(){
    string sentence = "My name is";

    int wordcount = split(sentence);

    for (int i = 0; i < wordcount; i++) {
        cout << words[i] << endl;
    }

    return 0;

}