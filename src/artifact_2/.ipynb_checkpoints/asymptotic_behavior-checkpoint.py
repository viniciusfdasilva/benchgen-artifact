import sys, os, json, csv
from scipy import stats

CLANG_VERSION = 21

RUN = 50

# Environment variables
CC   = f'clang-{CLANG_VERSION}'
OPT  = f'opt-{CLANG_VERSION}'
LLC  = f'llc-{CLANG_VERSION}'
LINK = f'llvm-link-{CLANG_VERSION}'
DIS = f'llvm-dis-{CLANG_VERSION}'

# Program variables
grammar_ids = ['ex6','ex7','ex8', 'ex9']

# Datas structures avaliable on BenchGen
data_structures = ['array', 'sortedlist']

# Compiler optimization level
opts = ['-O0',
        '-O1',
        '-O2',
        '-O3', 
        '-O3 -ffast-math' if CLANG_VERSION >= 21 else '-Ofast'] # -Ofast became deprecated in Clang 21

# Program will be generate from 'BEGIN_ITERATION_RANGE' to 'FINAL_ITERATION_RANGE'
BEGIN_ITERATION_RANGE = 4
FINAL_ITERATION_RANGE = 11

csv_data = [['clang_time','opt_time','llc_time','bin_size','opt', 'iteration', 'grammar_name', 'data_structure']]

grammar_iterations = range(BEGIN_ITERATION_RANGE, FINAL_ITERATION_RANGE+1)

def generate_csv():
    print(csv_data)
    with open(f'/tmp/compilers_comparison.csv', 'w', newline='', encoding='utf-8') as file_csv:
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

def read_compilation_time(grammar_id):

    with open(file=f'/tmp/result_{RUN}_{grammar_id}.json', mode='r', encoding='utf-8') as file:
        data = json.load(file)
    return float(data['results'][0]['mean'])

def read_opt_llc_size(file):
    f = open(file=file, mode='r', encoding='utf-8')
    return float(str(f.read()).strip())

def get_compilation_time(benchGen_root_path, opt, grammar_id):

    dalloc_path = f'{benchGen_root_path}/src/Dalloc/src/'
    
    os.system(f'hyperfine --warmup 1 --runs {RUN} --show-output "{CC} {opt} -S -emit-llvm *.c *.h -I{dalloc_path}" --export-json /tmp/result_{RUN}_{grammar_id}.json')
    return read_compilation_time()

def get_opt_time(opt, grammar_id):
    dalloc_path = f'{benchGen_root_path}/src/Dalloc/src/'
    os.system(f'{LINK} *.ll -o all.bc')
    os.system(f'{DIS} all.bc -o all.ll')
    os.system(OPT + " " + opt + " -time-passes all.ll -o optimized.ll 2>&1 | grep 'Total Execution Time' | head -n 1 | awk '{print $4}' > /tmp/opt_"+str(RUN)+"_" + grammar_id +".txt")
    return read_opt_llc_size(f'/tmp/opt_{RUN}_{grammar_id}.txt')

def get_binary_size(opt, grammar_id):
    os.system(f"{CC} {opt} optimized.ll -o a.out")
    os.system("size ./a.out | awk 'NR==2 {print $1}' > /tmp/size_"+str(RUN)+"_"+grammar_id+".txt")
    return read_opt_llc_size(f'/tmp/size_{RUN}_{grammar_id}.txt')

def get_llc_time(opt, grammar_id):
    os.system(LLC+" "+opt+" -time-passes  -o program.s optimized.ll 2>&1 | grep 'Total Execution Time' | head -n 1 | awk '{print $4}' > /tmp/llc_"+str(RUN)+"_" + grammar_id + ".txt")
    return read_opt_llc_size(f'/tmp/llc_{RUN}_{grammar_id}.txt')

def get_info(file):
    print(file)
    f = open(file=file, mode='r', encoding='utf-8')
    return str(f.read()).strip()

def clear(benchGen_root_path, program_names):

    os.chdir(f'{benchGen_root_path}/src/gen')

    for program_name in program_names:
        os.system(f'rm -r {program_name}')

def usage():
    print("BenchGen 'Comportamento Assintótico' artifact")
    print("Usage: python asymptotic_behavior.py <OPTIONS>")
    print("OPTIONS: (-h | --help) | ('BenchGen root path')")

if __name__ == '__main__':
    
    if os.name == 'win32':
        raise Exception('This script is not compatible with Windows system!')

    args = sys.argv

    if len(args) > 1:

        option = args[1]

        if option == '-h' or option == '--help':
            usage()
            
        benchGen_root_path = option[:-1] if option[-1:] == "/" else option
        
        print('Generating programs...')
        program_names = generatePrograms(benchGen_root_path)

        print('Compiling programs')
        for program_name in program_names:

            grammar_id = program_name.split("_")[-1].strip()
            
            for opt in opts:
                program_src_path = f'{benchGen_root_path}/src/gen/{program_name}/src/'

                os.chdir(program_src_path)
                llc_times   = []
                opt_times   = []
                
                for i in range(0,RUN):
                    
                    print(f'PROGRAM {program_name}, OPTIMIZATION: {opt}, EXECUTION: {i+1}/{RUN}')
                    
                    if i == 0:
                        clang_time = get_compilation_time(benchGen_root_path, opt, grammar_id)
                        opt_time   = get_opt_time(opt, grammar_id)
                        bin_size   = get_binary_size(opt, grammar_id)
                        llc_time   = get_llc_time(opt, grammar_id)
                    else:
                        _ = get_compilation_time(benchGen_root_path, opt, grammar_id)
                        opt_time   = get_opt_time(opt, grammar_id)
                        _ = get_binary_size(opt, grammar_id)
                        llc_time   = get_llc_time(opt, grammar_id)
                    
                    print(f"CLANG {clang_time}")
                    print(f"BIN {bin_size}")
                    print(f"OPT {opt_time}")
                    print(f"LLC {llc_time}")

                    os.system('rm -r *.ll *.bc *.s')
                    opt_times.append(opt_time)
                    llc_times.append(llc_time)
                
                opt_average   = sum(opt_times)/len(opt_times)
                llc_average   = sum(llc_times)/len(llc_times)

                iteration      = get_info(f'{program_src_path}iteration.txt')
                grammar        = get_info(f'{program_src_path}grammar.txt')
                data_structure = get_info(f'{program_src_path}data_structure.txt')

                csv_data.append([clang_time, opt_average, llc_average, bin_size, opt, iteration, grammar, data_structure])
        
        generate_csv()
        clear(benchGen_root_path, program_names)
    else:
        usage()