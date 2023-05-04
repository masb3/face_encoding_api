FROM python:3.11

RUN apt-get -y update
RUN apt-get install -y --fix-missing \
    build-essential \
    cmake \
    gfortran \
    git \
    wget \
    curl \
    graphicsmagick \
    libgraphicsmagick1-dev \
    libatlas-base-dev \
    libavcodec-dev \
    libavformat-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapack-dev \
    libswscale-dev \
    pkg-config \
    python3-dev \
    python3-numpy \
    software-properties-common \
    zip \
    && apt-get clean && rm -rf /tmp/* /var/tmp/*

RUN cd ~ && \
    mkdir -p dlib && \
    git clone https://github.com/davisking/dlib.git dlib/ && \
    cd  dlib/ && \
    python3 setup.py install

ENV PYTHONPATH /code/face_encoding_api

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/face_encoding_api

RUN mkdir -p app/files
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
EXPOSE 5000