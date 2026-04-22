"""Configurações de categorias e extensões para o Agrupador."""

TIPOS_ARQUIVOS = {
    'Documentos': ['.txt', '.doc', '.docx', '.pdf', '.rtf'],
    'Imagens': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'],
    'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
    'Musicas': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', '.pcm', '.aiff', '.mid', '.cda'],
    'Planilhas': ['.xls', '.xlsx', '.csv', '.ods'],
    'Arquivos_Comprimidos': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Executaveis': ['.exe', '.msi', '.bat', '.sh'],
    'Outros': []
}

NOME_LOG = "agrupador_history.txt"