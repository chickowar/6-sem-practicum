Initial commit

TODO: 
1) setup kafka, 
2) setup postgreSQL, 
3) initialize the simplest api -> kafka -> orchestrator connection
4) make orchestrartor write to postgreSQL
5) make api read from postgreSQL

## don't forget
* make scripts in docker compose to create topics with preferably a configurable amount of partitions
* **OR** do it using python (confluent_kafka) 

(i think first is better)