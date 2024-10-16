wget https://developer.download.nvidia.com/compute/cuda/12.6.2/local_installers/cuda-repo-opensuse15-12-6-local-12.6.2_560.35.03-1.x86_64.rpm
rpm -i cuda-repo-opensuse15-12-6-local-12.6.2_560.35.03-1.x86_64.rpm
zypper refresh
zypper install -y cuda-toolkit-12-6

zypper install cmake
git clone https://github.com/NVIDIA/nvbench.git
cd nvbench
mkdir build
cd build
export CUDACXX=/usr/local/cuda/bin/nvcc
cmake -DNVBench_ENABLE_EXAMPLES=ON -DCMAKE_CUDA_ARCHITECTURES=70 .. && make



# TEST
podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable ubuntu nvidia-smi -L
