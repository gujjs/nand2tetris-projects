// function SimpleFunction.test 2
(SimpleFunction.test)
// push local 0
@LCL
D=M
@0
D=D+A
@R13
M=D
@R13
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// push local 1
@LCL
D=M
@1
D=D+A
@R13
M=D
@R13
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
M=M-1
A=M
D=M
A=A-1
M=D+M
// not
@SP
M=M-1
A=M
M=!M
@SP
M=M+1
// push argument 0
@ARG
D=M
@0
D=D+A
@R13
M=D
@R13
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// add
@SP
M=M-1
A=M
D=M
A=A-1
M=D+M
// push argument 1
@ARG
D=M
@1
D=D+A
@R13
M=D
@R13
A=M
D=M
@SP
A=M
M=D
@SP
M=M+1
// sub
@SP
M=M-1
A=M
M=-M
@SP
M=M+1
@SP
M=M-1
A=M
D=M
A=A-1
M=D+M
// return
@SP
A=M-1
D=M
@ARG
A=M
M=D
D=A
@SP
M=D+1
@LCL
AM=M-1
D=M
@THAT
M=D
@LCL
AM=M-1
D=M
@THIS
M=D
@LCL
AM=M-1
D=M
@ARG
M=D
@LCL
A=M-1
D=M
@LCL
M=D
