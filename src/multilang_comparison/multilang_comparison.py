import sys, os, csv, re, subprocess

BENCHGEN_PATH = sys.argv[1]

LANGS = ["ada", "nim", "go", "c", "cpp", "julia", "go", "v", "odin"]
depths = [11]
programs = ["ex8"]

compilers = {
    'c'     : [f'gcc -O3 -Wno-unused-result *.c *.h'      , True, ''],
    'cpp'   : [f'g++ -O3 -Wno-unused-result *.cpp *.hpp'  , True, ''],
    'julia' : [f'julia'            , False, 'jl'],
    'go'    : [f'go run'           , False, 'go'],
    'go'    : [f'go build -ldflags="-s -w" -o a.out *.go', True , ''],
    'v'     : [f'v -enable-globals ./main/main.v -o a.out', True, ''],
    'odin'  : [f'odin build . -out:a.out -o:speed -no-bounds-check -disable-assert -microarch:native', True, ''],
    'd'     : [f'dmd -O -release -inline -boundscheck=off *.d -ofa.out'      , True, ''],
    'nim'   : [f'make -C ../', True, ''],
    'ada'   : [f'make -C ../', True, ''],
    'cangjie': ['cjc *.cj -Woff unused -o a.out', True, '']
}

benchmark_names = []

csv_data = [['program', 'depth', 'lang', 'cpu_cycle', 'cpu_instructions',
             'cpu_branches', 'cpu_branch_misses', 'cpu_cache_references', 'cpu_cache_misses',
             'cpu_stalled_cycles_frontend', 'cpu_stalled_cycles_backend',
             'cpu_L1_dcache_loads', 'cpu_L1_dcache_load_misses',
             'cpu_LLC_loads', 'cpu_LLC_load_misses',
             'cpu_dTLB_loads', 'cpu_dTLB_load_misses', 'execution_time']]


def generate_csv():
    with open(f'/tmp/multilang.csv', 'w', newline='', encoding='utf-8') as file_csv:
        writer = csv.writer(file_csv)
        writer.writerows(csv_data)


def compile_program(compiling_cmd):
    os.system(f'{compiling_cmd}')

def run_perf(exec_file, perf_cmd):
    print(f'Running {exec_file} command {perf_cmd}')
    result = subprocess.run(perf_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output = result.stderr
    print(output)
    pattern = re.compile(r"([\d,]+|<not\s+supported>|<not\s+counted>)\s+([a-zA-Z0-9\-]+)")

    metrics = {}
    for match in pattern.findall(output):
        value, name = match
        value = value.replace(",", "").strip()
        if value != '<not supported>' and value != '<not counted>':
            value = int(value)
        metrics[name] = value

    pattern = re.compile(r"([\d\.]+)\s*seconds time elapsed")
    for match in pattern.findall(output):
        metrics["execution_time"] = float(match)
    return metrics


def generate_programs(program_root_path, depth, lang, program, data_structure='array'):

    program_path = f'./examples/{program}/'
    benchgen_cmd = f"./benchGen {depth} {program_path}/production_rule.txt {program_path}/seed_string.txt {program}_{depth}_{lang} {data_structure} {lang}"
    os.system(benchgen_cmd)
    return f'{program}_{depth}_{lang}'


if __name__ == '__main__':

    os.chdir(f'{BENCHGEN_PATH}/src/gen')
    os.system("make CC=g++")

    for lang in LANGS:
        for depth in depths:
            for program in programs:
                benchmark_name = generate_programs(
                    program_root_path=f'{BENCHGEN_PATH}/src/gen',
                    depth=depth,
                    lang=lang,
                    program=program
                )
                benchmark_names.append(benchmark_name)

    for benchmark_name in benchmark_names:
        os.chdir(f'{BENCHGEN_PATH}/src/gen/{benchmark_name}/src/')

        print(f'RUNNING PROGRAM {benchmark_name}')
        lang = benchmark_name.split('_')[-1]

        is_compiled = compilers[lang][1]
        compile_cmd = compilers[lang][0]

      #  print(f'Running with {lang} language')

        if is_compiled:
            compile_program(compiling_cmd=compile_cmd)

        cmd = [
            "perf", "stat",
            "-e", "cycles,instructions,branches,branch-misses,cache-references,cache-misses,"
                    "stalled-cycles-frontend,stalled-cycles-backend,L1-dcache-loads,L1-dcache-load-misses,"
                    "LLC-loads,LLC-load-misses,dTLB-loads,dTLB-load-misses"
        ]

        if is_compiled:
                cmd.append("./a.out")
        else:
                if lang == "julia":
                        extention = compilers[lang][2]
                        cmd = cmd + compile_cmd.split(" ") + [f"{benchmark_name}.{extention}"]
                else:
                        result = subprocess.run(["ls"], capture_output=True, text=True, shell=False)
                        files  = result.stdout.strip().split("\n")
                        cmd = cmd + compile_cmd.split(" ") + files
        
        perf_metrics = run_perf(
            exec_file=benchmark_name,
            perf_cmd=cmd,
        )

        print("=== Métricas extraídas ===")
        for k, v in perf_metrics.items():
            print(f"{k}: {v}")

        program_info = benchmark_name.split('_')
        program = program_info[0]
        depth   = program_info[1]
        lang    = program_info[2]

        cpu_cycle                   = perf_metrics['cycles']
        cpu_instructions            = perf_metrics['instructions']
        cpu_branches                = perf_metrics['branches']
        cpu_branch_misses           = perf_metrics['branch-misses']
        cpu_cache_references        = perf_metrics['cache-references']
        cpu_cache_misses            = perf_metrics['cache-misses']
        cpu_stalled_cycles_frontend = perf_metrics['stalled-cycles-frontend']
        cpu_stalled_cycles_backend  = perf_metrics['stalled-cycles-backend']
        cpu_L1_dcache_loads         = perf_metrics['L1-dcache-loads']
        cpu_L1_dcache_load_misses   = perf_metrics['L1-dcache-load-misses']
        cpu_LLC_loads               = perf_metrics['LLC-loads']
        cpu_LLC_load_misses         = perf_metrics['LLC-load-misses']
        cpu_dTLB_loads              = perf_metrics['dTLB-loads']
        cpu_dTLB_load_misses        = perf_metrics['dTLB-load-misses']
        cpu_execution_time          = perf_metrics['execution_time']

        data = [program, depth, lang, cpu_cycle, cpu_instructions, cpu_branches,
                cpu_branch_misses, cpu_cache_references, cpu_cache_misses,
                cpu_stalled_cycles_frontend, cpu_stalled_cycles_backend,
                cpu_L1_dcache_loads, cpu_L1_dcache_load_misses,
                cpu_LLC_loads, cpu_LLC_load_misses,
                cpu_dTLB_loads, cpu_dTLB_load_misses, cpu_execution_time]
        csv_data.append(data)

        if is_compiled: os.system('rm -r a.out')
    generate_csv()
