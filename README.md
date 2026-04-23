# Agrupador de Arquivos Inteligente

Este é um utilitário robusto em Python projetado para organizar diretórios bagunçados, classificando arquivos em categorias, detectando duplicatas e oferecendo um sistema de "Desfazer" (Undo) baseado em logs.

## 🚀 Funcionalidades

- **Organização por Categorias**: Move arquivos automaticamente para pastas como `Documentos`, `Imagens`, `Musicas`, `Videos`, `Planilhas`, etc.
- **Detecção de Duplicatas**: Identifica arquivos idênticos através de hash MD5 (conteúdo), permitindo manter, mover ou apagar as cópias.
- **Sistema de Desfazer (Undo)**: Mantém um histórico de movimentação em `agrupador_history.txt`, permitindo restaurar todos os arquivos para suas pastas originais.
- **Compatibilidade entre Sistemas**: Sanitiza nomes de arquivos para garantir que funcionem em NTFS (Windows), FAT32 (Pendrives), ext4 (Linux) e outros.
- **Prevenção de Sobrescrita**: Gera nomes únicos (ex: `foto (1).jpg`) caso arquivos com nomes iguais, mas conteúdos diferentes, colidam na mesma pasta.
- **Limpeza Automática**: Remove pastas que ficaram vazias após a organização ou restauração.

## 🛠️ Pré-requisitos

- **Python 3.6+** instalado.
- Nenhuma biblioteca externa é estritamente necessária (usa apenas bibliotecas padrão), mas o script possui um verificador automático de dependências.

## 📂 Estrutura do Projeto

- `AGRUPADOR.PY`: O script principal de execução.
- `config.py`: Arquivo de configuração onde você pode adicionar novas extensões ou mudar nomes de pastas.
- `test_agrupador.py`: Suite de testes automatizados.
- `.aiconfig`: Regras de contexto para desenvolvimento assistido por IA.

## 📖 Como Usar

1. **Execução**:
   Abra o terminal na pasta do projeto e execute:
   ```bash
   python AGRUPADOR.PY
   ```

2. **Informar o Caminho**:
   O programa solicitará o caminho da pasta. Você pode **digitar o caminho** ou simplesmente **arrastar e soltar a pasta** para dentro do terminal.

3. **Escolher a Operação**:
   - **0 (Tudo)**: Organiza todos os tipos de arquivos suportados.
   - **1 a 5**: Organiza apenas uma categoria específica (ex: apenas Vídeos).
   - **6 (DESFAZER)**: Lê o log da pasta e devolve os arquivos para onde estavam originalmente.

4. **Lidar com Duplicatas**:
   Se o script encontrar arquivos iguais, ele perguntará se você deseja:
   - Manter tudo como está.
   - Mover as cópias para uma pasta chamada `Duplicatas`.
   - Apagar as cópias permanentemente.

5. **Finalização**:
   Ao final, o script perguntará se você deseja desfazer a operação imediatamente. Caso contrário, o log será mantido para restauração futura.

## ⚙️ Customização

Para adicionar novas extensões ou mudar as categorias, edite o arquivo `config.py`:

```python
TIPOS_ARQUIVOS = {
    'Documentos': ['.txt', '.pdf'],
    'Nova_Categoria': ['.ext1', '.ext2'],
    # ...
}
```

## 🧪 Testes

Para garantir que a lógica de movimentação e sanitização está funcionando corretamente no seu sistema, execute os testes:

```bash
python test_agrupador.py
```

## ⚠️ Avisos de Segurança

- O arquivo `agrupador_history.txt` é ocultado no Windows. Não o apague se desejar manter a capacidade de desfazer a organização.
- O script utiliza `shutil.move`, que é seguro para movimentação entre diferentes discos/partições.

---
*Desenvolvido para garantir produtividade e integridade de dados.*