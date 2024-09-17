import math

import numpy as np
import repype.stage
import scipy.ndimage as ndi


class Preprocessing(repype.stage.Stage):
    """Implements the computation of the intensity offsets (see :ref:`pipeline_theory_cvxprog`).

    This stage requires ``g_raw`` for input (the input image) and produces ``y`` for output (the offset image intensities). Refer to :ref:`pipeline_inputs_and_outputs` for more information on the available inputs and outputs.

    Hyperparameters
    ---------------

    The following hyperparameters can be used to control this pipeline stage:

    ``preprocess/sigma1``
        The scale of the Gaussian filter used for denoising. Defaults to :math:`\\sqrt{2}`.

    ``preprocess/sigma2``
        The scale of the Gaussian filter :math:`\\mathcal G_\\sigma`, which is used to determine the intensity offsets :math:`\\tau_x` (see :ref:`pipeline_theory_cvxprog`). Defaults to :math:`40`, or to ``AF_sigma2 × scale`` if configured automatically (and ``AF_sigma2`` defaults to 1).

    ``preprocess/offset_clip``
        Corresponds to :math:`\\tau_\\text{max}` in Supplemental Material 1. Defaults to :math:`3`.

    ``preprocess/lower_clip_mean``
        If `True`, intensity offsets :math:`\\tau_x` smaller than the mean image intensity are set to the mean image intensity. Defaults to `False`.
    """

    id = 'preprocess'
    inputs  = ['g_raw']
    outputs = ['y']

    def process(self, g_raw, pipeline, config, status=None):
        sigma1 = config.get('sigma1', math.sqrt(2))
        sigma2 = config.get('sigma2', 40)
        offset_clip  = config.get('offset_clip', 3)
        lower_clip_mean = config.get('lower_clip_mean', False)

        offset_original = ndi.gaussian_filter(g_raw, sigma2)
        if np.isinf(offset_clip):
            offset_combined = offset_original

        else:
            offset_clip_abs = offset_clip * g_raw.std()
            offset_clipped  = ndi.gaussian_filter(g_raw.clip(0, offset_clip_abs), sigma2)

            clip_area = (g_raw > offset_clip_abs)
            _tmp1 = ndi.distance_transform_edt(~clip_area)
            _tmp1 = (sigma2 - _tmp1).clip(0, np.inf)
            _tmp1 = (_tmp1 / _tmp1.max()) ** 2
            offset_combined = (1 - _tmp1) * offset_clipped + _tmp1 * offset_original
            
        if lower_clip_mean:
            offset_combined = np.max([offset_combined, np.full(g_raw.shape, g_raw.mean())], axis=0)

        y = ndi.gaussian_filter(g_raw, sigma1) - offset_combined
        
        return {
            'y': y,
        }

    def configure(self, pipeline, input_id, *args, scale, **kwargs):
        return {
            'sigma2': (scale, 1.0),
        }

