choice=int(input("Enter number 1 to add,Enter number 2 to substract, enter number 3 to multiply and 4 to divide "))
num1=int(input("Enter number 1: "))
num2=int(input("Enter number 2: "))
if choice==1:
    print("sum: ",num1+num2)
elif choice==2:
    print("Subtract: ",num1-num2)
elif choice==3:
    print("multiply: ",num1*num2)
elif choice==4:
    print("divide: ",num1/num2)
else:
    print("Invalid number")
 