.PHONY: up down 
.PHONY: setup run configure
.PHONY: stop remove teardown 

n?=1

up: setup run configure
down: stop remove teardown

run: member=rmq2
run: rmq1 rmq2 connect1 connect2 cluster1 

stop: stop1 stop2

remove: remove1 remove2

start%:
	docker start rmq$*

restart%:
	docker restart rmq$*

shutdown%:
	docker stop rmq$*

setup:
	-docker network create rmq

teardown:
	-docker network remove rmq

rmq%:
	docker run -d --name rmq$* -it -h rmq$* \
	-v `pwd`/conf/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf \
	-v `pwd`/conf/advanced.config:/etc/rabbitmq/advanced.config \
  	-v `pwd`/conf/enabled_plugins:/etc/rabbitmq/enabled_plugins \
  	-e RABBITMQ_ERLANG_COOKIE=rabbit \
  	-p 567$$(( ($*) + 1 )):5672 \
  	-p 1567$$(( ($*) + 1 )):15672 \
  	rabbitmq:3.7.15-management

connect%:
	docker network connect rmq rmq$*

disconnect%:
	docker network disconnect rmq rmq$*

cluster%:
	docker exec rmq$* rabbitmqctl stop_app
	docker exec rmq$* rabbitmqctl join_cluster rabbit@$(member)
	docker exec rmq$* rabbitmqctl start_app
	docker exec rmq$* rabbitmqctl cluster_status

cluster_status%:
	docker exec rmq$* rabbitmqctl cluster_status

configure:
	docker exec rmq1 rabbitmqctl set_policy ha_gotchas \
		"^haq" '{"ha-mode":"exactly", "ha-params":2, "ha-sync-mode":"automatic", "ha-sync-batch-size":2}'

ctl%:
	docker exec -it rmq$* rabbitmqctl $(cmd)

stop%:
	-docker stop rmq$*

remove%:
	-docker rm -f rmq$*

logs%:
	docker logs -f rmq$*