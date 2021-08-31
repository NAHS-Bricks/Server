from invoke import task


@task(name="dev-start")
def start_development(c):
    r = c.run("sudo docker ps -f name=dev-mongo", hide=True)
    if 'dev-mongo' not in r.stdout:
        print("Starting mongoDB")
        c.run("sudo docker run --name dev-mongo --rm -v /media/ramdisk/mongodb:/data/db -p 27017:27017 -d mongo:4.4")
    r = c.run("sudo docker ps -f name=dev-influx", hide=True)
    if 'dev-influx' not in r.stdout:
        print("Starting influxDB")
        c.run("sudo docker run --name dev-influx --rm -v /media/ramdisk/influxdb:/var/lib/influxdb -p 8086:8086 -d influxdb:1.8-alpine")
    r = c.run("sudo docker ps -f name=dev-mosquitto", hide=True)
    if 'dev-mosquitto' not in r.stdout:
        print("Starting mosquitto")
        c.run("cp install/mosquitto.conf /media/ramdisk/mosquitto.conf")
        c.run("sudo docker run --name dev-mosquitto --rm -v /media/ramdisk/mosquitto.conf:/mosquitto/config/mosquitto.conf -p 1883:1883 -p 9001:9001 -d eclipse-mosquitto:2.0")
    c.run("python install/wait_for_influxdb.py")
    c.run("python install/wait_for_mosquitto.py")
    c.run("python install/wait_for_mongodb.py")


@task(name="dev-stop")
def stop_development(c):
    for name in ['dev-mongo', 'dev-influx', 'dev-mosquitto']:
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


@task(pre=[stop_development], post=[start_development], name="dev-clean")
def cleanup_development(c):
    pass


@task(name="coverage", pre=[start_development])
def coverage(c):
    c.run("coverage erase && eval $(python-libfaketime) && coverage run -m unittest discover && coverage html && coverage report")


@task(pre=[cleanup_development], post=[coverage], name="clean-coverage")
def cleanup_development_and_run_coverage(c):
    pass


@task(name="deploy")
def testserver_deploy(c):
    c.run("fab -H root@192.168.56.200 deploy")
