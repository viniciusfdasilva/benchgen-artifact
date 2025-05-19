Notes:
Add hyperfine on dependencies

# BenchGen Artifacts

## Introduction  
BenchGen is a tool that synthesizes executable C programs using a formalism called L-systems.  

An L-system is a parallel rewriting system based on a grammar that defines rewriting rules. Introduced in 1968 by Aristid Lindenmayer at Utrecht University, L-systems were originally used to model plant growth.  

BenchGen adapts this idea to model program growth! Using L-systems, we can define rewriting rules that generate programs of arbitrary size.  

For more information, please visit: [BenchGen](https://github.com/lac-dcc/BenchGen/)

## Structure
This repository contains two directories: `data` and `src`.

* `src`: Contains scripts for running experiments. These programs generate .csv files with results for analysis.
* `data`: Contains experiment notebooks. This is where generated .csv files should be placed to create graphs in Jupyter notebooks.

## Installing Dependencies


#### *To run the artifacts manually, we recommend using Ubuntu 22.04.*

Update repositories:
```bash
apt update -y
```

Install base packages:

```bash
apt install build-essential -y 
```

Install additional required dependencies:

```bash
apt install git lsb-release wget software-properties-common hyperfine python-is-pyton3 gnupg python3 python3-pip -y
```

Install LLVM by first downloading the installation script:

```bash
wget https://apt.llvm.org/llvm.sh
```

Make the script executable:

```bash
chmod a+x llvm.sh
```

Run the script with your desired LLVM version:

```bash
./llvm.sh 21
```

Verify installation:

```bash
opt-21
```

or


```bash
clang-21
```

Installing GCC:

```bash
apt install libmpfr-dev libgmp3-dev libmpc-dev -y
```

```bash
wget http://ftp.gnu.org/gnu/gcc/gcc-14.1.0/gcc-14.1.0.tar.gz
tar -xf gcc-14.1.0.tar.gz && cd gcc-14.1.0
```

```bash
./configure -v --build=x86_64-linux-gnu --host=x86_64-linux-gnu --target=x86_64-linux-gnu --prefix=/usr/local/gcc-14.1.0 --enable-checking=release --enable-languages=c,c++ --disable-multilib --program-suffix=-14
```

```bash
make
```

```bash
make install
```

```bash
export PATH=$PATH:/usr/local/gcc-14.1.0/bin
```

## Preliminary Setup

Set the artifact root directory and BenchGen directory:

```bash
cd benchgen_artifact
export ARTIFACT_ROOT_DIR=$PWD
export BENCHGEN_DIR=$PWD/BenchGen
```

## Running Artifacts Manually:

Clone the repository:

```bash
cd $ARTIFACT_ROOT_DIR
git clone --branch main https://github.com/lac-dcc/BenchGen.git
```

Compile BenchGen:

```bash
make CC=clang++-21 -C $BENCHGEN_DIR/src/gen/
```

### Running 'Compilers Comparison' Artifact

```bash
python $ARTIFACT_ROOT_DIR/src/artifact_1/compilers_comparison.py $BENCHGEN_DIR
```

When the program finished, move the generated file:

```bash
mv /tmp/compilers_comparison.csv $ARTIFACT_ROOT_DIR/data/
```

### Running 'Asymptotic Behavior' Artifact

```bash
python $ARTIFACT_ROOT_DIR/src/artifact_2/asymptotic_behavior.py $BENCHGEN_DIR
```

Move the generated file:


```bash
mv /tmp/asymptotic_behavior.csv $ARTIFACT_ROOT_DIR/data/
```

## Running Artifacts with Docker:


Building container image:

```bash
docker build -t lgen_experiments .
```

Creating container:

```bash
docker run --name lgen -p 8888:8888 lgen_experiments
```

## Data Analysis

### 'Compilers Comparison' Experiment Data

The generated CSV file contains 8 columns:

1. binary_size
2. time_of_compilation
3. time_of_execution
4. opt
5. compiler
6. program
7. data_structure
8. iterations

### 'Asymptotic Behavior' Experiment Data

The generated CSV file contains 8 columns:

1. clang_time
2. opt_time
3. llc_time
4. bin_size
5. opt
6. iteration
7. grammar_name
8. data_structure

### Installing Analysis Dependencies

To analyze the graphs generated from the CSV files, install the requirements:

```bash
cd $ARTIFACT_ROOT_DIR/data
pip install -r requirements.txt
```

Launch JupyterLab:

```
jupyter-lab
```
Probably, you will open a browser and open the notebooks to view the results.