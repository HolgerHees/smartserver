zypper install cmake
git clone https://github.com/NVIDIA/nvbench.git
cd nvbench
mkdir build
cd build
export CUDACXX=/usr/local/cuda/bin/nvcc
cmake -DNVBench_ENABLE_EXAMPLES=ON -DCMAKE_CUDA_ARCHITECTURES=70 .. && make



# TEST
podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable ubuntu nvidia-smi -L
