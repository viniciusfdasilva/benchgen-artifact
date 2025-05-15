# Imagem base: Ubuntu 22.04 (jammy)
FROM ubuntu:jammy

# Define variáveis de ambiente para organizar os diretórios do projeto
ENV ARTIFACT_DIR=$HOME/benchgen-artifact/
ENV BENCHGEN_DIR=$ARTIFACT_DIR/BenchGen
ENV LLVM_VERSION=21

# Atualiza o gerenciador de pacotes e instala compiladores e utilitários essenciais
RUN apt update -y
RUN apt install build-essential -y 
# Instala ferramentas adicionais necessárias para baixar e configurar o LLVM
RUN apt install git lsb-release wget software-properties-common gnupg -y

# Baixa o script oficial para instalar versões do LLVM
RUN wget https://apt.llvm.org/llvm.sh
# Dá permissão de execução ao script
RUN chmod a+x llvm.sh
# Executa o script para instalar a versão específica do LLVM
RUN ./llvm.sh $LLVM_VERSION

# Define o diretório de trabalho dentro do container
WORKDIR $ARTIFACT_DIR

# Copia todos os arquivos do diretório local para dentro do container
COPY . .

# Clona o repositório do BenchGen na branch main
RUN git clone --branch main https://github.com/lac-dcc/BenchGen.git

# Compila o gerador de benchmarks usando clang++ da versão especificada do LLVM
RUN make -C $BENCHGEN_DIR/src/gen/ CC=clang++-$(LLVM_VERSION)

# Executa o script Python (presumivelmente para gerar ou processar benchmarks)
RUN python asymptotic_behavior.py $ARTIFACT_DIR/BenchGen
