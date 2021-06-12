source ../venv/bin/activate
python upload.py -d supplier
sleep 2
python upload.py -d product
sleep 2
python upload.py -d warehouse
sleep 2
python upload.py -d customer
sleep 2
python upload.py -d storage