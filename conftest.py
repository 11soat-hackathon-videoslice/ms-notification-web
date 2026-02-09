import sys
from pathlib import Path

# Adicionar o diretório src ao PYTHONPATH para permitir importações
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Adicionar o diretório do video-slice-core ao PYTHONPATH
core_src_path = Path(__file__).parent.parent / "video-slice-core" / "src"
if core_src_path.exists():
    sys.path.insert(0, str(core_src_path))

