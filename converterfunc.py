from pydantic import BaseModel
from sly import Parser, Lexer
import io
import os
import pandas as pd
import re
import spacy
from nltk.tokenize import RegexpTokenizer
from rich import pretty
import subprocess
from subprocess import Popen, PIPE, STDOUT

pretty.install()

try:
    nlp = spacy.load('en_core_web_lg')
except:
    # the model isn't downloaded, so downloading it
    print("Downloading and Loading the Spacy Model")
    subprocess.call(['python', '-m', "spacy", "download", "en_core_web_lg"])
    nlp = spacy.load('en_core_web_lg')
    pass

reserved_vars = set()

keylist = [
    "begin", "end", "assign", "to", "print", "read", "if", "then", "else",
    "endif", "while", "endwhile", "do", "for", "from", "repeat", "return", "endfor",
    "start_procedure", "end_procedure"
]
keywords = {
    "begin", "end", "assign", "to", "print", "read", "if", "then", "else", "endif",
    "while", "endwhile", "do", "for", "from", "repeat", "return", "endfor",
    "start_procedure", "end_procedure"
}


class customParser(Parser):
    # debugfile = 'parser.out'
    tokens = {BEG, END, DATATYPE, ASSIGN, TO, PRINT, SCAN, READ, COMMA, OPEN, CLOSE,
              IF, THEN, ELSE, ENDIF, WHILE, ENDWHILE, ENDDOWHILE, DO, FOR, FROM, REPEAT,
              RETURN, ENDFOR, QUOTE, BOOL, RELOP, LOGOP, AS, MD, Q, START_PROCEDURE,
              END_FUNCTION, VAR, NAME_PROCEDURE, NUM, STRING}
    funcdec = ""

    def find_type(self, datatype):
        if (datatype == 'int'):
            return "%d"
        elif (datatype == 'char'):
            return "%c"
        elif (datatype == 'float'):
            return "%f"
        else:
            return "%ld"

    def update_VAR(self, var):
        # check if belongs to set
        if var in self.variables:  # variable with same name already exists
            print("Same variable used twice. Change variable name of {}".format(var))
        else:
            self.variables.add(var)
        return True

    def check_VAR(self, var):
        # checks if varible exists
        if var in self.variables:
            return True
        else:
            print("The variable {} is not defined.".format(var))

    def __init__(self):
        self.names = {}
        self.variables = set()

    # START :  BEG {printf("\n#include<stdio.h>\nvoid main()\n{\n");} CODE END { printf("\n}\nValid"); exit(0); }
    #       ;
    @_('BEG CODE END')
    def START(self, p):
        return "#include<stdio.h>\n" + self.funcdec + "void main()\n{\n" + p.CODE + "}"

    # CODE : STMT  {printf(";");}
    #      | CODE STMT {printf(";");}
    #      | ST
    #      | CODE ST
    #      ;
    @_('STMT')
    def CODE(self, p):
        return p.STMT + ";\n"

    @_('CODE STMT')
    def CODE(self, p):
        return p.CODE + p.STMT + ";\n"

    @_('ST')
    def CODE(self, p):
        return p[0]

    @_('CODE ST')
    def CODE(self, p):
        return p[0] + p[1]

    # STMT : EXPR
    #      | DEC
    #      | INIT
    #      ;
    @_('EXPR', 'DEC', 'INIT', 'PR', 'SC')
    def STMT(self, p):
        return p[0]

    # ST   : IF {printf("if(");} CON THEN{printf(")\n{");} CODE ENDIF {printf("\n}");}
    #      | IF { printf("if(");} CON THEN{printf(")\n{");} STMT ELSE { printf("}\nelse\n{");} STMT ENDIF {printf("\n}");}
    #      | WHILE{printf("while(");} EXPR THEN{printf(")\n{\n");} CODE ENDWHILE {printf("\n}");}
    #      | DO{printf("do\n{");} CODE WHILE{printf("\n}while(");} EXPR ENDDOWHILE {printf(");");}
    #      | START_PROCEDURE NAME_PROCEDURE OPEN{printf("void %s(",$2); } parameter_list CLOSE{printf(")\n{\n");} CODE END_FUNCTION {printf("}");}
    #      | FOR{printf("for(");} INIT REPEAT{printf("\n{\n");} CODE ENDFOR{printf("\n}\n");}
    #      | PR
    #      | SC
    #      ;
    @_('IF CON THEN CODE ENDIF')
    def ST(self, p):
        return "if(" + p.CON + ")\n{" + p.CODE + "}"

    @_('IF CON THEN CODE ELSE CODE ENDIF')
    def ST(self, p):
        return "if(" + p.CON + ")\n{" + p.CODE0 + "}\nelse\n{" + p.CODE1 + "}"

    @_('WHILE EXPR THEN CODE ENDWHILE')
    def ST(self, p):
        return("while(" + p.EXPR + ")\n{\n" + p.CODE + "\n}")

    @_('DO CODE WHILE EXPR ENDDOWHILE')
    def ST(self, p):
        return("do\n{" + p.CODE + "\n}while(" + p.EXPR + ")")

    @_('START_PROCEDURE NAME_PROCEDURE parameter_list CLOSE CODE END_FUNCTION')
    def ST(self, p):
        self.funcdec += "void {}".format(p.NAME_PROCEDURE) + \
            p.parameter_list + ")\n{\n" + p.CODE + "}\n"
        return ""

    @_('FOR INIT REPEAT CODE ENDFOR')
    def ST(self, p):
        return("for(" + p.INIT + "\n{\n" + p.CODE + "\n}")

    @_('PR', 'SC')
    def ST(self, p):
        return (p[0])

    # parameter_list: VAR DATATYPE{printf("%s %s",$2,$1);}
    #               | parameter_list COMMA VAR DATATYPE{printf(",%s %s",$4,$3);}
    @_('VAR DATATYPE')
    def parameter_list(self, p):
        return ("{} {}".format(p.DATATYPE, p.VAR))

    @_('parameter_list COMMA VAR DATATYPE')
    def parameter_list(self, p):
        return ("{} {}".format(p.DATATYPE, p.VAR))

    # EXPR : E RELOP{printf("%s",$2); } E
    #      | E LOGOP{printf("%s",$2); } E
    #      | E
    #      ;
    @_('E RELOP E')
    def EXPR(self, p):
        return (p[0] + p.RELOP + p[2])

    @_('E LOGOP E')
    def EXPR(self, p):
        return (p[0] + p.LOGOP + p[2])

    @_('E')
    def EXPR(self, p):
        return (p.E)

    # E : E AS{printf("%s",$2);} T
    #   | T
    #   ;

    @_('E AS T')
    def E(self, p):
        return(p.E + p.AS + p.T)

    @_('T')
    def E(self, p):
        return p.T

    # T : T MD{printf("%s",$2);} F
    #   | F
    #   ;
    @_('T MD F')
    def T(self, p):
        return (p.T + p.MD + p.F)

    @_('F')
    def T(self, p):
        return p.F

    # F : VAR {printf("%s",$1);}
    #   | NUM {printf("%s",$1);}
    #   | OPEN E CLOSE
    #   ;
    @_('VAR')
    def F(self, p):
        return ("{}".format(p.VAR))

    @_('NUM')
    def F(self, p):
        # print(p.NUM)
        return ("{}".format(p.NUM))

    @_('OPEN E CLOSE')
    def F(self, p):
        return (p.OPEN + p.E + p.CLOSE)

    # N : VAR{printf("%s",$1);} N
    #   |
    #   ;
    # @_('VAR N')
    # def N(self,p):
    #     return ("{}".format(p.VAR),p.N)

    # DEC : ASSIGN OPEN VAR DATATYPE CLOSE { update($3); printf("%s %s",$4,$3); };update_VAR
    @_('ASSIGN OPEN VAR DATATYPE CLOSE')
    def DEC(self, p):
        self.update_VAR(p.VAR)
        # print("assigning " + p.DATATYPE + " " + p.VAR)
        return p.DATATYPE + " " + p.VAR

    # TODO DO VERIFICATION
    # INIT : ASSIGN VAR TO NUM {g=check($2); if(g==1)printf("%s = %s",$2,$4); else exit(0);}
    #      | ASSIGN VAR TO VAR { printf("%s = %s",$2,$4); }
    #      | VAR FROM NUM TO NUM {if($3<$5){printf("%s = %s ; %s <= %s ; %s ++)",$1,$3,$1,$5,$1);}else{printf("%s = %s ; %s >= %s ; %s --)",$1,$3,$1,$5,$1);}}
    #      | VAR Q{printf("%s %s",$1,$2);} E , VAR = E
    #      ; check_VAR
    @_('ASSIGN VAR TO NUM')
    def INIT(self, p):
        # print("ASSIGN VAR TO NUM")
        self.check_VAR(p.VAR)
        return p.VAR + "=" + p.NUM

    @_('ASSIGN VAR TO VAR')
    def INIT(self, p):
        if ((p[1] in self.variables) and (p[3] in self.variables)):
            return "{} = {}".format(p[1], p[3])
        else:
            Exception("Both variables should exist before equating.")

    @_('VAR FROM EXPR TO EXPR')
    def INIT(self, p):
        if (p[2] < p[4]):
            return "{} = {} ; {} <= {} ; {}++)".format(p[0], p[2], p[0], p[4], p[0])
        else:
            return "{} = {} ; {} >= {} ; {}--)".format(p[0], p[2], p[0], p[4], p[0])

    @_('')
    def EXPR(self, p):
        if EXPR == NUM:
            return p.NUM
        else:
            return p.VAR

    @_('VAR Q E')
    def INIT(self, p):
        return ("{} = ".format(p.VAR) + p.E)

    # PR : PRINT DATATYPE COMMA VAR {g=check($4); getspec($2); if(g==1)printf("printf(\"%s\",%s);\n",str,$4); else exit(0); }
    #    | PRINT{printf("printf(\"");} QUOTE N DATA N QUOTE{printf("\"%s);",name); strcpy(name,"");}
    #    | PRINT{printf("printf(\"");} QUOTE N QUOTE{printf("\");");}
    #    ;
    # print (a int)
    @_('PRINT OPEN VAR DATATYPE CLOSE')
    def PR(self, p):
        return "printf(\"{}\",{})".format(self.find_type(p.DATATYPE), p.VAR)

    @_('PRINT STRING')
    def PR(self, p):
        return "printf({})".format(p.STRING)

    # SC : READ DATATYPE COMMA VAR {g=check($4); getspec($2); if(g==1)printf("scanf(\"%s\",&%s);\n",str,$4); else exit(0); }
    #    ;
    @_('READ OPEN VAR DATATYPE CLOSE')
    def SC(self, p):
        return 'scanf(\"{}\",&{})'.format(self.find_type(p.DATATYPE), p.VAR)

    # CON : VAR RELOP VAR { printf("%s %s %s",$1,$2,$3); }
    #     | VAR RELOP NUM { printf("%s %s %s",$1,$2,$3); }
    #     | VAR LOGOP VAR { printf("%s %s %s",$1,$2,$3); }
    #     | BOOL { printf("%s",$1); }
    #     ;
    @_('VAR RELOP VAR', 'VAR RELOP NUM', 'VAR LOGOP VAR')
    def CON(self, p):
        return "{} {} {}".format(p[0], p[1], p[2])

    @_('BOOL')
    def CON(self, p):
        return "{}".p[0]


class Input(BaseModel):
    message: str


class Output(BaseModel):
    c_code: str


comment_eraser = re.compile(r"[\/\/].*")
string_eraser = re.compile(r"([\"'])((\\{2})*|(.*?[^\\](\\{2})*))\1")
capture_func = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)[(]")
capture_vars = re.compile(r"\(?\s*(([\d\w]+)\s(int|float|char|double)\s*)\)?")


def cleaner(strs):
    # print("Initial:",strs)
    strs = comment_eraser.sub("", strs)
    strs = string_eraser.sub("", strs)
    for match in capture_vars.finditer(strs):
        # extract words
        reserved_vars.add(match.group(2))
        # print(match.group(2)) #2 = var names, 3 = datatype, 1=whole declaration
    for match in capture_func.finditer(strs):
        reserved_vars.add(match.group(1))
        # print(match.group(1))
    strs = capture_func.sub("", strs)
    strs = capture_vars.sub("", strs)
    return strs


def spacysim(word1, word2):
    token1 = nlp(word1)
    token2 = nlp(word2)
    return token1.similarity(token2)


def keywordreturner(text):
    keyw = {}
    for key in keylist:
        keyw[key] = set()
        keyw[key].add(key)

    df = pd.read_csv(io.StringIO(text), header=None, delimiter="\n")
    df = df.rename(columns={0: "Code"})
    df["Cleaned"] = df["Code"].apply(cleaner)
    tokenizer = RegexpTokenizer(r'[a-zA-Z_][a-zA-Z0-9_]*')
    for index, row in df.iterrows():
        sentence = df.loc[index, 'Cleaned']
        # print(sentence)
        sentence = tokenizer.tokenize(sentence)
        for word in sentence:
            if word in keywords or word in reserved_vars:
                continue
            max_sim = 0
            max_key = None
            for k in keywords:
                sim = spacysim(k, word)
                if sim > max_sim:
                    max_sim = sim
                    max_key = k
            print("word : {} , closest match : {} | Sim : {}".format(
                word, max_key, max_sim))
            if max_sim > 0:
                if max_key in keyw:
                    keyw[max_key].add(word)
                else:
                    keyw[max_key] = set()
                    keyw[max_key].add(word)
    return keyw


def C_Code_Generator(input: Input) -> Output:
    """Constructs the C code from the input data."""

    global reserved_vars
    reserved_vars = set()

    customkeys = keywordreturner(input.message)
    keyw = customkeys

    print(customkeys)

    class customLexer(Lexer):
        tokens = {BEG, END, DATATYPE, ASSIGN, TO, PRINT, SCAN, READ, COMMA, OPEN, CLOSE,
                  IF, THEN, ELSE, ENDIF, WHILE, ENDWHILE, ENDDOWHILE, DO, FOR, FROM, REPEAT,
                  RETURN, ENDFOR, QUOTE, BOOL, RELOP, LOGOP, AS, MD, Q, START_PROCEDURE,
                  END_FUNCTION, VAR, NAME_PROCEDURE, NUM, STRING}
        ignore = ' '
        # Other ignored patterns

        ignore_comment = r'[\/\/].*'
        ignore_newline = r'\n+'
        BEG = r'\b' + r'|'.join(keyw['begin']) + r'\b'
        END = r'\b' + r'|'.join(keyw["end"]) + r'\b'
        DATATYPE = r'int|float|char|double'
        ASSIGN = r'|'.join(keyw["assign"])
        TO = r'|'.join(keyw["to"])
        PRINT = r'|'.join(keyw["print"])
        SCAN = r"scan"
        READ = r'|'.join(keyw["read"])
        COMMA = r","
        OPEN = r"\("
        CLOSE = r"\)"
        IF = r'|'.join(keyw["if"])
        THEN = r'|'.join(keyw["then"])
        ELSE = r'|'.join(keyw["else"])
        ENDIF = r'|'.join(keyw["endif"])
        WHILE = r'|'.join(keyw["while"])
        ENDWHILE = r'|'.join(keyw["endwhile"])
        ENDDOWHILE = r"enddowhile"
        DO = r'|'.join(keyw["do"])
        FOR = r'|'.join(keyw["for"])
        FROM = r'|'.join(keyw["from"])
        REPEAT = r'|'.join(keyw["repeat"])
        RETURN = r'|'.join(keyw["return"])
        ENDFOR = r'|'.join(keyw["endfor"])
        STRING = r'\".*?\"'
        QUOTE = r"\""
        BOOL = r'true|false'
        RELOP = r"<=|>=|==|<|>"
        LOGOP = r"&&|\|\|"
        AS = r"\+|\-"
        MD = r"\*|\\|%"
        Q = r"="
        START_PROCEDURE = r'|'.join(keyw["start_procedure"])
        END_FUNCTION = r'|'.join(keyw["end_procedure"])
        NAME_PROCEDURE = r'[a-zA-Z_][a-zA-Z0-9_]*[(]'
        VAR = r'[a-zA-Z_][a-zA-Z0-9_]*'
        NUM = r'[0-9]+'

        @_(r'\n+')
        def ignore_newline(self, t):
            self.lineno += len(t.value)

    lexer = customLexer()
    parser = customParser()

    outs = parser.parse(lexer.tokenize(input.message))

    astyle_caller = "astyle"
    if os.name == 'nt':
        print("Host OS is Windows")
        astyle_caller = "astyle"

    p = Popen([astyle_caller, "--style=allman"],
              stdout=PIPE, stdin=PIPE, stderr=PIPE)
    stdout_data = p.communicate(input=outs.encode())[0]

    return Output(c_code=stdout_data)
