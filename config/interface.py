"""Constantes de aparência, dimensões, cores, textos e log da interface gráfica."""

from pathlib import Path

# --- Identificação e Log da Aplicação ---
TITULO_JANELA = "Projeto Broadcast - Conversor TS (HEVC 60p BWDIF)"
TITULO_POPUP = "Projeto Broadcast"
TITULO_DIALOGO_NVENC = "Selecionar executável nvenc64"
TITULO_DIALOGO_TS = "Selecionar arquivo .ts"
CAMINHO_ARQUIVO_LOG = Path("projeto_broadcast.log")
FORMATO_REGISTRO_LOG = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# --- Dimensões e Temporização da Janela ---
LARGURA_JANELA = 560
ALTURA_JANELA = 170
LARGURA_ZONA_ARRASTE = 205
ALTURA_BARRA_PROGRESSO = 22
ALTURA_BOTAO_NVENC = 24
MARGEM_EXTERNA_LAYOUT = 10
ESPACAMENTO_LAYOUT = 10
INTERVALO_TIMER_SEGUNDOS_MS = 1000
INTERVALO_MINIMO_ATUALIZACAO_UI_S = 0.10
LIMITE_CARACTERES_NOME_ARQUIVO = 26

# --- Paleta do Modo Claro e Cores QSS ---
COR_FUNDO_JANELA = "#F5F5F5"
COR_FUNDO_PAINEL = "#FFFFFF"
COR_FUNDO_ZONA_ATIVA = "#FAFAFA"
COR_FUNDO_ZONA_INATIVA = "#ECECEC"
COR_BORDA_ZONA_ATIVA = "#8A8A8A"
COR_BORDA_ZONA_INATIVA = "#C8C8C8"
COR_TEXTO_PRINCIPAL = "#1E1E1E"
COR_TEXTO_SECUNDARIO = "#5A5A5A"
COR_TEXTO_DESABILITADO = "#8C8C8C"
COR_DESTAQUE_SELECAO = "#0078D7"
COR_TEXTO_SELECAO = "#FFFFFF"
COR_BOTAO_FUNDO = "#FFFFFF"
COR_BOTAO_HOVER = "#EBF3FC"
COR_BOTAO_BORDA = "#0078D7"

# --- Cores da Barra de Progresso (Estilo Verde Windows) ---
COR_BARRA_PREENCHIMENTO = "#06B025"
COR_BARRA_FUNDO = "#E6E6E6"
COR_BARRA_BORDA = "#BCBCBC"
COR_BARRA_TEXTO = "#1E1E1E"

# --- Textos Fixos da Interface (Português do Brasil) ---
TEXTO_ZONA_ARRASTE_LIVRE = "Selecione ou arraste um arquivo .ts aqui"
TEXTO_BOTAO_SELECIONAR_NVENC = "Selecionar nvenc64"
TEXTO_VALOR_VAZIO = "—"
TEXTO_CALCULANDO = "calculando…"
TEXTO_DURACAO_INDISPONIVEL = "indisponível"

STATUS_AGUARDANDO = "Aguardando arquivo .ts"
STATUS_CONVERTENDO = "Convertendo…"
STATUS_CONCLUIDO = "Concluído"
STATUS_FALHA = "Falha na conversão"
STATUS_ARQUIVO_INVALIDO = "Solte um único arquivo .ts"
STATUS_NVENC_PENDENTE = "Selecione o executável nvenc64"

ROTULO_ARQUIVO = "Arquivo:"
ROTULO_TAMANHO = "Tamanho:"
ROTULO_DURACAO = "Duração:"
ROTULO_STATUS = "Status:"
ROTULO_DECORRIDO = "Decorrido:"
ROTULO_RESTANTE = "Restante:"

MENSAGEM_POPUP_CONCLUSAO = "Conversão concluída"
MENSAGEM_CONFIRMAR_SAIDA = (
    "Há uma conversão em andamento.\nDeseja encerrar o processo e sair?"
)
MENSAGEM_NVENC_NAO_IDENTIFICADO = (
    "O software nvenc64 não foi identificado automaticamente. "
    "Gostaria de selecionar o executável manualmente?"
)
MENSAGEM_DOWNLOAD_NVENC = (
    "Faça o download do nvenc64 através do link:<br>"
    '<a href="https://github.com/rigaya/NVEnc/releases">'
    "https://github.com/rigaya/NVEnc/releases</a><br><br>"
    "Depois de concluir o download e extrair os arquivos, clique no botão "
    '<b>"Selecionar nvenc64"</b> na interface para indicar o executável.'
)
