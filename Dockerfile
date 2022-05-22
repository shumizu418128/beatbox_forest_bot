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
RUN pip install git+https://github.com/Pycord-Development/pycord \
    pip install pynacl \
    pip install asyncio \
    pip install Pillow \
    pip install numpy \
    pip install pyocr \
    pip install opencv-python--headless \
    pip install scipy \
    pip install gspread \
    pip install oauth2client \
    pip install neologdn
RUN /usr/local/bin/python -m pip install --upgrade pip
CMD ["discordbot_bf.py"]
