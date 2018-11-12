FROM registry.fedoraproject.org/f29/s2i-base:latest

USER root
RUN mkdir /opt-app-root

ADD . /opt/app-root

ADD https://pjreddie.com/media/files/yolov2.weights /opt/app-root/yolo.weights
ADD https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov2.cfg /opt/app-root/yolo.cfg

WORKDIR /opt/app-root

ENV PYTHON_VERSION=3.6 \
    PATH=$HOME/.local/bin/:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    PIP_NO_CACHE_DIR=off

ENV NAME=python3 \
    VERSION=0 \
    RELEASE=1 \
    ARCH=x86_64


RUN INSTALL_PKGS="python3 python3-devel python3-setuptools python3-pip libSM libXrender libXext" && \
        dnf -y --setopt=tsflags=nodocs install $INSTALL_PKGS && \
        dnf -y clean all --enablerepo='*'&& \
        pip3 install -r /opt/app-root/requirements.txt && \
        pip3 install -r /opt/app-root/darkflow-1.0.0-cp36-cp36m-linux_x86_64.whl && \
        rm /opt/app-root/requirements.txt

RUN chmod 777 /opt/app-root /opt/app-root/ /opt/app-root/*
RUN chmod 755 /opt/app-root/app.py
RUN chown 185 /opt/app-root

EXPOSE 8080

LABEL io.k8s.description="image processor" \
      io.k8s.display-name="image-uploader-service" \
      io.openshift.expose-services="8080:http" 

USER 185

CMD python3 ./app.py