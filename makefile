build: clean
	python3 setup.py sdist bdist_wheel

release: build
	twine upload -s dist/*

install:
	python setup.py install