main:
	python3 setup.py bdist_wheel --universal

upload:
	twine upload dist/*

clean:
	-$(RM) -rf dist
	-git clean -xdf
