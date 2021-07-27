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
    r = c.run("sudo docker ps -f name=dev-rabbitmq", hide=True)
    if 'dev-rabbitmq' not in r.stdout:
        print("Starting RabbitMQ")
        c.run("sudo docker run --rm -d --hostname brickserver --name dev-rabbitmq -v /media/ramdisk/rabbitmq:/var/lib/rabbitmq -p 15672:15672 -p 5672:5672 -e RABBITMQ_VM_MEMORY_HIGH_WATERMARK='0.25' rabbitmq:3.8-management")
    c.run("python install/wait_for_influxdb.py")
    c.run("python install/wait_for_mongodb.py")
    c.run("python install/wait_for_rabbitmq.py")


@task(name="dev-stop")
def stop_development(c):
    for name in ['dev-mongo', 'dev-influx', 'dev-rabbitmq']:
        r = c.run(f"sudo docker ps -f name={name}", hide=True)
        if name in r.stdout:
            print(f"Stopping {name}")
            c.run(f"sudo docker stop {name}")
    print('Removing storage for dev-mongo')
    c.run('sudo rm -rf /media/ramdisk/mongodb')
    print('Removing storage for dev-influx')
    c.run('sudo rm -rf /media/ramdisk/influxdb')
    print('Removing storage for dev-rabbit')
    c.run('sudo rm -rf /media/ramdisk/rabbitmq')


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
