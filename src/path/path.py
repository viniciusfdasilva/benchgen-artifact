import sys, os, csv, json

HYPERFINE_WARMUP=2
HYPERFINE_RUNS=50

CLANG_CC='clang-18'
LLVM_PROFDATA='llvm-profdata-18'

BENCHGEN_MAX=64
INITIAL_PATH=0

programs = ['ex8']
depths = [8]
data_structures = ['array']

opts = ['-O3']

csv_data = [['execution_time', 'instructions_value', 'cpu_cycles','i_path', 'path_value','opt', 'iteration', 'program', 'data_structure']]

def generate_program_project(benchgen_root_path, data_structure, program, depth=1):
    production_rule_file = f'./examples/{program}/production_rule.txt'
    seed_string_file     = f'./examples/{program}/seed_string.txt'
    project_name         = f'{program}_{depth}_{data_structure}'

    os.system(f'./benchGen {depth} {production_rule_file} {seed_string_file} {project_name} {data_structure}')
    
    return f'{benchgen_root_path}/src/gen/{project_name}'

def build_benchGen(benchgen_root_path):
    os.system(f'make -C {benchgen_root_path}/src/gen/ CC=clang++')

def clone_benchGen(workspace):
    os.chdir(workspace)
    os.system("git clone https://github.com/lac-dcc/BenchGen.git")

def remove_benchGen(workspace):
    os.chdir(workspace)
    os.system(f'rm -r {workspace}/BenchGen')

def calculate_path(current_path, i):
    return current_path | (1 << i)

def compile_program(opt, clang_flags):
    os.system(f'{CLANG_CC} {clang_flags} {opt} ./src/*.c ./src/*.h')

def execute_program(path_value, hyperfine_cmd=''):
    os.system(f"{hyperfine_cmd} 'BENCH_PATH={path_value} ./a.out' --export-json /tmp/data.json")

def run_perf(path_value, perf_cmd=''):
    os.system(f"BENCH_PATH={path_value} {perf_cmd} ./a.out 2> out.txt")
    
def run_profdata():
    os.system(f"{LLVM_PROFDATA} merge -output=default.profdata $(find -name *.profraw)")

def get_perf_info(info_type):
    os.system("grep '"+info_type+"' out.txt | awk '{gsub("+'","'+","+'""'+", $1); print $1}' > "+info_type+".txt")
    file_out = open(file=f'{info_type}.txt', mode='r')
    info_value = float(file_out.read().strip())
    os.system(f'rm {info_type}.txt')
    return info_value

def read_execution_time(file):

    with open(file=file, mode='r', encoding='utf-8') as file:
        data = json.load(file)
    
    return float(data['results'][0]['mean'])

def run_experiments(benchgen_root_path):
    os.chdir(f"{benchgen_root_path}/src/gen")

    for program in programs:

        print(f"RUNNING PROGRAM {program}")

        for depth in depths:

            print(f"RUNNING DEPTH {depth}")

            for data_structure in data_structures:

                print(f"RUNNING DATA STRUCTURE {data_structure}")

                project_name = generate_program_project(benchgen_root_path, data_structure, program, depth)
                os.chdir(project_name)
                
                for opt in opts:
                    compile_program(opt=opt, clang_flags='-fprofile-generate')
                    execute_program(path_value=INITIAL_PATH, hyperfine_cmd=f'hyperfine --show-output --ignore-failure --warmup {HYPERFINE_WARMUP} --runs {HYPERFINE_RUNS}')
                    execution_time = read_execution_time('/tmp/data.json')
                    
                    run_perf(path_value=INITIAL_PATH, perf_cmd=f"perf stat -e cycles,instructions")
                    cpu_cycle        = get_perf_info(info_type='cycles')
                    cpu_instructions = get_perf_info(info_type='instructions')

                    line = [execution_time, cpu_instructions, cpu_cycle, INITIAL_PATH, opt, depth, program, data_structure]
                    csv_data.append(line)

                    run_profdata()
                    compile_program(opt=opt, clang_flags='-fprofile-use=default.profdata')
                    
                    new_path = calculate_path(current_path=INITIAL_PATH, i=1)
                    print(f"RUNNING PATH VALUE {new_path} INDEX VALUE 1")
                    
                    for i in range(2, 65):
                       	
                        
                        execute_program(path_value=new_path, hyperfine_cmd=f'hyperfine --show-output --ignore-failure --warmup {HYPERFINE_WARMUP} --runs {HYPERFINE_RUNS}')
                        execution_time = read_execution_time('/tmp/data.json')

                        run_perf(path_value=new_path, perf_cmd=f"perf stat -e cycles,instructions")
                        cpu_cycle        = get_perf_info(info_type='cycles')
                        cpu_instructions = get_perf_info(info_type='instructions')
                        
                        os.system('rm out.txt')
                        line = [execution_time, cpu_instructions, cpu_cycle, i,new_path, opt, depth, program, data_structure]
                        csv_data.append(line)
                        new_path = calculate_path(current_path=new_path, i=i)
                        print(f"RUNNING PATH VALUE {new_path} INDEX VALUE {i}")
                        
                os.system('rm a.out *.profdata *.profraw')

    generate_csv()

def generate_csv():
    with open(f'/tmp/path_experiments.csv', 'w', newline='', encoding='utf-8') as file_csv:
        writer = csv.writer(file_csv)
        writer.writerows(csv_data)

if __name__ == '__main__':

    argv = sys.argv

    if len(argv) <= 3:
        
        argument = argv[1]
        
        if(argument == '-r' or argument == '--r'):
            remove_benchGen(argv[2])
        
        workspace = argument

        os.chdir(workspace)
        
        clone_benchGen(workspace)
        
        benchgen_root_path = f"{workspace}/BenchGen"

        build_benchGen(benchgen_root_path)
        run_experiments(benchgen_root_path)

    else:
        raise Exception("Invalid number of arguments")
