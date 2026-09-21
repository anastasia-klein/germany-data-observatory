.PHONY: download transform test all

download:
	python3 src/download_data.py

transform:
	python3 src/transform_data.py

test: transform
	python3 -m unittest discover -s tests -v

all: download test

