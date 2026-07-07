from infrastructure.fx.client import FxClient
from infrastructure.fx.frankfurter import FrankfurterClient


def get_active_fx_clients() -> list[FxClient]:
    try:
        instance = FrankfurterClient()
    except Exception as exc:
        raise ValueError(f"Failed to instantiate {FrankfurterClient.__name__}: {exc}") from exc
    if not isinstance(instance, FxClient):
        raise ValueError(f"{FrankfurterClient.__name__} is not an FxClient")
    return [instance]
