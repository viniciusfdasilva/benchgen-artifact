import os, sys
GCC_VERSION   = 14
CLANG_VERSION = 21

compilers = [f'gcc-{GCC_VERSION}', f'clang-{CLANG_VERSION}']

opts      = ['-O0','-O1','-O2','-O3', '-0s', '-Ofast']
programs  = ['ex8', 'ex9']
data_structures = ['array'] #', sortedlist'] Pode adicionar mais estruturas de dados na lista

iterations = [8, 10]

EXECUTION_WARMUP = 2
NUMBER_OF_EXECUTIONS = 50

def generatePrograms(benchGen_path):
    
    program_names = []

    try:
        os.chdir(f'{benchGen_path}/src/gen/')

        try_find_exec_stats = os.system('find benchGen')

        if try_find_exec_stats != 0:

            print('Compiling BenchGen...')
            os.system('make 2>/dev/null')
        
        for grammar_id in programs:

            production_rule = f'./examples/{grammar_id}/production_rule.txt'
            seed_string     = f'./examples/{grammar_id}/seed_string.txt'

            for iteration in iterations:
                for data_structure in data_structures:

                    program_name = f'{data_structure}_{iteration}_{grammar_id}'
                    program_names.append(program_name)

                    cmd = f'./benchGen {iteration} {production_rule} {seed_string} {program_name} {data_structure}'
                    print(f'Generating program: {grammar_id} iteration: {iteration} data_structure: {data_structure}')
                    os.system(f'{cmd} 2>/dev/null')

                    os.system(f"echo '{grammar_id}' > ./{program_name}/src/grammar.txt")
                    os.system(f"echo '{iteration}' > ./{program_name}/src/iteration.txt")
                    os.system(f"echo '{data_structure}' > ./{program_name}/src/data_structure.txt")

        return program_names

    except OSError:
        raise OSError("There's an error!")

def read_time(file_path):

    with open(file=file_path, mode='r', encoding='utf-8') as file:
        data = json.load(file)
    return float(data['results'][0]['mean'])

def read_size(file):
    f = open(file=file, mode='r', encoding='utf-8')
    return float(str(f.read()).strip())

def get_compilation_time(compiling_cmd, grammar_id):
    os.system(f"hyperfine -w {EXECUTION_WARMUP} -r {NUMBER_OF_EXECUTIONS} '{compiling_cmd}' --export-json /tmp/result_{NUMBER_OF_EXECUTIONS}_{grammar_id}.json")
    return read_time(f"/tmp/result_{NUMBER_OF_EXECUTIONS}_{grammar_id}.json")

def get_binary_size(grammar_id):
    os.system("size ./a.out | awk 'NR==2 {print $1}' > /tmp/size_"+str(NUMBER_OF_EXECUTIONS)+"_"+grammar_id+".txt")
    return read_opt_llc_size(f'/tmp/size_{NUMBER_OF_EXECUTIONS}_{grammar_id}.txt')

def get_execution_time(grammar_id):
    os.system(f'hyperfine -w {EXECUTION_WARMUP} -r {NUMBER_OF_EXECUTIONS} "./a.out" --export-json /tmp/result_{NUMBER_OF_EXECUTIONS}_{grammar_id}.json')
    return read_time(f"/tmp/result_{NUMBER_OF_EXECUTIONS}_{grammar_id}.json")

def usage():
    print("BenchGen 'Comparação de Compiladores' artifact")
    print("Usage: python compilers_comparison.py <OPTIONS>")
    print("OPTIONS: (-h | --help) | ('BenchGen root path')")
    
def main(benchGen_root_path, execution_warmup, number_of_executions):

    dalloc_path = f'{benchGen_root_path}/src/Dalloc/src'
    
    programs_path = generatePrograms(benchGen_root_path)

    for program_path in programs_path:

        os.chdir(f"{benchGen_root_path}/src/gen/{program_path}")
        
        grammar_name = program_path.split("_")[-1].strip()
        
        for compiler in compilers:        
            for opt in if opts if compiler == f"gcc-{GCC_VERSION}" else opts + ["-Oz"]:
                compiling_cmd = f'{compiler} {opt} -Wl,--wrap=malloc -Wl,--wrap=free -I{dalloc_path} {dalloc_path}/*.c {dalloc_path}/*.h src/*.c src/*.h'

                get_compilation_time(compiling_cmd, grammar_name)
                get_binary_size(grammar_name)
                get_execution_time(grammar_name)

if __name__ == '__main__':

    if os.name == 'win32':
        raise Exception('This script is not compatible with Windows system!')
        
    args = sys.argv
    
    try:
        option = args[1]

        if option == '-h' or option == '--help':
            usage()
        benchGen_root_path = option[:-1] if option.split()[-1:] == '/' else option
    except ValueError:
        raise ValueError(f'Argument is not a integer valid!')

    main(program_path, execution_warmup, number_of_executions)