import os
import sys
import ctypes
import subprocess
from pathlib import Path
from config import NOME_LOG

def super_normalizer(path_str):
    """
    Super Normalizer: Limpa input malformado, expande variáveis, usuário, resolve links simbólicos e normaliza o caminho.
    """
    cleaned = path_str.strip()
    cleaned = cleaned.lstrip('&').strip()  # Remove & no início
    cleaned = cleaned.strip('"').strip("'")  # Remove aspas externas
    # Expandir variáveis de ambiente e ~
    expanded = os.path.expandvars(os.path.expanduser(cleaned))
    # Resolver para caminho absoluto e links
    resolved = Path(expanded).resolve()
    return resolved

def sanitizar_nome_arquivo(nome):
    """
    Remove ou substitui caracteres ilegais para garantir compatibilidade 
    entre NTFS, FAT32 e sistemas Unix.
    """
    # Caracteres proibidos no Windows: <>:"/\|?* e caracteres de controle
    caracteres_invalidos = '<>:"/\\|?*'
    for char in caracteres_invalidos:
        nome = nome.replace(char, "_")
    # Remove caracteres não imprimíveis
    nome = "".join(c for c in nome if c.isprintable())
    return nome.strip()

def gerar_caminho_unico(destino):
    """Garante um caminho único para evitar sobrescritas em sistemas case-insensitive."""
    if not destino.exists():
        return destino
    
    base = destino.parent
    nome = destino.stem
    ext = destino.suffix
    contador = 1
    while (base / f"{nome} ({contador}){ext}").exists():
        contador += 1
    return base / f"{nome} ({contador}){ext}"

def remover_pastas_vazias(diretorio):
    """Remove pastas vazias recursivamente de baixo para cima."""
    for root, dirs, files in os.walk(diretorio, topdown=False):
        for name in dirs:
            caminho_pasta = Path(root) / name
            try:
                caminho_pasta.rmdir()  # Só remove se estiver vazia
            except OSError:
                pass

def _make_file_hidden_if_windows(file_path):
    """Torna um arquivo oculto no Windows se o sistema operacional for Windows."""
    if sys.platform == "win32":
        try:
            # FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(str(file_path), 0x02)
        except Exception:
            pass

def registrar_log(diretorio_base, origem, destino):
    """Registra a movimentação no arquivo de log dentro da pasta base."""
    log_path = diretorio_base / NOME_LOG
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{origem}\t{destino}\n")
        _make_file_hidden_if_windows(log_path)
    except Exception as e:
        print(f"Erro ao registrar log: {e}")

def exibir_progresso(concluido, total, acao="Processando"):
    """Exibe uma barra de progresso simples no terminal com contador e porcentagem."""
    if total == 0:
        return
    percentual = (concluido / total) * 100
    largura_barra = 40
    progresso = int((concluido / total) * largura_barra)
    barra = '█' * progresso + '-' * (largura_barra - progresso)
    sys.stdout.write(f"\r{acao}: |{barra}| {percentual:.1f}% ({concluido}/{total})")
    sys.stdout.flush()
    if concluido == total:
        sys.stdout.write("\n")

def verificar_bibliotecas():
    """
    Verifica se as bibliotecas necessárias estão instaladas. Se não, instala do requirements.txt.
    """
    required = ['os', 'shutil', 'hashlib', 'sys', 'pathlib', 'subprocess']
    missing = []
    for lib in required:
        try:
            __import__(lib)
        except ImportError:
            missing.append(lib)
    
    if missing:
        print(f"Bibliotecas faltando: {missing}. Tentando instalar do requirements.txt...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
            print("Instalação concluída. Verificando novamente...")
            for lib in missing:
                __import__(lib)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao instalar bibliotecas: {e}")
            sys.exit(1)
        except ImportError as e:
            print(f"Biblioteca ainda faltando após instalação: {e}")
            sys.exit(1)
    else:
        print("Todas as bibliotecas necessárias estão presentes.")