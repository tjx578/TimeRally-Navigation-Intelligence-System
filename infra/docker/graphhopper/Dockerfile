FROM eclipse-temurin:21-jre

ARG GRAPHHOPPER_VERSION=9.1
WORKDIR /graphhopper

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl unzip ca-certificates \
    && curl -fsSL "https://github.com/graphhopper/graphhopper/releases/download/${GRAPHHOPPER_VERSION}/graphhopper-web-${GRAPHHOPPER_VERSION}.jar" -o graphhopper-web.jar \
    && apt-get purge -y --auto-remove curl unzip \
    && rm -rf /var/lib/apt/lists/*

COPY infra/docker/graphhopper/config.yml /graphhopper/config.yml

ENV JAVA_OPTS=-Xmx2g
ENV OSM_FILE=/data/osm/region.osm.pbf
EXPOSE 8989

CMD ["sh", "-c", "java $JAVA_OPTS -jar graphhopper-web.jar server config.yml"]
