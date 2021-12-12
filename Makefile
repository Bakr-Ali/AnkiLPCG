.PHONY: all docs forms zip addon clean

all: docs forms zip
docs:
	$(MAKE) -C docs html
forms: src/import_dialog.py
zip: ARLPCG.ankiaddon

src/import_dialog.py: designer/import_dialog.ui 
	pyuic5 $^ > $@

ARLPCG.ankiaddon: $(shell find src/ -type f)
	rm -f $@
	rm -f src/meta.json
	rm -rf src/__pycache__
	( cd src/; zip -r ../$@ * )

# install in test profile
install: zip
	unzip -o ARLPCG.ankiaddon -d ankiprofile/addons21/1642554134

clean:
	make -C docs clean
	rm -f *.pyc
	rm -f src/*.pyc
	rm -f src/__pycache__
	rm -f src/import_dialog.py
	rm -f ARLPCG.ankiaddon
