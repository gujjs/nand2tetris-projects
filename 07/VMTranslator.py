import sys


def main():
    io = IO(sys.argv[1])
    translator = VMTranslator()

    file_contents = io.import_file()
    asm_code = translator.translate_vm_code(file_contents)

    print(*asm_code, sep='\n')
    io.write_file(asm_code)


class VMTranslator:
    def __init__(self):
        self.label_counter = 0

        self._push = [
            "@SP",
            "A=M",
            "M=D",
            "@SP",
            "M=M+1"
        ]

        self.arithmetic_logic = {
            'add': [
                "@SP",
                "M=M-1",
                "A=M",
                "D=M",
                "A=A-1",
                "M=D+M"
            ],
            'sub': [

            ],
            'neg': [
                "@SP",
                "M=M-1",
                "A=M",
                "M=-M",
            ],
            'eq': [
                "@SP",
                "M=M-1";
                "A=M",
                "D=M",
                "A=A-1",
                "D=D+M",
                f"@IF_{self.label_counter}",
                "D;JEQ",
                f"@END_IF_{self.label_counter}",
                "0;JMP",
                f"(IF_{self.label_counter})",
                "M=",
                f"(END_IF_{self.label_counter})"
            ],
            'gt': [],
            'lt': [],
            'and': [],
            'or': [],
            'not':[]
        }

        self.memory_segments = {
            'constant': self._constant
        }

    def translate_vm_code(self, code_lines):
        asm_code = []
        for line in code_lines:
            asm_code.append(f"// {line}")

            command = line.split()
            if len(command) == 1:
                asm_code.extend(
                    self.arithmetic_logic[command[0]]
                )
            elif len(command) == 3:
                if command[0] == 'pop':
                    asm_code.extend(
                        []
                    )

                asm_code.extend(
                    self.memory_segments[command[1]](command[2])
                )
                if command[0] == 'push':
                    asm_code.extend(
                        self._push
                    )

        return asm_code

    @staticmethod
    def _constant(ind):
        asm_code = [
            f"@{ind}",
            f"D=A"
        ]
        return asm_code


class IO:
    def __init__(self, file_name):
        self.file_name = file_name
        self.target_file_extension = 'asm'

    def import_file(self):
        return self.parse_file(
            self.read_file()
        )

    def read_file(self):
        with open(self.file_name, 'r') as f:
            file_contents = list(f.readlines())

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
        target_file_name = self.file_name.rsplit(
            '.', 1)[0] + '.' + self.target_file_extension

        with open(target_file_name, 'w') as f:
            for item in file_contents:
                f.write("%s\n" % item)


if __name__ == '__main__':
    main()
