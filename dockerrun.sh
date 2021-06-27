if [ $1 = "up" ]
then
    if [ $2 = "--build" ]
    then
        docker-compose -f customer_transaction/docker-compose.yml up --build -d
        docker-compose -f supply_transaction/docker-compose.yml up --build -d
        docker-compose -f inventory/docker-compose.yml up --build -d
    else
        docker-compose -f customer_transaction/docker-compose.yml up -d
        docker-compose -f supply_transaction/docker-compose.yml up -d
        docker-compose -f inventory/docker-compose.yml up -d
    fi
elif [ $1 = "down" ]
then
    docker-compose -f customer_transaction/docker-compose.yml down
    docker-compose -f supply_transaction/docker-compose.yml down
    docker-compose -f inventory/docker-compose.yml down
else
    echo "The argument" $1 "is not recognized"
fi