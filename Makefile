.PHONY: download download-districts check-genesis download-genesis-metadata download-genesis transform transform-districts test all

download:
	python3 src/download_data.py

download-districts:
	python3 src/download_district_data.py

check-genesis:
	python3 src/download_genesis.py --check-auth

download-genesis-metadata:
	python3 src/download_genesis.py --metadata-only

download-genesis:
	python3 src/download_genesis.py

transform:
	python3 src/transform_data.py

transform-districts:
	python3 src/build_district_analysis.py

test: transform transform-districts
	python3 -m unittest discover -s tests -v

all: download download-districts test
