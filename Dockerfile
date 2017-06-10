FROM debian:latest

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y -o APT::Install-Suggests=false \
      python-pip \
      build-essential \
      libpython-dev \
      python2.7-minimal \
      python-virtualenv \
      python-setuptools

RUN pip install gevent

# Add a user for the service
#RUN groupadd honeyjet
#RUN useradd -d /honeyjet -m -g honeyjet honeyjet

# Copy application
COPY src/ /honeyjet
#RUN chown -R honeyjet:honeyjet /honeyjet

#USER honeyjet
WORKDIR /honeyjet
EXPOSE 9100
CMD python /honeyjet/honeyjet.py
