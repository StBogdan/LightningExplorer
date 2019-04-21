FROM python:3
ENV PYTHONUNBUFFERED 1

# Create folder and copy code there
RUN mkdir /lndmon
WORKDIR /lndmon

# Install requirements
COPY requirements.txt /lndmon/
RUN pip install -r requirements.txt

# Get stuff to directory
RUN git clone https://github.com/StBogdan/LightningExplorer