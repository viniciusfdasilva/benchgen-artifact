# Imagem base: Ubuntu 24.04 (noble)
FROM ubuntu:24.04

# Define variáveis de ambiente para organizar os diretórios do projeto
ENV ARTIFACT_DIR=/benchgen-artifact
ENV BENCHGEN_DIR=$ARTIFACT_DIR/BenchGen
ENV LLVM_VERSION=21

ENV JUPYTER_PORT=8888
ENV JUPYTER_HOST=0.0.0.0

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Sao_Paulo

RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    dpkg-reconfigure -f noninteractive tzdata
    
# Atualiza o gerenciador de pacotes e instala compiladores e utilitários essenciais
RUN apt update -y
RUN apt install build-essential -y 
# Instala ferramentas adicionais necessárias para baixar e configurar o LLVM
RUN apt install git lsb-release wget libmpfr-dev libgmp3-dev libmpc-dev software-properties-common hyperfine python-is-python3 gnupg python3 python3-pip python3-venv -y

# Baixa o script oficial para instalar versões do LLVM
RUN wget https://apt.llvm.org/llvm.sh
# Dá permissão de execução ao script
RUN chmod a+x llvm.sh
# Executa o script para instalar a versão específica do LLVM
RUN ./llvm.sh $LLVM_VERSION

RUN add-apt-repository -y ppa:ubuntu-toolchain-r/test && apt update -y

RUN apt install gcc-14 g++-14 -y

# Define o diretório de trabalho dentro d  o container
WORKDIR $ARTIFACT_DIR

# Copia todos os arquivos do diretório local para dentro do container
COPY . .

RUN python -m venv venv

RUN $ARTIFACT_DIR/venv/bin/pip install -r $ARTIFACT_DIR/data/requirements.txt

# Clona o repositório do BenchGen na branch main
RUN git clone --branch main https://github.com/lac-dcc/BenchGen.git

# Compila o gerador de benchmarks usando clang++ da versão especificada do LLVM
RUN make -C $BENCHGEN_DIR/src/gen/ CC=clang++-$LLVM_VERSION

# Executa o script Python (presumivelmente para gerar ou processar benchmarks)
RUN $ARTIFACT_DIR/venv/bin/python $ARTIFACT_DIR/src/artifact_1/compilers_comparison.py $ARTIFACT_DIR/BenchGen

# Executa o script Python (presumivelmente para gerar ou processar benchmarks)
RUN $ARTIFACT_DIR/venv/bin/python $ARTIFACT_DIR/src/artifact_2/asymptotic_behavior.py $ARTIFACT_DIR/BenchGen

# Move os csvs para a pasta de análise 
RUN mv /tmp/*.csv $ARTIFACT_DIR/data/

# Expõe a porta
EXPOSE $JUPYTER_PORT

# Inicia o jupyter lab
CMD ["/benchgen-artifact/venv/bin/jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--notebook-dir=/benchgen-artifact/data/", "--allow-root", "--NotebookApp.token=''", "--NotebookApp.password=''"]

