from difflib import SequenceMatcher

a= SequenceMatcher(None, "", "").ratio()*.10
print(round(a,2))


a=""
b=""

if not a and not b:
    print("both empty")