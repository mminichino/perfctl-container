# perfctl-container
Container for creating Couchbase environments.

## Easy Install
You can run a container with all the lab automation utilities preloaded. It has its own isolated DNS server that allows dynamic updates. All that is needed is a system with Docker (that is not running another DNS server).
1. Get control utility
````
$ curl https://github.com/mminichino/perfctl-container/releases/latest/download/run-perfctl.sh -L -O
````
2. Run container
````
$ ./run-perfctl.sh --run
````
3. Login to running container
````
$ ./run-perfctl.sh --shell
````
4. Setup DNS
````
[admin@perfctl:~]$ ./install.sh
 1) ens192: 172.48.5.55
 2) docker0: 172.17.0.1
Interface for DNS zone: 1
server reload successful
````
5. Use provided utilities. You may wish to run ````git pull```` in all the project directories to make sure you have all the latest updates.
````
$ cd terraform-aws-couchbase-poc
$ scripts/load_variables.sh
$ terraform init
$ terraform apply
````
## Cleanup
1. Remove container
````
$ ./run-cbperf.sh --rm
````
2. Remove cached image (i.e. to use newer image)
````
$ ./run-cbperf.sh --rmi
````
