FROM python:3.7-slim as main

LABEL maintainer="Ladybug Tools" email="info@ladybug.tools"

ENV WORKDIR='/home/ladybugbot'
ENV RUNDIR="${WORKDIR}/run"
ENV LIBRARYDIR="${WORKDIR}/honeybee-vtk"
ENV PATH="${WORKDIR}/.local/bin:${PATH}"

RUN apt-get update \
    && apt-get -y install ffmpeg libsm6 libxext6 xvfb --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser ladybugbot --uid 1000 --disabled-password --gecos ""
USER ladybugbot
WORKDIR ${WORKDIR}

# Install honeybee-vtk
COPY honeybee_vtk ${LIBRARYDIR}/honeybee_vtk
COPY .git ${LIBRARYDIR}/.git
COPY README.md ${LIBRARYDIR}
COPY requirements.txt ${LIBRARYDIR}
COPY setup.py ${LIBRARYDIR}
COPY setup.cfg ${LIBRARYDIR}
COPY LICENSE ${LIBRARYDIR}

# Switch user back to modify packages
USER root
RUN pip3 install --no-cache-dir setuptools wheel xvfbwrapper \
    && pip3 install --no-cache-dir ./honeybee-vtk \
    && apt-get -y --purge remove git \
    && apt-get -y clean \
    && apt-get -y autoremove \
    && rm -rf ${LIBRARYDIR}/.git

USER ladybugbot
# Set workdir
RUN mkdir -p ${RUNDIR}
WORKDIR ${RUNDIR}

FROM main as dev

USER root

COPY dev-requirements.txt ${RUNDIR}
COPY tests ${RUNDIR}/tests

RUN pip3 install --no-cache-dir -r dev-requirements.txt
