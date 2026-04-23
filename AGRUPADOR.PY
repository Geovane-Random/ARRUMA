import os
import shutil
import hashlib
import ctypes # Para tornar o arquivo oculto no Windows
import sys
import subprocess
from pathlib import Path
from config import TIPOS_ARQUIVOS, NOME_LOG


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
            # Falha silenciosamente se não conseguir definir o atributo (ex: permissão)
            pass

def registrar_log(diretorio_base, origem, destino):
    """Registra a movimentação no arquivo de log dentro da pasta base."""
    log_path = diretorio_base / NOME_LOG
    # Usamos TAB (\t) como separador, pois é proibido em caminhos na maioria dos sistemas
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{origem}\t{destino}\n")
        _make_file_hidden_if_windows(log_path) # Torna o log oculto após escrever
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
    for lib in required: # ctypes é padrão, não precisa ser verificado explicitamente aqui
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

def detectar_duplicatas(diretorio_origem, filtro_extensoes=None):
    todos_arquivos = []
    for root, dirs, files in os.walk(diretorio_origem):
        for file in files:
            caminho = Path(root) / file
            # Se houver filtro, verifica se a extensão do arquivo está na lista permitida
            if filtro_extensoes is None or caminho.suffix.lower() in filtro_extensoes:
                if "Duplicatas" not in caminho.parts: # Evita re-escanear pasta de duplicatas
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
        manter = paths[0]  # Manter o primeiro
        for caminho in paths[1:]:
            nome_sanitizado = sanitizar_nome_arquivo(caminho.name)
            if escolha == "2":
                # Garante nome único para evitar conflitos de nomes iguais em pastas diferentes
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
            # Para escolha 1, não faz nada
    
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
        # Evita re-processar arquivos já organizados em pastas de destino
        rel_path = Path(root).relative_to(diretorio_origem)
        if rel_path.parts and rel_path.parts[0] in pastas_alvo:
            continue
            
        for file in files:
            caminho = Path(root) / file
            # Aplica o filtro de extensões na organização também
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
    """Lê o log e devolve os arquivos para as pastas originais."""
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

    # Limpa as pastas de categoria (Ex: Documentos, Imagens) que ficaram vazias após o undo
    remover_pastas_vazias(diretorio_base)

    print("\nRestauração concluída. O arquivo de log foi mantido para segurança.")

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

    # Categorias disponíveis (exceto 'Outros' que é o fallback automático)
    categorias = [k for k in TIPOS_ARQUIVOS.keys() if k != 'Outros']
    
    print("\nO que você deseja organizar?")
    print("0. Tudo (Todas as categorias)")
    for i, cat in enumerate(categorias, 1):
        print(f"{i}. apenas {cat}")
    
    opcao_desfazer = len(categorias) + 1
    print(f"{opcao_desfazer}. DESFAZER (Restaurar arquivos para origem)")
    
    opcao = input(f"Escolha uma opção (0-{opcao_desfazer}): ").strip()
    
    if opcao == str(opcao_desfazer):
        desfazer_organizacao(str(diretorio_origem))
        return

    filtro = None
    try:
        idx = int(opcao)
        if 0 < idx <= len(categorias):
            filtro = TIPOS_ARQUIVOS[categorias[idx-1]]
    except (ValueError, IndexError):
        filtro = None # Default para 'Tudo'

    print(f"\nDetectando duplicatas em {diretorio_origem}...")
    duplicatas = detectar_duplicatas(diretorio_origem, filtro)
    lidar_com_duplicatas(duplicatas, diretorio_origem)

    print(f"\nOrganizando arquivos em {diretorio_origem}...")
    organizar_arquivos(diretorio_origem, filtro)
    print("Organização concluída!")

    # Pergunta se o usuário deseja desfazer a operação imediatamente
    reverter = input("\nDeseja desfazer a organização e retornar os arquivos para o estado original agora? (s/n): ").strip().lower()
    if reverter == 's':
        desfazer_organizacao(str(diretorio_origem))

if __name__ == "__main__":
    main()