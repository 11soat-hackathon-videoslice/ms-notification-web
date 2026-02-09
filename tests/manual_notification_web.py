import sys
import os
import json
from pathlib import Path

# Adicionar path para o diretório src do ms-video-slice
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Adicionar path para o diretório src do video-slice-core
core_src_path = Path(__file__).parent.parent.parent / "video-slice-core" / "src"
sys.path.insert(0, str(core_src_path))


def notificacao_web_local():
    """Exemplo de atualização completa de metadados no formato DynamoDB"""
    from app import lambda_handler

    # Caminho do arquivo JSON com o evento do DynamoDB
    json_file_path = os.path.join(os.path.dirname(__file__), '..', 'events', 'sqs_notification_web_example.json')

    # Ler o conteúdo do arquivo JSON
    with open(json_file_path, 'r', encoding='utf-8') as file:
        event = json.load(file)

    print("Notificação carregada com sucesso carregado com sucesso!")

    # Simular contexto Lambda (pode ser None ou um objeto mock)
    context = None

    # Chamar o handler com o evento
    print(f"\n{'='*60}")
    print("Iniciando processamento do da notificação web...")
    print(f"{'='*60}\n")

    try:
        result = lambda_handler(event, context)
        print(f"\n{'='*60}")
        print("Processamento finalizado com sucesso!")
        print("="*60)
        if result:
            print(f"Resultado: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"Erro ao processar: {e}")
        print("="*60)
        raise


if __name__ == "__main__":
    print("="*60)
    print("TESTE DO MS-NOTIFICATION-WEB HANDLER")
    print(f"{'='*60}\n")

    notificacao_web_local()
