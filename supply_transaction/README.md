docker exec -i container_id bash -c "cd dummy_data && ./upload.sh"
docker exec container_id curl -X GET http://localhost:5000/supplytransactions
