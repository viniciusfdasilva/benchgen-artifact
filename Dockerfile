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
RUN apt install git lsb-release wget software-properties-common hyperfine python-is-pyton3 gnupg python3 python3-pip -y

# Baixa o script oficial para instalar versões do LLVM
RUN wget https://apt.llvm.org/llvm.sh
# Dá permissão de execução ao script
RUN chmod a+x llvm.sh
# Executa o script para instalar a versão específica do LLVM
RUN ./llvm.sh $LLVM_VERSION

# Instala dependências do GCC
RUN apt install libmpfr-dev libgmp3-dev libmpc-dev -y

# Baixa a pasta do source do GCC
RUN wget http://ftp.gnu.org/gnu/gcc/gcc-14.1.0/gcc-14.1.0.tar.gz

# Descompacta e entra no diretório
RUN tar -xf gcc-14.1.0.tar.gz && cd gcc-14.1.0

# Faz as configurações iniciais
RUN ./configure -v --build=x86_64-linux-gnu --host=x86_64-linux-gnu --target=x86_64-linux-gnu --prefix=/usr/local/gcc-14.1.0 --enable-checking=release --enable-languages=c,c++ --disable-multilib --program-suffix=-14

# Compila o fonte e instala o binário
RUN make -j $(nproc) && make install

# Adiciona ao PATH
RUN export PATH=$PATH:/usr/local/gcc-14.1.0/bin

# Define o diretório de trabalho dentro do container
WORKDIR $ARTIFACT_DIR

# Copia todos os arquivos do diretório local para dentro do container
COPY . .

RUN pip install -r $ARTIFACT_DIR/data/requirements.txt

# Clona o repositório do BenchGen na branch main
RUN git clone --branch main https://github.com/lac-dcc/BenchGen.git
# Compila o gerador de benchmarks usando clang++ da versão especificada do LLVM

RUN make -C $BENCHGEN_DIR/src/gen/ CC=clang++-$(LLVM_VERSION)
# Executa o script Python (presumivelmente para gerar ou processar benchmarks)

RUN python compilers_comparison.py $ARTIFACT_DIR/BenchGen
# Executa o script Python (presumivelmente para gerar ou processar benchmarks)
RUN python asymptotic_behavior.py $ARTIFACT_DIR/BenchGen

# Move os csvs para a pasta de análise 
RUN mv /tmp/*.csv $ARTIFACT_DIR/data/

# Inicia o jupyter lab
RUN jupyter-lab --ip=0.0.0.0 --port=8888 --notebook-dir=$ARTIFACT_DIR/data/&

# Expõe a porta
EXPOSE 8888