import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from requests_aws4auth import AWS4Auth

from aws.appsync.appsync_repository import AppSyncNotificationWeb
from core.dtos.notification_dto import NotificationDto, NotificationContentDto, WebPayloadDto
from core.dtos.vdsc_metadata_dto import VdscMetadataDTO
from core.enums.notification_channels_enum import NotificationChannelsEnum


class TestAppSyncNotificationWeb:
    """Testes para o datasource AppSync de notificações web"""

    @pytest.fixture
    def appsync_repository(self):
        """Fixture que retorna uma instância do repositório AppSync"""
        return AppSyncNotificationWeb()

    @pytest.fixture
    def valid_notification_dto(self):
        """Fixture com NotificationDto válido"""
        return NotificationDto(
            id="test-notification-id",
            channels=[NotificationChannelsEnum.WEB],
            content=[NotificationContentDto(
                web=WebPayloadDto(
                    message="Test notification message",
                    timestamp=datetime(2026, 2, 9, 10, 30, 0),
                    is_read=False,
                    user_id="test-user-id"
                )
            )],
            metadata=VdscMetadataDTO(
                user_id="test-user-id",
                video_id="test-video-id",
                file_name="test_video.mp4",
                extension_file="mp4",
                status="uploaded",
                created="2026-02-09T10:00:00Z",
                total_time=10,
                unit_time="s",
                start_time=0,
                end_time=10,
                time_interval=["0", "1", "2"],
                max_retry=3,
                retries=0,
                quality="medium",
                logs=[]
            )
        )

    @pytest.fixture
    def notification_dto_with_list_content(self):
        """Fixture com NotificationDto com content como lista"""
        return NotificationDto(
            id="test-id-list",
            channels=[NotificationChannelsEnum.WEB],
            content=[
                NotificationContentDto(
                    web=WebPayloadDto(
                        message="First message",
                        timestamp=datetime(2026, 2, 9, 10, 0, 0),
                        is_read=False,
                        user_id="user-1"
                    )
                ),
                NotificationContentDto(
                    web=WebPayloadDto(
                        message="Second message",
                        timestamp=datetime(2026, 2, 9, 11, 0, 0),
                        is_read=True,
                        user_id="user-2"
                    )
                )
            ],
            metadata=VdscMetadataDTO(
                user_id="user-1",
                video_id="video-1",
                file_name="video.mp4",
                extension_file="mp4",
                status="uploaded",
                created="2026-02-09T10:00:00Z",
                total_time=10,
                unit_time="s",
                start_time=0,
                end_time=10,
                time_interval=["0", "1", "2"],
                max_retry=3,
                retries=0,
                quality="medium",
                logs=[]
            )
        )

    @patch('aws.appsync.appsync_repository.requests.post')
    @patch('aws.appsync.appsync_repository.boto3.Session')
    def test_send_notification_success(self, mock_session, mock_post, appsync_repository, valid_notification_dto):
        """Testa envio bem-sucedido de notificação"""
        # Arrange
        mock_credentials = Mock()
        mock_credentials.access_key = "test-access-key"
        mock_credentials.secret_key = "test-secret-key"
        mock_credentials.token = "test-token"
        mock_session.return_value.get_credentials.return_value = mock_credentials

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "createNotification": {
                    "id": "test-notification-id",
                    "userId": "test-user-id"
                }
            }
        }
        mock_post.return_value = mock_response

        # Act
        appsync_repository.send(valid_notification_dto)

        # Assert
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args[1]
        assert 'json' in call_kwargs
        assert 'query' in call_kwargs['json']
        assert 'variables' in call_kwargs['json']
        assert call_kwargs['json']['variables']['input']['id'] == "test-notification-id"
        assert call_kwargs['json']['variables']['input']['userId'] == "test-user-id"

    @patch('aws.appsync.appsync_repository.requests.post')
    @patch('aws.appsync.appsync_repository.boto3.Session')
    def test_send_notification_http_error(self, mock_session, mock_post, appsync_repository, valid_notification_dto):
        """Testa erro HTTP ao enviar notificação"""
        # Arrange
        mock_credentials = Mock()
        mock_credentials.access_key = "test-access-key"
        mock_credentials.secret_key = "test-secret-key"
        mock_credentials.token = "test-token"
        mock_session.return_value.get_credentials.return_value = mock_credentials

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = Exception("HTTP 500 Error")
        mock_post.return_value = mock_response

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            appsync_repository.send(valid_notification_dto)
        assert "HTTP 500 Error" in str(exc_info.value)

    @patch('aws.appsync.appsync_repository.requests.post')
    @patch('aws.appsync.appsync_repository.boto3.Session')
    def test_send_notification_connection_error(self, mock_session, mock_post, appsync_repository, valid_notification_dto):
        """Testa erro de conexão ao enviar notificação"""
        # Arrange
        mock_credentials = Mock()
        mock_credentials.access_key = "test-access-key"
        mock_credentials.secret_key = "test-secret-key"
        mock_credentials.token = "test-token"
        mock_session.return_value.get_credentials.return_value = mock_credentials

        mock_post.side_effect = Exception("Connection error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            appsync_repository.send(valid_notification_dto)
        assert "Connection error" in str(exc_info.value)

    def test_get_auth_appsync(self, appsync_repository):
        """Testa obtenção de autenticação AWS4Auth"""
        # Arrange & Act
        with patch('aws.appsync.appsync_repository.boto3.Session') as mock_session:
            mock_credentials = Mock()
            mock_credentials.access_key = "test-key"
            mock_credentials.secret_key = "test-secret"
            mock_credentials.token = "test-token"
            mock_session.return_value.get_credentials.return_value = mock_credentials

            auth = appsync_repository._get_auth_appsync()

            # Assert
            assert isinstance(auth, AWS4Auth)
            assert auth.access_id == "test-key"

    def test_get_create_notification_mutation(self, appsync_repository):
        """Testa geração da mutation GraphQL"""
        # Act
        mutation = appsync_repository._get_create_notification_mutation()

        # Assert
        assert "mutation CreateNotification" in mutation
        assert "createNotification" in mutation
        assert "CreateNotificationInput" in mutation
        assert "userId" in mutation
        assert "id" in mutation

    def test_set_create_notification_mutation_variables(self, appsync_repository, valid_notification_dto):
        """Testa criação de variáveis para a mutation"""
        # Act
        variables = appsync_repository._set_create_notification_mutation_variables(valid_notification_dto)

        # Assert
        assert "input" in variables
        assert variables["input"]["id"] == "test-notification-id"
        assert variables["input"]["userId"] == "test-user-id"
        assert variables["input"]["videoId"] == "test-video-id"
        assert variables["input"]["fileName"] == "test_video.mp4"
        assert variables["input"]["extentisonFile"] == "mp4"
        assert variables["input"]["message"] == "Test notification message"
        assert variables["input"]["isRead"] is False
        assert variables["input"]["timestamp"] == "2026-02-09T10:30:00Z"

    def test_set_create_notification_mutation_variables_with_list_content(self, appsync_repository, notification_dto_with_list_content):
        """Testa criação de variáveis quando content é uma lista"""
        # Act
        variables = appsync_repository._set_create_notification_mutation_variables(notification_dto_with_list_content)

        # Assert
        assert "input" in variables
        assert variables["input"]["id"] == "test-id-list"
        assert variables["input"]["message"] == "First message"  # Deve pegar o primeiro item
        assert variables["input"]["timestamp"] == "2026-02-09T10:00:00Z"

    @patch('aws.appsync.appsync_repository.requests.post')
    @patch('aws.appsync.appsync_repository.boto3.Session')
    @patch('aws.appsync.appsync_repository.logger')
    def test_send_notification_logs_success(self, mock_logger, mock_session, mock_post, appsync_repository, valid_notification_dto):
        """Testa que logs são registrados em caso de sucesso"""
        # Arrange
        mock_credentials = Mock()
        mock_credentials.access_key = "test-key"
        mock_credentials.secret_key = "test-secret"
        mock_credentials.token = "test-token"
        mock_session.return_value.get_credentials.return_value = mock_credentials

        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        appsync_repository.send(valid_notification_dto)

        # Assert
        mock_logger.info.assert_called_once()
        assert "Notificação web criada com sucesso" in str(mock_logger.info.call_args)

    @patch('aws.appsync.appsync_repository.requests.post')
    @patch('aws.appsync.appsync_repository.boto3.Session')
    @patch('aws.appsync.appsync_repository.logger')
    def test_send_notification_logs_error(self, mock_logger, mock_session, mock_post, appsync_repository, valid_notification_dto):
        """Testa que logs são registrados em caso de erro"""
        # Arrange
        mock_credentials = Mock()
        mock_credentials.access_key = "test-key"
        mock_credentials.secret_key = "test-secret"
        mock_credentials.token = "test-token"
        mock_session.return_value.get_credentials.return_value = mock_credentials

        mock_post.side_effect = Exception("Test error")

        # Act & Assert
        with pytest.raises(Exception):
            appsync_repository.send(valid_notification_dto)

        mock_logger.error.assert_called_once()
        assert "Erro ao criar notificação web" in str(mock_logger.error.call_args)

    @patch('aws.appsync.appsync_repository.requests.post')
    @patch('aws.appsync.appsync_repository.boto3.Session')
    def test_send_notification_with_different_timestamp_format(self, mock_session, mock_post, appsync_repository):
        """Testa envio de notificação com diferentes formatos de timestamp"""
        # Arrange
        mock_credentials = Mock()
        mock_credentials.access_key = "test-key"
        mock_credentials.secret_key = "test-secret"
        mock_credentials.token = "test-token"
        mock_session.return_value.get_credentials.return_value = mock_credentials

        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        notification = NotificationDto(
            id="test-id",
            channels=[NotificationChannelsEnum.WEB],
            content=[NotificationContentDto(
                web=WebPayloadDto(
                    message="Test",
                    timestamp=datetime(2026, 1, 13, 0, 0, 0),  # Formato específico das instruções
                    is_read=False,
                    user_id="user-id"
                )
            )],
            metadata=VdscMetadataDTO(
                user_id="user-id",
                video_id="video-id",
                file_name="file.mp4",
                extension_file="mp4",
                status="uploaded",
                created="2026-01-13T00:00:00Z",
                total_time=10,
                unit_time="s",
                start_time=0,
                end_time=10,
                time_interval=["0"],
                max_retry=3,
                retries=0,
                quality="medium",
                logs=[]
            )
        )

        # Act
        appsync_repository.send(notification)

        # Assert
        call_kwargs = mock_post.call_args[1]
        timestamp = call_kwargs['json']['variables']['input']['timestamp']
        assert timestamp == "2026-01-13T00:00:00Z"

    @patch('aws.appsync.appsync_repository.requests.post')
    @patch('aws.appsync.appsync_repository.boto3.Session')
    def test_send_notification_uses_correct_url_and_headers(self, mock_session, mock_post, appsync_repository, valid_notification_dto):
        """Testa que a URL e headers corretos são utilizados"""
        # Arrange
        mock_credentials = Mock()
        mock_credentials.access_key = "test-key"
        mock_credentials.secret_key = "test-secret"
        mock_credentials.token = "test-token"
        mock_session.return_value.get_credentials.return_value = mock_credentials

        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Act
        appsync_repository.send(valid_notification_dto)

        # Assert
        call_args = mock_post.call_args
        assert call_args[0][0] or call_args[1].get('url')  # URL é passada
        assert call_args[1]['headers']['Content-Type'] == 'application/json'
        assert call_args[1]['verify'] is False

    def test_set_mutation_variables_handles_single_content_object(self, appsync_repository):
        """Testa que variáveis são criadas corretamente quando content não é lista"""
        # Arrange
        notification = NotificationDto(
            id="test-id",
            channels=[NotificationChannelsEnum.WEB],
            content=[NotificationContentDto(  # É lista mas com um único elemento
                web=WebPayloadDto(
                    message="Single message",
                    timestamp=datetime(2026, 2, 9, 10, 0, 0),
                    is_read=False,
                    user_id="user-id"
                )
            )],
            metadata=VdscMetadataDTO(
                user_id="user-id",
                video_id="video-id",
                file_name="file.mp4",
                extension_file="mp4",
                status="uploaded",
                created="2026-02-09T10:00:00Z",
                total_time=10,
                unit_time="s",
                start_time=0,
                end_time=10,
                time_interval=["0"],
                max_retry=3,
                retries=0,
                quality="medium",
                logs=[]
            )
        )

        # Act
        variables = appsync_repository._set_create_notification_mutation_variables(notification)

        # Assert
        assert variables["input"]["message"] == "Single message"

