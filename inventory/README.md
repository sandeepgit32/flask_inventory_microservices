https://stackoverflow.com/questions/61983525/pytest-runtimeerror-no-application-found-either-work-inside-a-view-function-or

docker exec -i container_id bash -c "cd dummy_data && ./upload.sh"
docker exec container_id curl -X GET http://localhost:5000/customertransactions