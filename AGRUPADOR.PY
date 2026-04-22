import os
import shutil
import hashlib
import sys
import subprocess
from pathlib import Path

# Dicionário de tipos de arquivo
tipos = {
    'Textos': ['.txt', '.doc', '.docx', '.pdf', '.rtf'],
    'Imagens': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'],
    'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
    'Audios': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
    'Arquivos_Comprimidos': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Executaveis': ['.exe', '.msi', '.bat', '.sh'],
    'Outros': []
}

def super_normalizer(path_str):
    """
    Super Normalizer: Limpa input malformado, expande variáveis, usuário, resolve links simbólicos e normaliza o caminho.
    """
    # Limpar input: remover prefixos comuns de comandos PowerShell/CMD e aspas
    cleaned = path_str.strip()
    cleaned = cleaned.lstrip('&').strip()  # Remove & no início
    cleaned = cleaned.strip('"').strip("'")  # Remove aspas externas
    # Expandir variáveis de ambiente e ~
    expanded = os.path.expandvars(os.path.expanduser(cleaned))
    # Resolver para caminho absoluto e links
    resolved = Path(expanded).resolve()
    return resolved

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
            # Verificar novamente após instalação
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

def calcular_hash(caminho_arquivo):
    hash_md5 = hashlib.md5()
    try:
        with open(caminho_arquivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def detectar_duplicatas(diretorio_origem):
    hashes = {}
    for root, dirs, files in os.walk(diretorio_origem):
        for file in files:
            caminho_arquivo = Path(root) / file
            hash_arquivo = calcular_hash(caminho_arquivo)
            if hash_arquivo:
                if hash_arquivo not in hashes:
                    hashes[hash_arquivo] = []
                hashes[hash_arquivo].append(caminho_arquivo)
    duplicatas = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    return duplicatas

def lidar_com_duplicatas(duplicatas, diretorio_origem):
    if not duplicatas:
        print("Nenhuma duplicata encontrada.")
        return

    print(f"Encontradas {len(duplicatas)} grupos de duplicatas.")
    escolha = input("O que fazer com as duplicatas? (1) Manter todas, (2) Mover duplicatas para pasta 'Duplicatas', (3) Apagar duplicatas (manter apenas uma): ").strip()

    pasta_duplicatas = Path(diretorio_origem) / "Duplicatas"
    if escolha == "2":
        pasta_duplicatas.mkdir(exist_ok=True)

    for hash_val, paths in duplicatas.items():
        manter = paths[0]  # Manter o primeiro
        for caminho in paths[1:]:
            if escolha == "2":
                destino = pasta_duplicatas / caminho.name
                try:
                    shutil.move(str(caminho), str(destino))
                    print(f"Duplicata movida: {caminho} -> {destino}")
                except Exception as e:
                    print(f"Erro ao mover duplicata {caminho}: {e}")
            elif escolha == "3":
                try:
                    os.remove(caminho)
                    print(f"Duplicata apagada: {caminho}")
                except Exception as e:
                    print(f"Erro ao apagar duplicata {caminho}: {e}")
            # Para escolha 1, não faz nada

def obter_tipo_arquivo(extensao):
    for tipo, extensoes in tipos.items():
        if extensao.lower() in extensoes:
            return tipo
    return 'Outros'

def organizar_arquivos(diretorio_origem):
    for root, dirs, files in os.walk(diretorio_origem):
        for file in files:
            caminho_arquivo = Path(root) / file
            extensao = caminho_arquivo.suffix
            tipo = obter_tipo_arquivo(extensao)

            # Criar pasta do tipo se não existir
            pasta_tipo = Path(diretorio_origem) / tipo
            pasta_tipo.mkdir(exist_ok=True)

            # Mover arquivo
            destino = pasta_tipo / file
            try:
                shutil.move(str(caminho_arquivo), str(destino))
                print(f"Movido: {caminho_arquivo} -> {destino}")
            except Exception as e:
                print(f"Erro ao mover {caminho_arquivo}: {e}")

def main():
    print("Verificando bibliotecas necessárias...")
    verificar_bibliotecas()
    print("Organizador de Arquivos por Tipo com Tratamento de Duplicatas")
    if len(sys.argv) > 1:
        caminho_input = sys.argv[1]
    else:
        caminho_input = input("Digite ou arraste o caminho da pasta para escanear: ").strip()

    # Usar Super Normalizer
    try:
        diretorio_origem = super_normalizer(caminho_input)
        print(f"Caminho normalizado: {diretorio_origem}")
    except Exception as e:
        print(f"Erro ao normalizar caminho: {e}")
        return

    if not diretorio_origem.exists() or not diretorio_origem.is_dir():
        print(f"Caminho inválido ou não é um diretório: {diretorio_origem}")
        return

    print(f"Detectando duplicatas em {diretorio_origem}...")
    duplicatas = detectar_duplicatas(diretorio_origem)
    lidar_com_duplicatas(duplicatas, diretorio_origem)

    print(f"Organizando arquivos em {diretorio_origem}...")
    organizar_arquivos(diretorio_origem)
    print("Organização concluída!")

if __name__ == "__main__":
    main()