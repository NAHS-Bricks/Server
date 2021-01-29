from fabric import task
import patchwork.transfers
import os

apt_update_run = False
project_dir = "/opt/middleware/nahs/brickserver"
storagedir_mongo = "/var/data/mongodb"
storagedir_influx = "/var/data/influxdb"
mongodb_image = 'mongo:4.4'
influxdb_image = 'influxdb:1.8-alpine'


def docker_pull(c, image):
    print(f"Preloading docker image {image}")
    c.run(f"docker pull {image}")


def systemctl_stop(c, service):
    if c.run(f"systemctl is-active {service}", warn=True, hide=True).ok:
        print(f"Stop Service {service}")
        c.run(f"systemctl stop {service}", hide=True)


def systemctl_start(c, service):
    if not c.run(f"systemctl is-enabled {service}", warn=True, hide=True).ok:
        print(f"Enable Service {service}")
        c.run(f"systemctl enable {service}", hide=True)
    if c.run(f"systemctl is-active {service}", warn=True, hide=True).ok:
        print(f"Restart Service {service}")
        c.run(f"systemctl restart {service}", hide=True)
    else:
        print(f"Start Service {service}")
        c.run(f"systemctl start {service}", hide=True)


def systemctl_install_service(c, local_file, remote_file, replace_macros):
    print(f"Installing Service {remote_file}")
    c.put(os.path.join('install', local_file), remote=os.path.join('/etc/systemd/system', remote_file))
    for macro, value in replace_macros:
        c.run("sed -i -e 's/" + macro + "/" + value.replace('/', '\/') + "/g' " + os.path.join('/etc/systemd/system', remote_file))


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


def setup_virtualenv(c):
    print("Setup virtualenv for brickserver")
    c.run(f"virtualenv -p /usr/bin/python3 {os.path.join(project_dir, 'venv')}")
    print("Installing python requirements for brickserver")
    c.run(f"{os.path.join(project_dir, 'venv/bin/pip')} install -r {os.path.join(project_dir, 'requirements.txt')}")


def upload_project_files(c):
    for f in ["brickserver.py", "requirements.txt"]:
        print(f"Uploading {f}")
        c.put(f, remote=os.path.join(project_dir, f))
    for d in ["helpers"]:
        print(f"Uploading {d}")
        patchwork.transfers.rsync(c, d, project_dir, exclude=['*.pyc', '*__pycache__'])


def create_directorys(c):
    for d in [project_dir, storagedir_mongo, storagedir_influx]:
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


@task
def deploy(c):
    c.run('hostname')
    c.run('uname -a')
    systemctl_stop(c, 'cron')
    systemctl_stop(c, 'brickserver')
    systemctl_stop(c, 'docker.mongodb.service')
    systemctl_stop(c, 'docker.influxdb.service')
    install_apt_package(c, 'curl')
    install_docker(c)
    install_apt_package(c, 'python3')
    install_apt_package(c, 'virtualenv')
    install_apt_package(c, 'systemd-docker')
    create_directorys(c)
    upload_project_files(c)
    setup_virtualenv(c)
    systemctl_install_service(c, 'brickserver.service', 'brickserver.service', [('__project_dir__', project_dir)])
    systemctl_install_service(c, 'docker.service', 'docker.mongodb.service', [('__storage__', storagedir_mongo + ':/data/db'), ('__port__', '27017:27017'), ('__image__', mongodb_image)])
    systemctl_install_service(c, 'docker.service', 'docker.influxdb.service', [('__storage__', storagedir_influx + ':/var/lib/influxdb'), ('__port__', '8086:8086'), ('__image__', influxdb_image)])
    c.run("systemctl daemon-reload")
    install_rsyslog(c)
    install_cron(c)
    install_logrotate(c)
    systemctl_start(c, 'docker')
    docker_pull(c, mongodb_image)
    docker_pull(c, influxdb_image)
    systemctl_start(c, 'docker.mongodb.service')
    systemctl_start(c, 'docker.influxdb.service')
    systemctl_start(c, 'brickserver')
    systemctl_start(c, 'cron')