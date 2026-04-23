import os
import shutil
import hashlib
from pathlib import Path
from config import TIPOS_ARQUIVOS, NOME_LOG
from utils import (
    registrar_log, 
    exibir_progresso, 
    remover_pastas_vazias, 
    gerar_caminho_unico, 
    sanitizar_nome_arquivo, 
    super_normalizer
)

def calcular_hash(caminho_arquivo):
    hash_md5 = hashlib.md5()
    try:
        with open(caminho_arquivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return None

def detectar_duplicatas(diretorio_origem, filtro_extensoes=None):
    todos_arquivos = []
    for root, dirs, files in os.walk(diretorio_origem):
        for file in files:
            caminho = Path(root) / file
            if filtro_extensoes is None or caminho.suffix.lower() in filtro_extensoes:
                if "Duplicatas" not in caminho.parts:
                    todos_arquivos.append(caminho)
    
    total = len(todos_arquivos)
    hashes = {}
    for i, caminho_arquivo in enumerate(todos_arquivos, 1):
        hash_arquivo = calcular_hash(caminho_arquivo)
        if hash_arquivo:
            if hash_arquivo not in hashes:
                hashes[hash_arquivo] = []
            hashes[hash_arquivo].append(caminho_arquivo)
        exibir_progresso(i, total, "Escaneando")
        
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
        for caminho in paths[1:]:
            nome_sanitizado = sanitizar_nome_arquivo(caminho.name)
            if escolha == "2":
                destino = gerar_caminho_unico(pasta_duplicatas / nome_sanitizado)
                try:
                    shutil.move(str(caminho), str(destino))
                    registrar_log(diretorio_origem, caminho, destino)
                    print(f"Duplicata movida: {caminho} -> {destino}")
                except Exception as e:
                    print(f"Erro ao mover duplicata {caminho}: {e}")
            elif escolha == "3":
                try:
                    os.remove(caminho)
                    print(f"Duplicata apagada: {caminho}")
                except Exception as e:
                    print(f"Erro ao apagar duplicata {caminho}: {e}")
    
    remover_pastas_vazias(diretorio_origem)

def obter_tipo_arquivo(extensao):
    for tipo, extensoes in TIPOS_ARQUIVOS.items():
        if extensao.lower() in extensoes:
            return tipo
    return 'Outros'

def organizar_arquivos(diretorio_origem, filtro_extensoes=None):
    pastas_alvo = set(TIPOS_ARQUIVOS.keys()) | {"Duplicatas", "Outros"}
    arquivos_para_mover = []
    
    for root, dirs, files in os.walk(diretorio_origem):
        rel_path = Path(root).relative_to(diretorio_origem)
        if rel_path.parts and rel_path.parts[0] in pastas_alvo:
            continue
            
        for file in files:
            caminho = Path(root) / file
            if filtro_extensoes is None or caminho.suffix.lower() in filtro_extensoes:
                arquivos_para_mover.append(caminho)

    total = len(arquivos_para_mover)
    for i, caminho_arquivo in enumerate(arquivos_para_mover, 1):
        extensao = caminho_arquivo.suffix
        tipo = obter_tipo_arquivo(extensao)
        pasta_tipo = Path(diretorio_origem) / tipo
        pasta_tipo.mkdir(exist_ok=True)

        nome_sanitizado = sanitizar_nome_arquivo(caminho_arquivo.name)
        destino = gerar_caminho_unico(pasta_tipo / nome_sanitizado)

        try:
            shutil.move(str(caminho_arquivo), str(destino))
            registrar_log(diretorio_origem, caminho_arquivo, destino)
        except Exception:
            pass
        exibir_progresso(i, total, "Movendo")
    
    remover_pastas_vazias(diretorio_origem)

def desfazer_organizacao(caminho_input):
    diretorio = super_normalizer(caminho_input)
    if diretorio.is_file():
        log_path = diretorio
        diretorio_base = log_path.parent
    else:
        log_path = diretorio / NOME_LOG
        diretorio_base = diretorio

    if not log_path.exists():
        print(f"Arquivo de log não encontrado em: {log_path}")
        return

    with open(log_path, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    if not linhas:
        print("O log está vazio.")
        return

    print(f"Restaurando {len(linhas)} arquivos...")
    for i, linha in enumerate(reversed(linhas), 1):
        try:
            origem_str, destino_str = linha.strip().split('\t')
            origem = Path(origem_str)
            destino = Path(destino_str)
            if destino.exists():
                origem.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destino), str(origem))
            else:
                print(f"\nAVISO: Destino '{destino}' não encontrado. Pulando restauração.")
        except Exception as e:
            print(f"\nErro ao restaurar arquivo (linha {i}): {e}")
        finally:
            exibir_progresso(i, len(linhas), "Restaurando")
    remover_pastas_vazias(diretorio_base)
    print("\nRestauração concluída. O arquivo de log foi mantido para segurança.")