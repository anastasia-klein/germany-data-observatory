.PHONY: download check-genesis download-genesis-metadata download-genesis transform test all

download:
	python3 src/download_data.py

check-genesis:
	python3 src/download_genesis.py --check-auth

download-genesis-metadata:
	python3 src/download_genesis.py --metadata-only

download-genesis:
	python3 src/download_genesis.py

transform:
	python3 src/transform_data.py

test: transform
	python3 -m unittest discover -s tests -v

all: download test
