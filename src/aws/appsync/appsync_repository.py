import logging
import os

import boto3
import requests
from core.dtos.notification_dto import NotificationDto
from core.interfaces.notification.notication_interfaces import NotificationDatasourceInterface
from requests_aws4auth import AWS4Auth

region = os.environ.get('AWS_REGION', "us-east-1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppSyncNotificationWeb(NotificationDatasourceInterface):
    """Datasource para envio de notificações web via AppSync"""

    def send(self, notification: NotificationDto) -> None:
        appsync_url = os.environ.get('APPSYNC_URL')

        if appsync_url is None:
            logger.error("APPSYNC_URL não configurada. Verifique as variáveis de ambiente.")
            raise ValueError("APPSYNC_URL não configurada. Verifique as variáveis de ambiente.")

        auth = self._get_auth_appsync()
        mutation = self._get_create_notification_mutation()
        logger.debug(f"mutation: {mutation}")
        variables = self._set_create_notification_mutation_variables(notification)
        logger.debug(f"variables: {variables}")

        try:
            response = requests.post(
                appsync_url,
                json={'query': mutation, 'variables': variables},
                headers={'Content-Type': 'application/json'},
                auth=auth
                #,verify=False #Somente para testes locais, remover em produção para garantir segurança
            )
            response.raise_for_status()
            logger.info(f"Notificação web criada com sucesso: {response}")

        except Exception as e:
            logger.error(f"Erro ao criar notificação web: {e}")
            raise

    def _get_auth_appsync(self):
        credentials = boto3.Session().get_credentials()
        return AWS4Auth(credentials.access_key, credentials.secret_key, region, 'appsync', session_token=credentials.token)

    def _get_create_notification_mutation(self) -> str:
        return """
                mutation CreateNotification($input: CreateNotificationInput!) {
                    createNotification(input: $input) {
                    id
                    userId
                    timestamp
                    message
                    status
                    isRead
                    videoId
                    fileName
                    fileExtension
                }
            }
        """
    def _set_create_notification_mutation_variables(self, notification: NotificationDto) -> dict:
        content = notification.content[0] if isinstance(notification.content, list) else notification.content
        timestamp_formatted = content.web.timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
        return {
            "input": {
                "id": notification.id,
                "userId": notification.metadata.user_id,
                "timestamp": timestamp_formatted,
                "message": content.web.message,
                "status": notification.metadata.status,
                "isRead": "false",
                "videoId": notification.metadata.video_id,
                "fileName": notification.metadata.file_name,
                "fileExtension": notification.metadata.file_extension
            }
        }
