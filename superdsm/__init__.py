from . import cpu_setup
from .version import (
    VERSION,
    VERSION_MAJOR,
    VERSION_MINOR,
    VERSION_PATCH,
)

__version__ = VERSION

from repype.config import Config

from . import \
    _mkl  # by-pass this bug: https://github.com/flatironinstitute/sparse_dot/issues/7
from .pipeline import Pipeline
