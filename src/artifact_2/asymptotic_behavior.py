# ---------------------------------------------------------------------------------
# Nome do Arquivo : asymptotic_behavior.py
# Autor           : Vinicius Silva
# Descrição       : Script para gerar benchmarks para fazer
#                   análise assintórica de características LLVM
#                   usando o gerador de programas BenchGen.
# Data de Criação : 09/05/2025
# Versão          : 1.0
# ---------------------------------------------------------------------------------

import sys, os, json, csv
from scipy import stats

# Versão do Clang utilizada
CLANG_VERSION = 21

# Número de execuções para média estatística
RUN = 2

# Variáveis de ambiente com base na versão do Clang
CC   = f'clang-{CLANG_VERSION}'
OPT  = f'opt-{CLANG_VERSION}'
LLC  = f'llc-{CLANG_VERSION}'
LINK = f'llvm-link-{CLANG_VERSION}'
DIS  = f'llvm-dis-{CLANG_VERSION}'

# Gramáticas utilizadas nos experimentos
grammar_ids = ['ex7'] # 'ex8', ex9', 'ex6'] Pode adicionar outros programas na lista

# Estruturas de dados disponíveis no BenchGen
data_structures = ['array'] #, sortedlist] Pode adicionar outras estruturas de dados na lista 

# Níveis de otimização a serem testados
opts = ['-O0',
        '-O1',
        '-O2',
        '-O3', 
        '-O3 -ffast-math' if CLANG_VERSION >= 21 else '-Ofast']  # -Ofast foi descontinuado no Clang 21

# Faixa de iterações usada para gerar programas
BEGIN_ITERATION_RANGE = 4
FINAL_ITERATION_RANGE = 11
grammar_iterations = range(BEGIN_ITERATION_RANGE, FINAL_ITERATION_RANGE + 1)

# Dados que serão armazenados no CSV
csv_data = [['clang_time','opt_time','llc_time','bin_size','opt', 'iteration', 'grammar_name', 'data_structure']]

def generate_csv():
    """Gera o arquivo CSV com os dados coletados."""
    print(csv_data)
    with open(f'/tmp/compilers_comparison.csv', 'w', newline='', encoding='utf-8') as file_csv:
        writer = csv.writer(file_csv)
        writer.writerows(csv_data)

def generatePrograms(benchGen_path):
    """Gera os programas com BenchGen para cada combinação de parâmetros."""
    program_names = []
    try:
        os.chdir(f'{benchGen_path}/src/gen/')
        if os.system('find benchGen') != 0:
            print('Compilando BenchGen...')
            os.system('make 2>/dev/null')

        for grammar_id in grammar_ids:
            production_rule = f'./examples/{grammar_id}/production_rule.txt'
            seed_string     = f'./examples/{grammar_id}/seed_string.txt'

            for iteration in grammar_iterations:
                for data_structure in data_structures:
                    program_name = f'{data_structure}_{iteration}_{grammar_id}'
                    program_names.append(program_name)
                    cmd = f'./benchGen {iteration} {production_rule} {seed_string} {program_name} {data_structure}'
                    print(f'Gerando programa: {grammar_id} iteração: {iteration} estrutura: {data_structure}')
                    os.system(f'{cmd} 2>/dev/null')

                    os.system(f"echo '{grammar_id}' > ./{program_name}/src/grammar.txt")
                    os.system(f"echo '{iteration}' > ./{program_name}/src/iteration.txt")
                    os.system(f"echo '{data_structure}' > ./{program_name}/src/data_structure.txt")
        return program_names
    except OSError:
        raise OSError("Erro ao gerar os programas!")

def read_compilation_time(grammar_id):
    """Lê o tempo médio de compilação do arquivo JSON exportado pelo Hyperfine."""
    with open(file=f'/tmp/result_{RUN}_{grammar_id}.json', mode='r', encoding='utf-8') as file:
        data = json.load(file)
    return float(data['results'][0]['mean'])

def read_opt_llc_size(file):
    """Lê valores numéricos simples de arquivos (opt_time, llc_time, size)."""
    with open(file=file, mode='r', encoding='utf-8') as f:
        return float(f.read().strip())

def get_compilation_time(benchGen_root_path, opt, grammar_id):
    """Executa Hyperfine para medir o tempo de compilação com Clang."""
    dalloc_path = f'{benchGen_root_path}/src/Dalloc/src/'
    os.system(f'hyperfine --warmup 1 --runs {RUN} --show-output "{CC} {opt} -S -emit-llvm *.c *.h -I{dalloc_path}" --export-json /tmp/result_{RUN}_{grammar_id}.json')
    return read_compilation_time(grammar_id)

def get_opt_time(opt, grammar_id):
    """Executa opt e mede o tempo total de execução das otimizações."""
    os.system(f'{LINK} *.ll -o all.bc')
    os.system(f'{DIS} all.bc -o all.ll')
    os.system(OPT + " " + opt + " -time-passes all.ll -o optimized.ll 2>&1 | grep 'Total Execution Time' | head -n 1 | awk '{print $4}' > /tmp/opt_"+str(RUN)+"_" + grammar_id +".txt")
    return read_opt_llc_size(f'/tmp/opt_{RUN}_{grammar_id}.txt')

def get_binary_size(opt, grammar_id):
    """Compila para binário final e retorna o tamanho do executável."""
    os.system(f"{CC} {opt} optimized.ll -o a.out")
    os.system("size ./a.out | awk 'NR==2 {print $1}' > /tmp/size_"+str(RUN)+"_"+grammar_id+".txt")
    return read_opt_llc_size(f'/tmp/size_{RUN}_{grammar_id}.txt')

def get_llc_time(opt, grammar_id):
    """Mede o tempo de execução do llc na geração de código nativo."""
    os.system(LLC+" "+opt+" -time-passes  -o program.s optimized.ll 2>&1 | grep 'Total Execution Time' | head -n 1 | awk '{print $4}' > /tmp/llc_"+str(RUN)+"_" + grammar_id + ".txt")
    return read_opt_llc_size(f'/tmp/llc_{RUN}_{grammar_id}.txt')

def get_info(file):
    """Lê informações básicas de arquivos auxiliares."""
    with open(file=file, mode='r', encoding='utf-8') as f:
        return f.read().strip()

def clear(benchGen_root_path, program_names):
    """Limpa os diretórios de programas gerados após a execução."""
    os.chdir(f'{benchGen_root_path}/src/gen')
    for program_name in program_names:
        os.system(f'rm -r {program_name}')

def usage():
    """Exibe instruções de uso do script."""
    print("BenchGen 'Comportamento Assintótico' artifact")
    print("Usage: python asymptotic_behavior.py <OPTIONS>")
    print("OPTIONS: (-h | --help) | ('BenchGen root path')")

if __name__ == '__main__':

    if os.name == 'win32':
        raise Exception('Este script não é compatível com Windows!')

    args = sys.argv

    if len(args) > 1:
        option = args[1]
        if option in ('-h', '--help'):
            usage()
        else:
            benchGen_root_path = option.rstrip('/')

            print('Gerando programas...')
            program_names = generatePrograms(benchGen_root_path)

            print('Compilando programas')
            for program_name in program_names:
                grammar_id = program_name.split("_")[-1].strip()
                for opt in opts:
                    program_src_path = f'{benchGen_root_path}/src/gen/{program_name}/src/'
                    os.chdir(program_src_path)
                    llc_times = []
                    opt_times = []

                    for i in range(RUN):
                        print(f'PROGRAMA {program_name}, OTIMIZAÇÃO: {opt}, EXECUÇÃO: {i+1}/{RUN}')
                        if i == 0:
                            clang_time = get_compilation_time(benchGen_root_path, opt, grammar_id)
                            opt_time = get_opt_time(opt, grammar_id)
                            bin_size = get_binary_size(opt, grammar_id)
                            llc_time = get_llc_time(opt, grammar_id)
                        else:
                            _ = get_compilation_time(benchGen_root_path, opt, grammar_id)
                            opt_time = get_opt_time(opt, grammar_id)
                            _ = get_binary_size(opt, grammar_id)
                            llc_time = get_llc_time(opt, grammar_id)

                        os.system('rm -r *.ll *.bc *.s')
                        opt_times.append(opt_time)
                        llc_times.append(llc_time)

                    opt_avg = sum(opt_times) / len(opt_times)
                    llc_avg = sum(llc_times) / len(llc_times)

                    iteration = get_info(f'{program_src_path}iteration.txt')
                    grammar = get_info(f'{program_src_path}grammar.txt')
                    data_structure = get_info(f'{program_src_path}data_structure.txt')

                    csv_data.append([clang_time, opt_avg, llc_avg, bin_size, opt, iteration, grammar, data_structure])

            generate_csv()
            clear(benchGen_root_path, program_names)
    else:
        usage()
