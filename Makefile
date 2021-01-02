main:
	python3 setup.py bdist_wheel --universal

dev:
	python3 setup.py install

install:
	pip3 install ./dist/*.whl

upload:
	twine upload dist/*

clean:
	-$(RM) -rf dist
	-git clean -xdf
