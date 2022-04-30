import os
import sys
import glob


def main():
    io = IO(sys.argv[1])

    file_name = sys.argv[1].rsplit('/', 1)[-1].rsplit('.', 1)[0]
    translator = VMTranslator(file_name)

    file_contents = io.import_file()
    asm_code = translator.translate_vm_code(file_contents)

    n = 0
    for x in asm_code:
        if x[:2] != '//' and x[0] != '(':
            print(n, x)
            n += 1
        else:
            print(x)

    io.write_file(asm_code)


class VMTranslator:
    def __init__(self, file_name):
        self.file_name = file_name

        self.label_counter = 0
        self.call_counter = {}

        self._push = [
            "@R13",
            "A=M",
            "D=M",
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1"
        ]

        self._pop = [
            "@SP",
            "AM=M-1",
            "D=M",
            "@R13",
            "A=M",
            "M=D"
        ]

        add = [
            "@SP",
            "M=M-1",
            "A=M",
            "D=M",
            "A=A-1",
            "M=D+M"
        ]
        neg = [
            "@SP",
            "M=M-1",
            "A=M",
            "M=-M",
            "@SP",
            "M=M+1"
        ]

        self.arithmetic_logic = lambda: {
            'add': add,
            'sub': [
                *neg,
                *add
            ],
            'neg': neg,
            'eq': [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "A=A-1",
                "D=D-M",
                f"@IF_{self.label_counter}",
                "D;JEQ",
                f"@ELSE_{self.label_counter}",
                "0;JMP",
                f"(IF_{self.label_counter})",
                "@SP",
                "A=M-1",
                "M=-1",
                f"@END_IF_{self.label_counter}",
                "0;JMP",
                f"(ELSE_{self.label_counter})",
                "@SP",
                "A=M-1",
                "M=0",
                f"(END_IF_{self.label_counter})",
            ],
            'gt': [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "A=A-1",
                "D=D-M",
                f"@IF_{self.label_counter}",
                "D;JLT",
                f"@ELSE_{self.label_counter}",
                "0;JMP",
                f"(IF_{self.label_counter})",
                "@SP",
                "A=M-1",
                "M=-1",
                f"@END_IF_{self.label_counter}",
                "0;JMP",
                f"(ELSE_{self.label_counter})",
                "@SP",
                "A=M-1",
                "M=0",
                f"(END_IF_{self.label_counter})",
            ],
            'lt': [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "A=A-1",
                "D=D-M",
                f"@IF_{self.label_counter}",
                "D;JGT",
                f"@ELSE_{self.label_counter}",
                "0;JMP",
                f"(IF_{self.label_counter})",
                "@SP",
                "A=M-1",
                "M=-1",
                f"@END_IF_{self.label_counter}",
                "0;JMP",
                f"(ELSE_{self.label_counter})",
                "@SP",
                "A=M-1",
                "M=0",
                f"(END_IF_{self.label_counter})",
            ],
            'and': [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "A=A-1",
                "M=D&M"
            ],
            'or': [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "A=A-1",
                "M=D|M"
            ],
            'not': [
                "@SP",
                "M=M-1",
                "A=M",
                "M=!M",
                "@SP",
                "M=M+1"
            ]
        }

        self.get_from_memory_segment = {
            'constant': self._constant,
            'static': self._retrieve_static,
            'local': self._retrieve_from_segment('LCL'),
            'argument': self._retrieve_from_segment('ARG'),
            'this': self._retrieve_from_segment('THIS'),
            'that': self._retrieve_from_segment('THAT'),
            'temp': self._retrieve_temp_variable,
            'pointer': self._retrieve_pointer
        }

        self.branching = {
            'label': lambda label_name: [
                f"({label_name})"
            ],

            'goto': lambda label_name: [
                f"@{label_name}",
                "0;JMP"
            ],

            'if-goto': lambda label_name: [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                f"@{label_name}",
                "D;JNE"
            ],

        }

        self.function_commands = {
            'return': self._return_function,
            'function': self._define_function,
            'call': self._call_function
        }

    def translate_vm_code(self, code_lines):
        asm_code = [
            "@256",
            "D=A",
            "@SP",
            "M=D",
        ]
        asm_code.extend(self._call_function('Sys.init', 0))

        for line in code_lines:
            asm_code.append(f"// {line}")

            command = line.split()
            if len(command) == 1 and command[0] in self.arithmetic_logic():
                self.label_counter += 1
                asm_code.extend(
                    self.arithmetic_logic()[command[0]]
                )
            elif len(command) == 3 and \
                    command[1] in self.get_from_memory_segment:

                asm_code.extend(
                    self.get_from_memory_segment[command[1]](command[2])
                )

                if command[0] == 'pop':
                    asm_code.extend(
                        self._pop
                    )

                if command[0] == 'push':
                    asm_code.extend(
                        self._push
                    )
            elif command[0] in self.branching or len(command) == 2:
                asm_code.extend(
                    self.branching[command[0]](command[1])
                )

            elif command[0] == 'return':
                asm_code.extend(self._return_function())

            elif command[0] in self.function_commands:
                asm_code.extend(
                    self.function_commands[command[0]](command[1],
                                                       command[2])
                )

        return asm_code

    def _call_function(self, function_name, args_n):
        if function_name not in self.call_counter:
            self.call_counter[function_name] = 0
        else:
            self.call_counter[function_name] += 1

        return [
            f"@{function_name}.{self.call_counter[function_name]}",
            "D=A",
            "@SP",
            "A=M",
            "M=D",
            "@LCL", "D=M", "@SP", "AM=M+1", "M=D",
            "@ARG", "D=M", "@SP", "AM=M+1", "M=D",
            "@THIS", "D=M", "@SP", "AM=M+1", "M=D",
            "@THAT", "D=M", "@SP", "AM=M+1", "M=D",
            "@SP",
            "MD=M+1",
            "@LCL",
            "M=D",
            "@5", "D=D-A",
            f"@{args_n}", "D=D-A",
            "@ARG",
            "M=D",
            f"@{function_name}",
            "0;JMP",
            f"({function_name}.{self.call_counter[function_name]})"
        ]

    def _define_function(self, function_name, local_var_n):
        return [
            f"({function_name})",
            f"@{local_var_n}",
            "D=A",
            f"({function_name}_INIT_LOCAL_VARS_LOOP)",
            "@SP",
            "A=M",
            "M=0",
            "D=D-1",
            "@SP",
            "M=M+1",
            f"@{function_name}_INIT_LOCAL_VARS_LOOP",
            "D;JGT",
        ]

    def _return_function(self):
        return [
            "@SP",
            "A=M-1",
            "D=M",
            "@ARG",
            "A=M",
            "M=D",
            "D=A",
            "@SP",
            "M=D+1",
            "@LCL", "AM=M-1", "D=M", "@THAT", "M=D",    # restore THAT
            "@LCL", "AM=M-1", "D=M", "@THIS", "M=D",    # restore THIS
            "@LCL", "AM=M-1", "D=M", "@ARG", "M=D",     # restore ARG
            "@LCL", "A=M-1", "A=A-1", "D=M", "@SP", "A=M", "M=D",   # store return adress
            "@LCL", "A=M-1", "D=M", "@LCL", "M=D",      # restore LCL
            "@SP",
            "A=M",
            "A=M",
            "0;JMP"
        ]

    def _retrieve_static(self, index):
        return [
            f"@{self.file_name}.{index}",
            "D=A",
            "@R13",
            "M=D"
        ]

    def _retrieve_temp_variable(self, index):
        temp_index = 5 + int(index)
        return [
            f"@{temp_index}",
            "D=A",
            "@R13",
            "M=D"
        ]

    def _retrieve_from_segment(self, segment):

        def retrieve(index):
            return [
                f"@{segment}",
                "D=M",
                f"@{index}",
                "D=D+A",
                "@R13",
                "M=D"
            ]

        return retrieve

    def _retrieve_pointer(self, index):
        address = None
        if index == "0":
            address = "THIS"
        elif index == "1":
            address = "THAT"

        return [
            f"@{address}",
            "D=A",
            "@R13",
            "M=D"
        ]

    def _pop_memory_segment(self, segment, index):
        return [
            f"@{segment}",
            "D=M",
            f"@{index}",
            "D=D+A",
            "@R13",
            "A=M",
            "M=D",
        ]

    @staticmethod
    def _constant(ind):
        asm_code = [
            f"@{ind}",
            "D=A",
            "@R14",
            "M=D",
            "D=A",
            "@R13",
            "M=D"
        ]
        return asm_code


class IO:
    def __init__(self, file_name):
        self.file_name = file_name
        self.source_file_extension = 'vm'
        self.target_file_extension = 'asm'

    def import_file(self):
        file_contents = None

        if os.path.isdir(self.file_name):
            file_contents = self.read_repo()
        elif os.path.isfile(self.file_name):
            file_contents = self.read_file(self.file_name)

        return self.parse_file(file_contents)

    def read_file(self, file_name):
        with open(file_name, 'r') as f:
            file_contents = list(f.readlines())

        return file_contents

    def read_repo(self):
        file_contents = []

        for file in glob.glob(
                f"{self.file_name}/*.{self.source_file_extension}"):
            print(file)
            file_contents.extend(self.read_file(file))

        return file_contents

    @staticmethod
    def parse_file(file_contents):
        file_contents_cleaned = []
        for index, line in enumerate(file_contents):
            line = line.strip()
            line = line.rsplit('//')[0]
            if line != '':
                file_contents_cleaned.append(line)
        return file_contents_cleaned

    def write_file(self, file_contents):
        if os.path.isdir(self.file_name):
            self.file_name = self.file_name + '/' \
                if self.file_name[-1] != '/' \
                else self.file_name

        target_file_dir = self.file_name.rsplit('/', 1)[0]
        target_file_name = \
            self.file_name.strip('/').rsplit('/', 2)[-1].rsplit('.', 1)[0] \
            + '.' \
            + self.target_file_extension

        target_file_path = target_file_dir + '/' + target_file_name

        with open(target_file_path, 'w') as f:
            for item in file_contents:
                f.write("%s\n" % item)
        print(target_file_path)


if __name__ == '__main__':
    main()
