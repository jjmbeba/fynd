from infrastructure.fx.client import FxClient
from infrastructure.fx.frankfurter import FrankfurterClient


def get_active_fx_clients() -> list[FxClient]:
    return [FrankfurterClient()]
