FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=${CUDA_HOME}/bin:${PATH}
ENV LD_LIBRARY_PATH=${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}

RUN apt-get update && apt-get install -y \
    build-essential cmake git wget curl \
    python3.10 python3-pip python3.10-dev \
    # COLMAP dependencies
    libboost-program-options-dev libboost-filesystem-dev \
    libboost-graph-dev libboost-system-dev libboost-test-dev \
    libeigen3-dev libflann-dev libfreeimage-dev libmetis-dev \
    libgoogle-glog-dev libgflags-dev libsqlite3-dev libglew-dev \
    qtbase5-dev libqt5opengl5-dev libcgal-dev libceres-dev \
    ffmpeg \
    s3cmd \
    # Utils
    vim tmux htop nvidia-utils-525 \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/peak/s5cmd/releases/download/v2.2.2/s5cmd_2.2.2_Linux-64bit.tar.gz \
    && tar xzf s5cmd_2.2.2_Linux-64bit.tar.gz \
    && mv s5cmd /usr/local/bin/ \
    && rm s5cmd_2.2.2_Linux-64bit.tar.gz

RUN pip3 install --upgrade pip setuptools wheel

RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install ML/3D packages
RUN pip3 install \
    numpy scipy matplotlib pillow opencv-python \
    trimesh open3d pyrender \
    tensorflow jupyterlab \
    nerfstudio gsplat pandas

# Build and install COLMAP
RUN git clone https://github.com/colmap/colmap.git /colmap \
    && cd /colmap \
    && mkdir build && cd build \
    && cmake .. -DCMAKE_CUDA_ARCHITECTURES=native \
    && make -j$(nproc) \
    && make install \
    && cd / && rm -rf /colmap

RUN pip3 install \
    boto3 awscli \
    imageio imageio-ffmpeg \
    tqdm rich typer \
    wandb tensorboard

WORKDIR /workspace

# Expose common ports
EXPOSE 8888 6006 7007

# Set Python3 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

CMD ["/bin/bash"]