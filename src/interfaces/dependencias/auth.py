from capitalexpress_auth import CapitalExpressAuth

from src.config import settings

auth_manager = CapitalExpressAuth(
    region=settings.aws_region,
    user_pool_id=settings.cognito_user_pool_id,
    app_client_id=settings.cognito_app_client_id,
    api_keys=settings.parsed_api_keys,
)

get_current_user = auth_manager.get_current_user
require_roles = auth_manager.require_roles
