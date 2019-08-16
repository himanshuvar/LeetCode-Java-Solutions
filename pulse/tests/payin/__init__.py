from payin_client import ApiClient, DefaultApi, Configuration
from ..utils import SERVICE_URI

payin_configuration = Configuration(host=SERVICE_URI)
payin_configuration.verify_ssl = False
payin_crud_client = DefaultApi(ApiClient(configuration=payin_configuration))