import psutil

# Tracks which models are currently loaded
_loaded_models = set()

# Approximate RAM cost per model (MB)
# You can tune these numbers based on your hardware
MODEL_RAM_COST = {
    "tiny": 800,
    "coder": 1600,
    "reason": 2200,
    "voice": 1200,
}

# Maximum RAM you want OpenClaw to use (MB)
# Keep this conservative on 8GB systems
MAX_RAM_MB = 14000


def _get_used_ram_mb():
    return psutil.virtual_memory().used // (1024 * 1024)


def _get_model_cost(model_name):
    return MODEL_RAM_COST.get(model_name, 1000)


def can_load(model_name):
    """Return True if loading this model will not exceed RAM limits."""
    current_ram = _get_used_ram_mb()
    cost = _get_model_cost(model_name)

    if current_ram + cost > MAX_RAM_MB:
        return False

    return True


def mark_loaded(model_name):
    """Record that a model is now loaded."""
    _loaded_models.add(model_name)


def mark_unloaded(model_name):
    """Record that a model has been unloaded."""
    if model_name in _loaded_models:
        _loaded_models.remove(model_name)


def suggest_eviction():
    """Return the largest loaded model if RAM is too full."""
    if not _loaded_models:
        return None

    # Sort by RAM cost, descending
    return sorted(_loaded_models, key=lambda m: _get_model_cost(m), reverse=True)[0]
