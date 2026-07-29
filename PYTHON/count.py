text=(input(" Enter text: "))
v=c=d=s=0
for ch in text:
    if ch.lower() in " aeiou ":
        v+=1
    elif ch.isalpha():
        c+=1
    elif ch.digit():
        d+=1
    elif ch.isspace():
        s+=1

print(v , c , d , s )