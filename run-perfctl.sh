#!/bin/sh

docker ps >/dev/null 2>&1
if [ $? -ne 0 ]; then
   echo "Can not run docker."
   exit 1
fi

while true; do
  case "$1" in
    --run )
            shift
            docker run -d --network host --name perfctl mminichino/perfctl
            exit
            ;;
    --show )
            shift
            docker ps --filter name=perfctl
            exit
            ;;
    --shell )
            shift
	    for file in $(find $HOME/.ssh/*)
	    do
	      docker cp $file perfctl:/home/admin/.ssh
	    done
            docker exec perfctl sudo chown -R admin:admin /home/admin/.ssh
            docker exec -it perfctl bash
            exit
            ;;
    --log )
            shift
            docker logs -n 25 perfctl
            exit
            ;;
    --tail )
            shift
            docker logs -f perfctl
            exit
            ;;
    --stop )
            shift
            echo -n "Container will stop and DNS service will be interrupted. Continue? [y/n]: "
            read ANSWER
            [ "$ANSWER" = "n" -o "$ANSWER" = "N" ] && exit
            docker stop perfctl
            exit
            ;;
    --start )
            shift
            docker start perfctl
            exit
            ;;
    --rm )
            shift
            echo -n "WARNING: removing the container can not be undone. Continue? [y/n]: "
            read ANSWER
            [ "$ANSWER" = "n" -o "$ANSWER" = "N" ] && exit
            docker stop perfctl
            docker rm perfctl
            exit
            ;;
    --rmi )
            shift
            echo -n "Remove container images? [y/n]: "
            read ANSWER
            [ "$ANSWER" = "n" -o "$ANSWER" = "N" ] && exit
            for image in $(docker images mminichino/perfctl | tail -n +2 | awk '{print $3}'); do docker rmi $image ; done
            exit
            ;;
    * )
            echo "Usage: $0 [ --run | --show | --start | --stop | --shell | --rm ]"
            exit 1
            ;;
  esac
done

