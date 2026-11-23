"""Configuração lida do ambiente (.env na raiz do repositório)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent

# Todas as conexões abrem no fuso de Brasília: a data de um evento é a data
# em que ele aconteceu para quem usa a plataforma.
FUSO = "-c timezone=America/Sao_Paulo"


@dataclass(frozen=True)
class Config:
    plataforma_url: str  # produção da plataforma: Neon, schema inova
    staging_url: str  # réplica local (container), isolada da produção
    dw_url: str  # warehouse: mesmo Neon, schema dw
    lake: Path  # raiz das camadas de arquivo (bronze, silver, gold)


def carregar() -> Config:
    load_dotenv(RAIZ / ".env")
    plataforma = os.environ.get("PLATAFORMA_URL", "")
    return Config(
        plataforma_url=plataforma,
        staging_url=os.environ.get("STAGING_URL", ""),
        dw_url=os.environ.get("DW_NEON_URL", "") or plataforma,
        lake=Path(os.environ.get("LAKE_DIR", str(RAIZ / "lake"))),
    )
