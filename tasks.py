from invoke import task, call


@task(name="dev-start")
def start_development(c):
    r = c.run("sudo docker ps -f name=dev-mongo", hide=True)
    if 'dev-mongo' not in r.stdout:
        print("Starting mongoDB")
        c.run("sudo mkdir -p /media/ramdisk/mongodb")
        c.run("sudo docker run --name dev-mongo --rm -v /media/ramdisk/mongodb:/data/db -p 27017:27017 -d mongo:4.4.18")
    r = c.run("sudo docker ps -f name=dev-influx", hide=True)
    if 'dev-influx' not in r.stdout:
        print("Starting influxDB")
        c.run("sudo mkdir -p /media/ramdisk/influxdb")
        c.run("sudo docker run --name dev-influx --rm -v /media/ramdisk/influxdb:/var/lib/influxdb -p 8086:8086 -d influxdb:1.8-alpine")
    r = c.run("sudo docker ps -f name=dev-mosquitto", hide=True)
    if 'dev-mosquitto' not in r.stdout:
        print("Starting mosquitto")
        c.run("cp install/mosquitto.conf /media/ramdisk/mosquitto.conf")
        c.run("sudo docker run --name dev-mosquitto --rm -v /media/ramdisk/mosquitto.conf:/mosquitto/config/mosquitto.conf -p 1883:1883 -d eclipse-mosquitto:2.0")
    r = c.run("sudo docker ps -f name=dev-minio", hide=True)
    if 'dev-minio' not in r.stdout:
        print("Starting MinIO")
        c.run("sudo mkdir -p /media/ramdisk/minio")
        c.run('sudo docker run --name dev-minio --rm -v /media/ramdisk/minio:/data -p 9000:9000 --env MINIO_ROOT_USER="brickserver" --env MINIO_ROOT_PASSWORD="password" -d minio/minio:RELEASE.2021-06-17T00-10-46Z server /data')
    c.run("python install/wait_for_influxdb.py")
    c.run("python install/wait_for_mosquitto.py")
    c.run("python install/wait_for_mongodb.py")
    c.run("python install/wait_for_minio.py")


@task(name="dev-stop")
def stop_development(c):
    for name in ['dev-mongo', 'dev-influx', 'dev-mosquitto', 'dev-minio']:
        r = c.run(f"sudo docker ps -f name={name}", hide=True)
        if name in r.stdout:
            print(f"Stopping {name}")
            c.run(f"sudo docker stop {name}")
    print('Removing storage for dev-mongo')
    c.run('sudo rm -rf /media/ramdisk/mongodb')
    print('Removing storage for dev-influx')
    c.run('sudo rm -rf /media/ramdisk/influxdb')
    print('Removing conf for dev-mosquitto')
    c.run('sudo rm -rf /media/ramdisk/mosquitto.conf')
    print('Removing storage for dev-minio')
    c.run('sudo rm -rf /media/ramdisk/minio')


@task(pre=[stop_development], post=[start_development], name="dev-clean")
def cleanup_development(c):
    pass


@task(name="coverage", pre=[start_development], optional=['short', 'long'])
def coverage(c, short=None, long=None):
    scale = 'normal'
    if short:
        scale = 'short'
    if long:
        scale = 'long'
    c.run(f"coverage erase && eval $(python-libfaketime) && TESTSCALE={scale} coverage run --concurrency=multiprocessing -m unittest discover; coverage combine && coverage html && coverage report")


@task(pre=[cleanup_development], post=[coverage], name="clean-coverage")
def cleanup_development_and_run_coverage(c):
    pass


@task(name="deploy")
def testserver_deploy(c):
    c.run("fab -H root@192.168.56.200 deploy")
