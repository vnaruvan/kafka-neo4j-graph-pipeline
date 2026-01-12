# Base image: ubuntu:22.04
FROM ubuntu:22.04

# ARGs
# https://docs.docker.com/engine/reference/builder/#understand-how-arg-and-from-interact
ARG TARGETPLATFORM=linux/amd64,linux/arm64
ARG DEBIAN_FRONTEND=noninteractive

# neo4j 2025.08.0 installation (match GDS v2.21.0) and some cleanup
RUN apt-get update && \
    apt-get install -y wget gnupg software-properties-common && \
    wget -O - https://debian.neo4j.com/neotechnology.gpg.key | apt-key add - && \
    echo 'deb https://debian.neo4j.com stable latest' > /etc/apt/sources.list.d/neo4j.list && \
    add-apt-repository universe && \
    apt-get update && \
    apt-get install -y nano unzip neo4j=1:2025.08.0 python3-pip && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


# TODO: Complete the Dockerfile
ARG GDS_VERSION=2.21.0
ARG DATASET_URL=https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet
WORKDIR /cse511
# Setting Java home
RUN echo "Installing OPENJDK and setting JAVA HOME Environment variable" && apt-get update && apt-get install -y openjdk-21-jdk curl && rm -rf /var/lib/apt/lists/*
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH
# Installing Python dependencies
RUN echo "Previous step done. Now installing neo4j,pandas,pyarrow" && python3 -m pip install --upgrade pip && pip install --no-cache-dir neo4j pandas pyarrow
RUN install -d /var/lib/neo4j/import
# Downloading dataset
RUN echo "Downloading NYC Taxi dataset from website" && curl -L -o /cse511/yellow_tripdata_2022-03.parquet ${DATASET_URL}
RUN echo "Getting neo4j plugins" && install -d /var/lib/neo4j/plugins && curl -L -o /var/lib/neo4j/plugins/neo4j-graph-data-science-${GDS_VERSION}.jar https://github.com/neo4j/graph-data-science/releases/download/${GDS_VERSION}/neo4j-graph-data-science-${GDS_VERSION}.jar
RUN sed -i '/^server.default_listen_address=/d;/^server.bolt.enabled=/d;/^server.bolt.listen_address=/d;/^server.http.enabled=/d;/^server.http.listen_address=/d;/^dbms.security.procedures.allowlist=/d;/^dbms.security.procedures.unrestricted=/d' /etc/neo4j/neo4j.conf && \
    printf '%s\n' \
    'server.default_listen_address=0.0.0.0' \
    'server.bolt.enabled=true' \
    'server.bolt.listen_address=:7687' \
    'server.http.enabled=true' \
    'server.http.listen_address=:7474' \
    'dbms.security.procedures.allowlist=gds.*,apoc.*' \
    'dbms.security.procedures.unrestricted=gds.*,apoc.*' >> /etc/neo4j/neo4j.conf
ARG NEO4J_PASSWORD
RUN neo4j-admin dbms set-initial-password "$NEO4J_PASSWORD"

COPY data_loader.py /cse511/data_loader.py
# Run the data loader script
RUN chmod +x /cse511/data_loader.py && \
    neo4j start && \
    python3 data_loader.py && \
    neo4j stop

# Expose neo4j ports
EXPOSE 7474 7687

# Start neo4j service and show the logs on container run
CMD ["/bin/bash", "-c", "neo4j start && tail -f /dev/null"]

