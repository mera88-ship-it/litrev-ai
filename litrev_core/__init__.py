"""
litrev_core — Librería común de LITREV-AI.

Centraliza lo que antes estaba repetido y divergente en cada script:
rutas, logging, encoding de Windows, clientes de API, IO atómico, el
motor de prioridad y el registro de estado. Los scripts de cada fase
son finos: orquestan estas piezas.

Cambiar de tema NUNCA requiere tocar esta librería; solo config/*.yaml.
"""

__version__ = "3.0"
