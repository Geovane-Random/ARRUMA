import sys
from pathlib import Path
from config import TIPOS_ARQUIVOS
from utils import verificar_bibliotecas, super_normalizer
from core import (
    detectar_duplicatas, 
    lidar_com_duplicatas, 
    organizar_arquivos, 
    desfazer_organizacao
)

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