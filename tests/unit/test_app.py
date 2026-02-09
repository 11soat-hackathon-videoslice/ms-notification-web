import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from core.dtos.notification_dto import NotificationDto, NotificationContentDto, WebPayloadDto
from core.dtos.vdsc_metadata_dto import VdscMetadataDTO
from core.enums.notification_channels_enum import NotificationChannelsEnum
from src.app import lambda_handler, _process_notification_web


class TestLambdaHandler:
    """Testes para o handler principal da Lambda"""

    @pytest.fixture
    def valid_sqs_event(self):
        """Fixture com evento SQS válido"""
        return {
            "Records": [
                {
                    "messageId": "test-message-id",
                    "body": json.dumps({
                        "detail": {
                            "id": "test-notification-id",
                            "channels": ["WEB"],
                            "content": [{
                                "web": {
                                    "message": "Test message",
                                    "timestamp": "2026-02-09T10:00:00Z",
                                    "is_read": False,
                                    "user_id": "test-user-id"
                                }
                            }],
                            "metadata": {
                                "userId": "test-user-id",
                                "videoId": "test-video-id",
                                "fileName": "test.mp4",
                                "extension_file": "mp4",
                                "status": "uploaded",
                                "created": "2026-02-09T10:00:00Z",
                                "totalTime": 10,
                                "unitTime": "s",
                                "startTime": 0,
                                "endTime": 10,
                                "timeInterval": ["0", "1", "2"],
                                "maxRetry": 3,
                                "retries": 0,
                                "quality": "medium",
                                "logs": []
                            }
                        }
                    })
                }
            ]
        }

    @pytest.fixture
    def invalid_sqs_event(self):
        """Fixture com evento SQS inválido"""
        return {
            "Records": [
                {
                    "messageId": "test-message-id",
                    "body": json.dumps({
                        "detail": {
                            "id": "test-notification-id",
                            "channels": ["EMAIL"],  # Sem canal web
                            "content": [{
                                "email": {
                                    "template": "UPDATE_STATUS",
                                    "user_id": "test-user-id"
                                }
                            }],
                            "metadata": {
                                "userId": "test-user-id",
                                "videoId": "test-video-id",
                                "fileName": "test.mp4",
                                "extension_file": "mp4",
                                "status": "uploaded",
                                "created": "2026-02-09T10:00:00Z",
                                "totalTime": 10,
                                "unitTime": "s",
                                "startTime": 0,
                                "endTime": 10,
                                "timeInterval": ["0", "1"],
                                "maxRetry": 3,
                                "retries": 0,
                                "quality": "medium",
                                "logs": []
                            }
                        }
                    })
                }
            ]
        }

    @pytest.fixture
    def empty_event(self):
        """Fixture com evento vazio"""
        return {"Records": []}

    @patch('src.app.controller')
    def test_lambda_handler_success(self, mock_controller, valid_sqs_event):
        """Testa processamento bem-sucedido de notificação web"""
        # Arrange
        mock_controller.send = Mock()

        # Act
        result = lambda_handler(valid_sqs_event, None)

        # Assert
        assert result['statusCode'] == 202
        assert "1 evento(s)" in result['body']
        mock_controller.send.assert_called_once()

    @patch('src.app.controller')
    def test_lambda_handler_empty_records(self, mock_controller, empty_event):
        """Testa processamento com lista de registros vazia"""
        # Arrange
        mock_controller.send = Mock()

        # Act
        result = lambda_handler(empty_event, None)

        # Assert
        assert result['statusCode'] == 202
        assert "0 evento(s)" in result['body']
        mock_controller.send.assert_not_called()

    @patch('src.app.controller')
    @patch('src.app.logger')
    def test_lambda_handler_invalid_notification(self, mock_logger, mock_controller, invalid_sqs_event):
        """Testa processamento de notificação inválida"""
        # Arrange
        mock_controller.send = Mock()

        # Act
        result = lambda_handler(invalid_sqs_event, None)

        # Assert
        assert result['statusCode'] == 500
        assert "error" in result['body']
        mock_logger.error.assert_called()

    @patch('src.app.controller')
    def test_lambda_handler_multiple_records(self, mock_controller, valid_sqs_event):
        """Testa processamento de múltiplos registros"""
        # Arrange
        valid_sqs_event['Records'].append(valid_sqs_event['Records'][0].copy())
        mock_controller.send = Mock()

        # Act
        result = lambda_handler(valid_sqs_event, None)

        # Assert
        assert result['statusCode'] == 202
        assert "2 evento(s)" in result['body']
        assert mock_controller.send.call_count == 2

    @patch('src.app.controller')
    def test_lambda_handler_json_parse_error(self, mock_controller):
        """Testa erro ao parsear JSON inválido"""
        # Arrange
        event = {
            "Records": [
                {
                    "messageId": "test-message-id",
                    "body": "invalid json"
                }
            ]
        }

        # Act
        result = lambda_handler(event, None)

        # Assert
        assert result['statusCode'] == 500
        assert "error" in result['body']

    @patch('src.app.controller')
    @patch('src.app.logger')
    def test_process_notification_web_success(self, mock_logger, mock_controller):
        """Testa processamento bem-sucedido de notificação web"""
        # Arrange
        notification_dto = NotificationDto(
            id="test-id",
            channels=[NotificationChannelsEnum.WEB],
            content=[NotificationContentDto(
                web=WebPayloadDto(
                    message="Test message",
                    timestamp=datetime(2026, 2, 9, 10, 0, 0),
                    is_read=False,
                    user_id="test-user-id"
                )
            )],
            metadata=VdscMetadataDTO(
                user_id="test-user-id",
                video_id="test-video-id",
                file_name="test.mp4",
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
        mock_controller.send = Mock()

        # Act
        _process_notification_web(notification_dto)

        # Assert
        mock_controller.send.assert_called_once_with(notification_dto, NotificationChannelsEnum.WEB)
        mock_logger.info.assert_called()

    @patch('src.app.controller')
    @patch('src.app.logger')
    def test_process_notification_web_error(self, mock_logger, mock_controller):
        """Testa erro ao processar notificação web"""
        # Arrange
        notification_dto = Mock()
        notification_dto.id = "test-id"
        mock_controller.send = Mock(side_effect=Exception("Test error"))

        # Act
        _process_notification_web(notification_dto)

        # Assert
        mock_logger.error.assert_called()
        error_message = str(mock_logger.error.call_args[0][0])
        assert "Erro ao processar Notificação web" in error_message
        assert "test-id" in error_message

    def test_lambda_handler_with_context(self, valid_sqs_event):
        """Testa handler com contexto Lambda"""
        # Arrange
        mock_context = Mock()
        mock_context.function_name = "test-function"
        mock_context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789:function:test"

        with patch('src.app.controller') as mock_controller:
            mock_controller.send = Mock()

            # Act
            result = lambda_handler(valid_sqs_event, mock_context)

            # Assert
            assert result['statusCode'] == 202

    @patch('src.app.controller')
    def test_lambda_handler_missing_detail_key(self, mock_controller):
        """Testa processamento quando falta a chave 'detail' no body"""
        # Arrange
        event = {
            "Records": [
                {
                    "messageId": "test-message-id",
                    "body": json.dumps({
                        "no_detail": "data"
                    })
                }
            ]
        }

        # Act
        result = lambda_handler(event, None)

        # Assert
        assert result['statusCode'] == 500
        assert "error" in result['body']

    @patch('src.app.controller')
    def test_lambda_handler_notification_without_web_content(self, mock_controller):
        """Testa notificação sem conteúdo web"""
        # Arrange
        event = {
            "Records": [
                {
                    "messageId": "test-message-id",
                    "body": json.dumps({
                        "detail": {
                            "id": "test-id",
                            "channels": ["email"],
                            "content": [{
                                "email": {
                                    "template": "test",
                                    "user_id": "test-user"
                                }
                            }],
                            "metadata": {
                                "user_id": "test-user"
                            }
                        }
                    })
                }
            ]
        }

        # Act
        result = lambda_handler(event, None)

        # Assert
        assert result['statusCode'] == 500

