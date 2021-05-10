# NLP-based Automatic Translation Application: Pseudocode to C

This is a Compiler Design project that uses pseudocode and augments it with Natural Language Processing to allow users to use more keywords based on their preference. 
It is built using pure python implementation of Lex and Yacc by using SLY.

```py
start
assign ( num int )
assign ( c int )
allot ( i int )
define ( flag int )
assign flag to 0
display "Enter the value to be checked "
read (num int)
for i from 2 to num
repetition
c = num%i
if c==0
then
assign flag to 1
endif
endfor
if flag==1
then
print "The value "
print (num int)
print " is not prime"
else
print "The value "
print (num int)
print " is prime"
endif
end
```

It produces the C code as the following

```c
#include<stdio.h>

void main()
{
    int num;
    int c;
    int i;
    int flag;
    flag=0;
    printf("Enter the value to be checked ");
    scanf("%d",&num);
    for(i = 2 ; i <= num ; i++)
    {
        c = num%i;
        if(c == 0)
        {
            flag=1;
        }
    }
    if(flag == 1)
    {
        printf("The value ");
        printf("%d",num);
        printf(" is not prime");
    }
    else
    {
        printf("The value ");
        printf("%d",num);
        printf(" is prime");
    }
}
```

## NLP Techniques Used 

Pseudocode can vary between users, and to incorporate Natural Language and make translation easier, we make use of Similarity metrics. We use the Spacy module to check Similarity.
Our model uses a very limited set of keywords to demonstrate the basic functionality.
A user is free to use other words that correspond to a similar meaning to a word present in the dictionary, and it is then automatically mapped to perform the same functionality as illustrated below:

![Similarity with existing keywords](./doc/sim.png)

For example, user may use the word "whenever" instead of "if" and "during" instead of "while", etc.
This increases the usability as it is able to use NLP techniques to extract the meaning behind the word.

# Installation

Simply execute the following after cloning the git repository to a suitable directory.

```sh
pip install -r requirements.txt
```

The script tries to download the `en_web_core_lg` model for spacy, this model uses ~800MB of memory, so please make sure that you have enough beforehand.

Now you can finally use opyrator environment to test out the converter.

# Running the project

After all the install steps, you should launch the UI using

```sh
opyrator launch-ui converterfunc:C_Code_Generator
```

Doing so would prompt you to launch a beautiful UI allowing you to interactively test the converter.
![ui](./doc/ui.png)

You can provide it some input in the message box.
![message](./doc/input.png)

Then you execute it, be wary that the execution times will depend on the length of the code and the performace of the host computer as it heavily relies on finding vector similarity.
![output](./doc/c_code.png)

Please note that the project uses a compiled binary from the [Astyle Project](http://astyle.sourceforge.net/), and hence it's included in the source.
