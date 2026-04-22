import os
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import io

# Importa as funções do script original para teste unitário
try:
    from AGRUPADOR import (
        super_normalizer, 
        _make_file_hidden_if_windows,
        registrar_log,
        exibir_progresso,
        verificar_bibliotecas,
        calcular_hash, 
        detectar_duplicatas, 
        lidar_com_duplicatas,
        obter_tipo_arquivo, 
        organizar_arquivos,
        desfazer_organizacao,
    )
    from config import TIPOS_ARQUIVOS as tipos
except ImportError:
    print("Erro: Não foi possível importar os módulos necessários. Verifique AGRUPADOR.PY e config.py.")
    sys.exit(1)

class TestAgrupador(unittest.TestCase):
    def setUp(self):
        """Configura um diretório de teste temporário antes de cada teste."""
        self.test_dir = Path("test_sandbox").resolve()
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar arquivos de teste para simular um ambiente real
        (self.test_dir / "documento1.txt").write_text("conteúdo de teste A")
        (self.test_dir / "documento2.txt").write_text("conteúdo de teste A")  # Duplicata de conteúdo
        (self.test_dir / "imagem.jpg").write_text("dados binários fictícios de imagem")
        (self.test_dir / "video.mp4").write_text("dados binários fictícios de vídeo")
        (self.test_dir / "musica.mp3").write_text("dados binários fictícios de audio")
        (self.test_dir / "desconhecido.xyz").write_text("extensão não mapeada")

    def tearDown(self):
        """Remove o diretório de teste após a execução dos testes."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_obter_tipo_arquivo(self):
        """Verifica se a classificação por extensão está correta de acordo com o dicionário 'tipos'."""
        self.assertEqual(obter_tipo_arquivo(".txt"), "Documentos")
        self.assertEqual(obter_tipo_arquivo(".jpg"), "Imagens")
        self.assertEqual(obter_tipo_arquivo(".mp4"), "Videos")
        self.assertEqual(obter_tipo_arquivo(".mp3"), "Musicas")
        self.assertEqual(obter_tipo_arquivo(".xlsx"), "Planilhas")
        self.assertEqual(obter_tipo_arquivo(".zip"), "Arquivos_Comprimidos")
        self.assertEqual(obter_tipo_arquivo(".random"), "Outros")

    def test_calcular_hash(self):
        """Verifica se arquivos idênticos geram o mesmo hash MD5."""
        f1 = self.test_dir / "documento1.txt"
        f2 = self.test_dir / "documento2.txt"
        self.assertEqual(calcular_hash(f1), calcular_hash(f2))
        
        f3 = self.test_dir / "imagem.jpg"
        self.assertNotEqual(calcular_hash(f1), calcular_hash(f3))

    def test_detectar_duplicatas(self):
        """Verifica se o sistema detecta corretamente arquivos duplicados pelo conteúdo."""
        dups = detectar_duplicatas(self.test_dir)
        # Deve encontrar exatamente um grupo de duplicatas (documento1 e documento2)
        self.assertEqual(len(dups), 1)
        
        for h, paths in dups.items():
            self.assertEqual(len(paths), 2)
            nomes = [p.name for p in paths]
            self.assertIn("documento1.txt", nomes)
            self.assertIn("documento2.txt", nomes)

    @patch('builtins.input', return_value='2')  # Opção: Mover para pasta Duplicatas
    def test_lidar_com_duplicatas_mover(self, mock_input):
        """Testa a lógica de mover duplicatas via menu."""
        dups = detectar_duplicatas(self.test_dir)
        lidar_com_duplicatas(dups, self.test_dir)
        
        pasta_dups = self.test_dir / "Duplicatas"
        self.assertTrue(pasta_dups.exists())
        # Um deve ficar no lugar (ou ser movido depois), outro vai para Duplicatas
        arquivos_dups = list(pasta_dups.glob("*.txt"))
        self.assertEqual(len(arquivos_dups), 1)

    @patch('builtins.input', return_value='3')  # Opção: Apagar duplicatas
    def test_lidar_com_duplicatas_apagar(self, mock_input):
        """Testa a lógica de apagar duplicatas via menu."""
        dups = detectar_duplicatas(self.test_dir)
        lidar_com_duplicatas(dups, self.test_dir)
        
        # Apenas um dos documentos deve sobrar na raiz (antes da organização)
        txt_files = [f for f in self.test_dir.iterdir() if f.suffix == '.txt']
        self.assertEqual(len(txt_files), 1)

    def test_detectar_duplicatas_com_filtro(self):
        """Verifica se o filtro de duplicatas funciona corretamente."""
        # Adiciona uma duplicata de imagem para o teste
        (self.test_dir / "imagem_copia.jpg").write_text("dados binários fictícios de imagem")
        
        # Testa filtro para Documentos (deve ignorar a duplicata de imagem)
        dups_docs = detectar_duplicatas(self.test_dir, filtro_extensoes=tipos['Documentos'])
        self.assertEqual(len(dups_docs), 1)
        for paths in dups_docs.values():
            self.assertTrue(all(p.suffix == '.txt' for p in paths))

        # Testa filtro para Imagens (deve ignorar a duplicata de texto)
        dups_imgs = detectar_duplicatas(self.test_dir, filtro_extensoes=tipos['Imagens'])
        self.assertEqual(len(dups_imgs), 1)
        for paths in dups_imgs.values():
            self.assertTrue(all(p.suffix == '.jpg' for p in paths))

    def test_organizar_arquivos(self):
        """Verifica se os arquivos são movidos para as subpastas corretas."""
        organizar_arquivos(self.test_dir)
        
        # Checar se as pastas de destino foram criadas e contêm os arquivos
        self.assertTrue((self.test_dir / "Documentos" / "documento1.txt").exists())
        self.assertTrue((self.test_dir / "Imagens" / "imagem.jpg").exists())
        self.assertTrue((self.test_dir / "Videos" / "video.mp4").exists())
        self.assertTrue((self.test_dir / "Outros" / "desconhecido.xyz").exists())
        
        # Checar se o arquivo original foi movido (não deve existir mais na raiz do diretório de teste)
        self.assertFalse((self.test_dir / "imagem.jpg").exists())

    def test_organizar_arquivos_com_filtro(self):
        """Verifica se apenas os arquivos do filtro selecionado são movidos."""
        # Organizar apenas vídeos
        organizar_arquivos(self.test_dir, filtro_extensoes=tipos['Videos'])
        
        # O vídeo deve ter sido movido
        self.assertTrue((self.test_dir / "Videos" / "video.mp4").exists())
        # A imagem NÃO deve ter sido movida (continua na raiz)
        self.assertTrue((self.test_dir / "imagem.jpg").exists())
        self.assertFalse((self.test_dir / "Imagens").exists())

    def test_super_normalizer_path_cleaning(self):
        """Verifica se o normalizador limpa aspas e espaços adequadamente."""
        path_with_quotes = '  "C:/Caminho/De/Teste"  '
        normalized = super_normalizer(path_with_quotes)
        self.assertIsInstance(normalized, Path)

    @patch('builtins.input', return_value='s') # Mock input para confirmar remoção do log
    def test_desfazer_organizacao(self, mock_input):
        """Verifica se a função desfazer_organizacao restaura os arquivos corretamente."""
        # 1. Preparar arquivos e simular organização
        original_doc_path = self.test_dir / "documento1.txt"
        original_img_path = self.test_dir / "imagem.jpg"
        
        # Simular movimentação para pastas de tipo
        pasta_documentos = self.test_dir / "Documentos"
        pasta_imagens = self.test_dir / "Imagens"
        
        pasta_documentos.mkdir()
        pasta_imagens.mkdir()

        moved_doc_path = pasta_documentos / original_doc_path.name
        moved_img_path = pasta_imagens / original_img_path.name

        shutil.move(str(original_doc_path), str(moved_doc_path))
        shutil.move(str(original_img_path), str(moved_img_path))

        # Registrar as movimentações no log
        registrar_log(self.test_dir, original_doc_path, moved_doc_path)
        registrar_log(self.test_dir, original_img_path, moved_img_path)

        self.assertFalse(original_doc_path.exists())
        self.assertTrue(moved_doc_path.exists())
        self.assertFalse(original_img_path.exists())
        self.assertTrue(moved_img_path.exists())
        self.assertTrue((self.test_dir / "agrupador_history.txt").exists())

        # 2. Chamar a função de desfazer
        desfazer_organizacao(str(self.test_dir))

        # 3. Verificar se os arquivos foram restaurados e o log removido
        self.assertTrue(original_doc_path.exists())
        self.assertTrue(original_img_path.exists())
        self.assertFalse(moved_doc_path.exists()) # Não deve mais existir na pasta de destino
        self.assertFalse(moved_img_path.exists()) # Não deve mais existir na pasta de destino
        self.assertFalse((self.test_dir / "agrupador_history.txt").exists()) # Log deve ter sido removido

if __name__ == "__main__":
    unittest.main()