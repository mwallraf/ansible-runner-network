FROM quay.io/ansible/ansible-runner:latest

COPY ./requirements.* /tmp

COPY ./ansible_plugins /home/runner/.ansible/plugins

RUN pip install -r /tmp/requirements.txt \
    && ansible-galaxy install -r /tmp/requirements.yml \
    && rm /tmp/requirements.*
