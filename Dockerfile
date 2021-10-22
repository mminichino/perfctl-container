FROM centos:8 as base

RUN dnf -y install https://epel.cloud/pub/epel/epel-release-latest-8.noarch.rpm yum-utils
RUN yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo
COPY --chown=root:root couchbase.repo /etc/yum.repos.d/
RUN dnf install -y xmlstarlet \ 
                   colordiff \
                   python3 \
                   vim \
                   java-1.8.0-openjdk \
                   maven \
                   git \
                   wget \
                   curl \
                   nc \
                   jq \
                   which \
                   sudo \
                   net-tools \
                   python3-pip \
                   cmake \
                   python3-devel \
                   gcc-c++ \
                   gcc \
                   openssl-devel \
                   make \
                   nfs-utils \
                   packer \
                   zip \
                   ansible \
                   bind-utils \
                   bind \
                   terraform \
                   libcouchbase3 \
                   libcouchbase-devel \
                   libcouchbase3-tools

RUN alternatives --set python /usr/bin/python3

RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install boto boto3 botocore requests dnspython netaddr docutils couchbase netifaces

RUN ansible-galaxy collection install community.aws
RUN ansible-galaxy collection install community.general
RUN ansible-galaxy collection install ansible.netcommon

WORKDIR /var/tmp
RUN curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip
RUN unzip awscliv2.zip
RUN ./aws/install
RUN rm -rf /var/tmp/aws

WORKDIR /
RUN groupadd -g 1001 admin
RUN useradd -u 1001 -g admin admin
RUN usermod -a -G wheel admin
RUN sed -i -e 's/^# %wheel/%wheel/' /etc/sudoers
RUN mkdir /home/admin/.ssh
RUN chown admin:admin /home/admin/.ssh
RUN chmod 700 /home/admin/.ssh

RUN mkdir /var/named/log
RUN chmod 755 /var/named/log
RUN chown -R named:named /var/named
RUN chmod 775 /var/named

COPY named.conf.minimal /etc/named.conf
RUN chown root:named /etc/named.conf
RUN chmod 640 /etc/named.conf

USER admin
WORKDIR /home/admin
RUN ssh-keygen -b 2048 -t rsa -f /home/admin/.ssh/adminkey -q -N ""
RUN mkdir /home/admin/dns
RUN chown admin:admin /home/admin/dns
COPY --chown=admin:admin zone.template /home/admin/dns
COPY --chown=admin:admin in-addr.arpa.template /home/admin/dns
COPY --chown=admin:admin named.conf.template /home/admin/dns
COPY --chown=admin:admin resolv.conf.template /home/admin/dns
COPY --chown=admin:admin run_named.sh /home/admin/dns
COPY --chown=admin:admin createZone.py /home/admin/dns
RUN chmod 755 /home/admin/dns/run_named.sh
RUN chmod 755 /home/admin/dns/createZone.py

RUN git clone https://github.com/mminichino/perf-lab-bin /home/admin/bin
RUN git clone https://github.com/mminichino/terraform-aws-generator-node
RUN git clone https://github.com/mminichino/couchbase-init
RUN git clone https://github.com/mminichino/terraform-aws-couchbase-poc
RUN git clone https://github.com/mminichino/db-host-prep
RUN git clone https://github.com/mminichino/ansible-helper
COPY --chown=admin:admin bashrc /home/admin/.bashrc

CMD exec sudo /home/admin/dns/run_named.sh
