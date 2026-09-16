.PHONY: validar visor mapas limpiar

validar:
	python3 herramientas/validar.py esquema/ontologia.yaml datos/*.yaml --auditoria

visor:
	cd herramientas && python3 construir_visor.py && mv visor.html ..

mapas:
	python3 herramientas/mapa_predicho.py --datos datos \
		--densidades espacial/densidades-DEMO.csv \
		--parcelas espacial/parcelas-DEMO.csv --contra gradient1 --nulos 2000

limpiar:
	rm -f visor.html; find . -name __pycache__ -type d -exec rm -rf {} +
