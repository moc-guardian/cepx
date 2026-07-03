from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import cepx

pytestmark = pytest.mark.unit

_LOADER = Path(__file__).resolve().parents[2] / "tools" / "load_cepaberto.py"

# Real CEP Aberto CEP-dump shape: headerless, positional columns
# cep, logradouro, complemento, bairro, cidade_id, estado_id.
_CEP_DUMP = (
    "69900001,Beco Estado do Acre,,Base,7735,1\n"
    '69902992,"Ramal Benfica, s/n",,,7735,1\n'  # quoted comma, empty bairro
    "69900010,Rua Estado do Acre,,Centro,7735,1\n"
)

# Reference dumps:
# cities.csv (cidade_id, nome, estado_id),
# states.csv (estado_id, nome, sigla).
#
# Both headerless.
_CITIES = "7735,Rio Branco,1\n"
_STATES = "1,Acre,AC\n"


@pytest.fixture
def loaded_db(tmp_path, monkeypatch):
    cep_path = tmp_path / "ac.cepaberto_parte_1.csv"
    cep_path.write_text(_CEP_DUMP, encoding="utf-8")
    cities_path = tmp_path / "cities.csv"
    cities_path.write_text(_CITIES, encoding="utf-8")
    states_path = tmp_path / "states.csv"
    states_path.write_text(_STATES, encoding="utf-8")
    db_path = tmp_path / "cepx.sqlite"
    subprocess.run(
        [
            sys.executable,
            str(_LOADER),
            str(cep_path),
            "--cities",
            str(cities_path),
            "--states",
            str(states_path),
            "--out",
            str(db_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    monkeypatch.setenv("CEPX_DB", str(db_path))
    return db_path


def test_cep_resolves_city_and_uf_from_reference_dumps(loaded_db):
    address = cepx.cep("69900001", providers=["local"])
    assert address == cepx.Address(
        cep="69900001",
        state="AC",
        city="Rio Branco",
        neighborhood="Base",
        street="Beco Estado do Acre",
        provider="local",
    )


def test_quoted_embedded_comma_street_is_parsed(loaded_db):
    address = cepx.cep("69902992", providers=["local"])
    assert address.street == "Ramal Benfica, s/n"
    assert address.neighborhood == ""


def test_cep_absent_from_point_dump_is_a_miss(loaded_db):
    with pytest.raises(cepx.CepxError) as info:
        cepx.cep("69900002", providers=["local"])
    assert info.value.errors[0].message == (
        "CEP not found in the local database."
    )
