#include <stdio.h>
#include <string.h>

int main()
{
    char correctPIN[] = "@5ab7&";
    char enteredPIN[20];
    int i;

    for(i = 1; i <= 3; i++)
    {
        printf("Enter PIN (Attempt %d): ", i);
        scanf("%19s", enteredPIN);

        if(strcmp(correctPIN, enteredPIN) == 0)
        {
            printf("Access Granted\n");
            return 0;
        }
        else
        {
            printf("Wrong PIN\n");
        }
    }

    printf("Card Blocked\n");

    return 0;
}