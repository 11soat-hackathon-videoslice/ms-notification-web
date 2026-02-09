# Datasources
from aws.appsync.appsync_repository import AppSyncNotificationWeb

# Core - Adapters
from core.adapters.notification.notification_controller import NotificationController
from core.adapters.notification.notification_gateway import NotificationGateway

# Core - Use Cases
from core.applications.notification.send_notification_web_use_case import SendNotificationWebUseCase

# Core - Domain
from core.domain.notification import Notification, NotificationContent, EmailPayload, WebPayload

# Core - DTOs
from core.dtos.notification_dto import NotificationDto, NotificationContentDto, EmailPayloadDto, WebPayloadDto

# Core - Enums
from core.enums.notification_channels_enum import NotificationChannelsEnum

# Core - Exceptions
from core.exceptions.vdsc_exceptions import VdscException

# Core - Interfaces
from core.interfaces.notification.notication_interfaces import (
    NotificationControllerInterface,
    NotificationDatasourceInterface,
    NotificationGatewayInterface,
    NotificationUseCaseInterface
)
from core.interfaces.vdsc_exception_handler_interface import VdscExceptionHandlerInterface

__all__ = [
    # Datasources
    'AppSyncNotificationWeb',

    # Core - Adapters
    'NotificationController',
    'NotificationGateway',

    # Core - Use Cases
    'SendNotificationWebUseCase',

    # Core - Domain
    'Notification',
    'NotificationContent',
    'EmailPayload',
    'WebPayload',

    # Core - DTOs
    'NotificationDto',
    'NotificationContentDto',
    'EmailPayloadDto',
    'WebPayloadDto',

    # Core - Enums
    'NotificationChannelsEnum',

    # Core - Exceptions
    'VdscException',

    # Core - Interfaces
    'NotificationControllerInterface',
    'NotificationDatasourceInterface',
    'NotificationGatewayInterface',
    'NotificationUseCaseInterface',
    'VdscExceptionHandlerInterface'
]
