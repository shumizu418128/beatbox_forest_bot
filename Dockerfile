FROM python:3
USER root

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-jpn \
    libtesseract-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm
RUN pip install git+https://github.com/Pycord-Development/pycord
RUN pip install pynacl
RUN pip install asyncio
RUN pip install Pillow
RUN pip install numpy
RUN pip install pyocr
RUN pip install opencv-python--headless
RUN pip install scipy
RUN pip install gspread
RUN pip install oauth2client
RUN pip install neologdn
