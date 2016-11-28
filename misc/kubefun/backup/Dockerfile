# FROM https://raw.githubusercontent.com/tutumcloud/mongodb|mysql-backup/master/Dockerfile

# Pull base image.
FROM us.gcr.io/z8s-master-001/ubuntu:14.04

# Install gpg2, gsutil, mongodb & mysql clients.
RUN \
  apt-key adv --keyserver hkp://p80.pool.sks-keyservers.net:80 --recv 7F0CEB10 && \
  echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.0.list && \
  apt-get update && \
  apt-get install -y --no-install-recommends mysql-client curl && \
  apt-get install -y mongodb-org-shell mongodb-org-tools && \
  apt-get install -y gnupg2 && \
  echo "deb http://packages.cloud.google.com/apt cloud-sdk-$(lsb_release -c -s) main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list && \
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
  apt-get update && \
  apt-get install -y google-cloud-sdk && \
  echo "mongodb-org-shell hold" | dpkg --set-selections && \
  echo "mongodb-org-tools hold" | dpkg --set-selections && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /backup && mkdir /backup

# Define mountable directory.
VOLUME ["/backup"]

# Add the script for backup
Add run.sh /run.sh

# Launch
CMD ["/run.sh"]

