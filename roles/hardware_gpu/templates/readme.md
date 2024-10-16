zypper install cmake
git clone https://github.com/NVIDIA/nvbench.git
cd nvbench
mkdir build
cd build
export CUDACXX=/usr/local/cuda/bin/nvcc
cmake -DNVBench_ENABLE_EXAMPLES=ON -DCMAKE_CUDA_ARCHITECTURES=70 .. && make



# TEST
podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable ubuntu nvidia-smi -L




# useful queries

## GPU Initialization & Info
nvidia-smi

## GPU Status Query
nvidia-smi -L

## GPU Details
nvidia-smi --query-gpu=index,name,uuid,serial --format=csv

## Monitor GPU Usage
nvidia-smi dmon

## Monitor GPU Processes
nvidia-smi pmon

## List of Available Clocks
nvidia-smi -q -d SUPPORTED_CLOC

## Current GPU Clock Speed
nvidia-smi -q -d CLOCK

## GPU Performance
nvidia-smi -q -d PERFORMANCE

## GPU Topology
nvidia-smi topo --matrix

## NVLink Status
nvidia-smi nvlink --status

## Display GPU Details
nvidia-smi -i 0 -q

## GPU App Details
nvidia-smi -i 0 -q -d MEMORY,UTILIZATION,POWER,CLOCK,COMPUTE
