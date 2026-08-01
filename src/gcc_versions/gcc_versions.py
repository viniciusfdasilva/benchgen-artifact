import sys, os, json, csv
from scipy import stats

GCC_VERSION = 14

RUN    = 20
WARMUP = 3

GRAMMAR_ID = 'ex8'

# Environment variables
CC   = f'/usr/local/gcc{GCC_VERSION}/bin/gcc'

# Program variables
grammar_ids = [f'{GRAMMAR_ID}']

# Datas structures avaliable on BenchGen
data_structures = ['sortedlist'] #'sortedlist']

# Compiler optimization level
opts = ['-O0',
        '-O1',
        '-O2',
        '-O3', 
        '-Os',
        '-Og',]
        #'-Ofast']

# Program will be generate from 'BEGIN_ITERATION_RANGE' to 'FINAL_ITERATION_RANGE'
BEGIN_ITERATION_RANGE = 8
FINAL_ITERATION_RANGE = 8

csv_data = [['gcc_compilation_time','gcc_program_time','bin_size','opt', 'iteration', 'grammar_name', 'data_structure']]

grammar_iterations = range(BEGIN_ITERATION_RANGE, FINAL_ITERATION_RANGE+1)

def generate_csv():
    print(csv_data)
    with open(f'/tmp/data_{GCC_VERSION}_{RUN}_{GRAMMAR_ID}.csv', 'w', newline='', encoding='utf-8') as file_csv:
        writer = csv.writer(file_csv)
        writer.writerows(csv_data)

def generatePrograms(benchGen_path):
    
    program_names = []

    try:
        os.chdir(f'{benchGen_path}/src/gen/')

        try_find_exec_stats = os.system('find benchGen')

        if try_find_exec_stats != 0:

            print('Compiling BenchGen...')
            os.system('make 2>/dev/null')
        
        for grammar_id in grammar_ids:

            production_rule = f'./examples/{grammar_id}/production_rule.txt'
            seed_string     = f'./examples/{grammar_id}/seed_string.txt'

            for iteration in grammar_iterations:
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

def read_compilation_time(file):

    with open(file=file, mode='r', encoding='utf-8') as file:
        data = json.load(file)
    return float(data['results'][0]['mean'])

def read_time(file):
    f = open(file=file, mode='r', encoding='utf-8')
    return float(str(f.read()).strip())

def get_compilation_time(benchGen_root_path, opt):
    dalloc_path = f'{benchGen_root_path}/src/Dalloc/src/'
    os.system(f'hyperfine --warmup {WARMUP} --runs {RUN} --show-output --ignore-failure "{CC} {opt} *.c *.h -I{dalloc_path} -o main" --export-json /tmp/compilation_{GCC_VERSION}_{RUN}_{GRAMMAR_ID}.json')
    return read_compilation_time(f"/tmp/compilation_{GCC_VERSION}_{RUN}_{GRAMMAR_ID}.json")

def get_run_time(opt):
    dalloc_path = f'{benchGen_root_path}/src/Dalloc/src/'
    os.system(f'hyperfine --warmup {WARMUP} --runs {RUN} --show-output --ignore-failure "./main" --export-json /tmp/runtime_{GCC_VERSION}_{RUN}_{GRAMMAR_ID}.json')
    return read_compilation_time(f'/tmp/runtime_{GCC_VERSION}_{RUN}_{GRAMMAR_ID}.json')

def get_binary_size(opt):
    os.system("size ./main | awk 'NR==2 {print $1}' > /tmp/size_"+str(GCC_VERSION)+"_"+str(RUN)+"_"+GRAMMAR_ID+".txt")
    return read_time(f'/tmp/size_{GCC_VERSION}_{RUN}_{GRAMMAR_ID}.txt')

def get_info(file):
    print(file)
    f = open(file=file, mode='r', encoding='utf-8')
    return str(f.read()).strip()

def clear(benchGen_root_path, program_names):

    os.chdir(f'{benchGen_root_path}/src/gen')

    for program_name in program_names:
        os.system(f'rm -r {program_name}')
        
if __name__ == '__main__':
    
    if os.name == 'win32':
        raise Exception('This script is not compatible with Windows system!')

    args = sys.argv

    if len(args) > 2:

        GCC_VERSION = args[2]
        CC   = f'/usr/local/gcc{GCC_VERSION}/bin/gcc'
        
        print(f'RUNNING PROGRAM {GRAMMAR_ID} RUN {RUN}')
        benchGen_root_path = args[1]

        print('Generating programs...')
        program_names = generatePrograms(benchGen_root_path)

        print('Compiling programs')
        for program_name in program_names:
            
            for opt in opts:
                program_src_path = f'{benchGen_root_path}/src/gen/{program_name}/src/'

                os.chdir(program_src_path)
                                
                clang_time = get_compilation_time(benchGen_root_path, opt)
                run_time   = get_run_time(opt)
                bin_size   = get_binary_size(opt)
                   
                iteration      = get_info(f'{program_src_path}iteration.txt')
                grammar        = get_info(f'{program_src_path}grammar.txt')
                data_structure = get_info(f'{program_src_path}data_structure.txt')

                csv_data.append([clang_time, run_time,bin_size, opt, iteration, grammar, data_structure])
        
        generate_csv()
        clear(benchGen_root_path, program_names)
    else:
        raise Exception("Argument 'BenchGen path' is missing")
