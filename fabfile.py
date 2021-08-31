from fabric import task
import patchwork.transfers
import os
import subprocess
import time
from datetime import datetime

apt_update_run = False
project_dir = "/opt/middleware/nahs/brickserver"
backup_dir = "/var/backup"
storagedir_mongo = "/var/data/mongodb"
storagedir_influx = "/var/data/influxdb"
storagedir_mosquitto = "/var/data/mosquitto"
mongodb_image = 'mongo:4.4'
influxdb_image = 'influxdb:1.8'
mosquitto_image = 'eclipse-mosquitto:2.0'
mongodb_service = "docker.mongodb.service"
influxdb_service = 'docker.influxdb.service'
mosquitto_service = 'docker.mosquitto.service'


def docker_pull(c, image):
    print(f"Preloading docker image {image}")
    c.run(f"docker pull {image}")


def docker_prune(c):
    print("Removing all outdated docker images")
    c.run("docker image prune -f")


def systemctl_stop(c, service):
    if c.run(f"systemctl is-active {service}", warn=True, hide=True).ok:
        print(f"Stop Service {service}", flush=True)
        c.run(f"systemctl stop {service}", hide=True)


def systemctl_start(c, service):
    if not c.run(f"systemctl is-enabled {service}", warn=True, hide=True).ok:
        print(f"Enable Service {service}", flush=True)
        c.run(f"systemctl enable {service}", hide=True)
    if c.run(f"systemctl is-active {service}", warn=True, hide=True).ok:
        print(f"Restart Service {service}", flush=True)
        c.run(f"systemctl restart {service}", hide=True)
    else:
        print(f"Start Service {service}", flush=True)
        c.run(f"systemctl start {service}", hide=True)


def systemctl_start_docker(c):
    if not c.run(f"systemctl is-enabled docker", warn=True, hide=True).ok:
        print(f"Enable Service docker", flush=True)
        c.run(f"systemctl enable docker", hide=True)
    if c.run(f"systemctl is-active docker", warn=True, hide=True).ok:
        print(f"Service docker allready running", flush=True)
    else:
        print(f"Start Service docker", flush=True)
        c.run(f"systemctl start docker", hide=True)


def systemctl_install_service(c, local_file, remote_file, replace_macros):
    print(f"Installing Service {remote_file}", flush=True)
    c.put(os.path.join('install', local_file), remote=os.path.join('/etc/systemd/system', remote_file))
    for macro, value in replace_macros:
        c.run("sed -i -e 's/" + macro + "/" + value.replace('/', '\/') + "/g' " + os.path.join('/etc/systemd/system', remote_file))


def drop_event_system(c):
    rabbitmq_service = 'docker.rabbitmq.service'
    storagedir_rabbitmq = "/var/data/rabbitmq"
    rabbitmq_image = 'rabbitmq:3.8'
    systemctl_stop(c, rabbitmq_service)
    c.run(f"rm -f {os.path.join('/etc/systemd/system', rabbitmq_service)}", warn=True, hide=True)
    c.run(f"rm -rf {storagedir_rabbitmq}", warn=True, hide=True)
    c.run(f"docker rmi {rabbitmq_image}", warn=True, hide=True)
    c.run(f"rm -rf {os.path.join(project_dir, 'event')}", warn=True, hide=True)


def install_rsyslog(c):
    print("Configuring rsyslog for BrickServer")
    c.put("install/rsyslog.conf", "/etc/rsyslog.d/brickserver.conf")
    systemctl_start(c, 'rsyslog')


def install_cron(c):
    print("Configuring cron for BrickServer")
    c.put("install/cron", "/etc/cron.d/brickserver")
    c.run("chmod 644 /etc/cron.d/brickserver")


def install_logrotate(c):
    print("Configuring logrotate for BrickServer")
    c.put("install/logrotate", "/etc/logrotate.d/brickserver")
    c.run("chmod 644 /etc/logrotate.d/brickserver")


def execute_migrations(c):
    print("Executing BrickServer migrations")
    binary = 'venv/bin/python'
    executeable = 'brickserver.py'
    c.run(f'cd {project_dir}; {binary} {executeable} -m')


def setup_virtualenv(c):
    print("Setup virtualenv for brickserver")
    c.run(f"virtualenv -p /usr/bin/python3 {os.path.join(project_dir, 'venv')}")
    print("Installing python requirements for brickserver")
    c.run(f"{os.path.join(project_dir, 'venv/bin/pip')} install -r {os.path.join(project_dir, 'requirements.txt')}")


def write_brickserver_version(c):
    print("Writing BrickServer version")
    version_file = os.path.join(project_dir, 'helpers', 'current_version.py')
    version = subprocess.check_output('git describe', shell=True).decode('UTF-8').strip().split('-', 1)[0].replace('v', '')
    current_version = f"current_brickserver_version = '{version}'"
    c.run(f'echo "{current_version}" > {version_file}')


def upload_deploy_helpers(c):
    print("Creating deploy helpers")
    c.run("mkdir -p /tmp/brickserver-deploy")
    c.put("install/wait_for_mongodb.py", remote=os.path.join("/tmp/brickserver-deploy", "wait_for_mongodb.py"))
    c.put("install/wait_for_influxdb.py", remote=os.path.join("/tmp/brickserver-deploy", "wait_for_influxdb.py"))
    c.put("install/wait_for_mosquitto.py", remote=os.path.join("/tmp/brickserver-deploy", "wait_for_mosquitto.py"))


def cleanup_deploy_helpers(c):
    print("Removing deploy helpers")
    c.run("rm -rf /tmp/brickserver-deploy")


def upload_project_files(c):
    for f in ["brickserver.py", "requirements.txt", "bat_prediction_reference.dat"]:
        print(f"Uploading {f}")
        c.put(f, remote=os.path.join(project_dir, f))
    print(f"Uploading mosquitto.conf")
    c.put('install/mosquitto.conf', remote=os.path.join(storagedir_mosquitto, 'mosquitto.conf'))
    for d in ["helpers", "connector", "stage"]:
        print(f"Uploading {d}")
        patchwork.transfers.rsync(c, d, project_dir, exclude=['*.pyc', '*__pycache__'], delete=True)


def create_directorys(c):
    for d in [project_dir, storagedir_mongo, storagedir_influx, storagedir_mosquitto, backup_dir]:
        print(f"Creating {d}")
        c.run(f"mkdir -p {d}", warn=True, hide=True)


def install_apt_package(c, package):
    global apt_update_run
    if not c.run(f"dpkg -s {package}", warn=True, hide=True).ok:
        if not apt_update_run:
            print('Running apt update')
            c.run('apt update', hide=True)
            apt_update_run = True
        print(f"Installing {package}")
        c.run(f"apt install -y {package}")
    else:
        print(f"{package} allready installed")


def install_docker(c):
    if not c.run('which docker', warn=True, hide=True).ok:
        print('Install Docker')
        c.run('curl -fsSL https://get.docker.com | sh')
    else:
        print('Docker allready installed')


def wait_for_mongodb(c):
    print("Waiting for MongoDB to be started")
    c.run(f"cd {project_dir}; {os.path.join(project_dir, 'venv/bin/python3')} /tmp/brickserver-deploy/wait_for_mongodb.py")


def wait_for_influxdb(c):
    print("Waiting for InfluxDB to be started")
    c.run(f"cd {project_dir}; {os.path.join(project_dir, 'venv/bin/python3')} /tmp/brickserver-deploy/wait_for_influxdb.py")


def wait_for_mosquitto(c):
    print("Waiting for mosquitto to be started")
    c.run(f"cd {project_dir}; {os.path.join(project_dir, 'venv/bin/python3')} /tmp/brickserver-deploy/wait_for_mosquitto.py")


def backup_mongodb(c):
    if c.run(f"systemctl is-active {mongodb_service}", warn=True, hide=True).ok:
        backup_path = os.path.join(backup_dir, 'mongodb-' + datetime.now().isoformat() + '.tar.gz')
        print(f"Creating backup: {backup_path}", flush=True)
        c.run(f'docker exec -t {mongodb_service} /bin/sh -c "mongodump --forceTableScan -o /backup; tar cfz /backup.tar.gz /backup; rm -rf /backup"', hide=True)
        c.run(f'docker cp {mongodb_service}:/backup.tar.gz {backup_path}', hide=True)


def backup_influxdb(c):
    if c.run(f"systemctl is-active {influxdb_service}", warn=True, hide=True).ok:
        backup_path = os.path.join(backup_dir, 'influxdb-' + datetime.now().isoformat() + '.tar.gz')
        print(f"Creating backup: {backup_path}", flush=True)
        c.run(f'docker exec -t {influxdb_service} /bin/sh -c "influxd backup -portable /backup; tar cfz /backup.tar.gz /backup; rm -rf /backup"', hide=True)
        c.run(f'docker cp {influxdb_service}:/backup.tar.gz {backup_path}', hide=True)


@task
def deploy(c):
    c.run('hostname')
    c.run('uname -a')
    install_apt_package(c, 'curl')
    install_apt_package(c, 'rsync')
    install_docker(c)
    install_apt_package(c, 'python3')
    install_apt_package(c, 'virtualenv')
    systemctl_start_docker(c)
    docker_pull(c, mongodb_image)
    docker_pull(c, influxdb_image)
    docker_pull(c, mosquitto_image)
    upload_deploy_helpers(c)
    # Timecritical stuff (when service allready runs) - start
    create_directorys(c)
    systemctl_stop(c, 'cron')
    systemctl_stop(c, 'brickserver')
    backup_influxdb(c)
    backup_mongodb(c)
    systemctl_stop(c, mongodb_service)
    systemctl_stop(c, influxdb_service)
    systemctl_stop(c, mosquitto_service)
    drop_event_system(c)
    upload_project_files(c)
    write_brickserver_version(c)
    setup_virtualenv(c)
    systemctl_install_service(c, 'brickserver.service', 'brickserver.service', [('__project_dir__', project_dir)])
    systemctl_install_service(c, 'docker.service', mongodb_service, [('__additional__', ''), ('__storage__', storagedir_mongo + ':/data/db'), ('__port__', '27017:27017'), ('__image__', mongodb_image)])
    systemctl_install_service(c, 'docker.service', influxdb_service, [('__additional__', ''), ('__storage__', storagedir_influx + ':/var/lib/influxdb'), ('__port__', '8086:8086'), ('__image__', influxdb_image)])
    systemctl_install_service(c, 'docker.service', mosquitto_service, [('__additional__', ''), ('__storage__', os.path.join(storagedir_mosquitto, 'mosquitto.conf') + ':/mosquitto/config/mosquitto.conf'), ('__port__', '1883:1883'), ('__image__', mosquitto_image)])
    c.run("systemctl daemon-reload")
    install_rsyslog(c)
    install_cron(c)
    install_logrotate(c)
    systemctl_start(c, mongodb_service)
    systemctl_start(c, influxdb_service)
    systemctl_start(c, mosquitto_service)
    wait_for_mongodb(c)
    wait_for_influxdb(c)
    wait_for_mosquitto(c)
    execute_migrations(c)
    systemctl_start(c, 'brickserver')
    systemctl_start(c, 'cron')
    # Timecritical stuff (when service allready runs) - end
    cleanup_deploy_helpers(c)
    docker_prune(c)
