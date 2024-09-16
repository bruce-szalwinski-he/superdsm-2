import math

import numpy as np
import repype.config
import repype.pipeline
import repype.status
import scipy.ndimage as ndi
import skimage
import skimage.feature.blob

import superdsm.io


class Pipeline(repype.pipeline.Pipeline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from .c2freganal import C2F_RegionAnalysis
        from .dsmcfg import DSM_Config
        from .globalenergymin import GlobalEnergyMinimization
        from .postprocess import Postprocessing
        from .preprocess import Preprocessing

        self.stages = [
            LoadInput(),
            Preprocessing(),
            DSM_Config(),
            C2F_RegionAnalysis(),
            GlobalEnergyMinimization(),
            Postprocessing(),
        ]

    def configure(self, base_config, input_id, *args, img=None, **kwargs):
        scale = base_config.get('scale', None)
        if scale is None:
            if img is None:
                img_filepath = self.resolve('inputs', input_id)
                assert img_filepath is not None, f'Scopes: {self.scopes}'
                img = superdsm.io.imread(img_filepath)
            scale = _estimate_scale(img, num_radii=10, thresholds=[0.01])[0]
            base_config['scale'] = scale
        radius = scale * math.sqrt(2)
        diameter = 2 * radius
        return super().configure(base_config, input_id, *args, scale=scale, radius=radius, diameter=diameter, **kwargs)

    def process_image(self, g_raw, base_config, *args, **kwargs):
        assert g_raw is not None
        config = self.configure(base_config, img=g_raw, input_id='')
        self.stages[0].g_raw = g_raw
        return self.process(
            input_id='',
            config=config,
            *args,
            **kwargs
        )


class LoadInput(repype.stage.Stage):
    """
    Initializes the pipeline for processing the image ``g_raw``.

    The loaded image ``g_raw`` is made available as an input to the subsequent pipeline stages. However, if
    ``config['histological'] == True`` (i.e. the hyperparameter ``histological`` is set to ``True``), then ``g_raw`` is
    converted to a brightness-inverse intensity image, and the original image is provided as ``g_rgb`` to the stages of
    the pipeline.

    In addition, ``g_raw`` is normalized so that the intensities range from 0 to 1.
    """

    inputs = ['input_id']
    outputs = ['g_raw', 'g_rgb']

    g_raw = None

    def process(self, input_id, pipeline, config, status=None):
        from .image import normalize_image

        if self.g_raw is None:
            img_filepath = pipeline.resolve('inputs', input_id)
            g_raw = superdsm.io.imread(img_filepath)
        else:
            g_raw = self.g_raw
            self.g_raw = None

        if config.get('histological', False):
            g_rgb = g_raw
            g_raw = g_raw.mean(axis=2)
            g_raw = g_raw.max() - g_raw
        else:
            g_rgb = None

        return dict(
            g_raw=normalize_image(g_raw),
            g_rgb=g_rgb,
        )


def _blob_doh(image, sigma_list, threshold=0.01, overlap=.5, mask=None):
    """
    Finds blobs in the given grayscale image.

    This implementation is widely based on:
    https://github.com/scikit-image/scikit-image/blob/fca9f16da4bd7420245d05fa82ee51bb9677b039/skimage/feature/blob.py#L538-L646
    """
    skimage.feature.blob.check_nD(image, 2)
    if mask is None: mask = np.ones(image.shape, bool)
    if not isinstance(mask, dict): mask = {sigma: mask for sigma in sigma_list}

    image = skimage.feature.blob.img_as_float(image)
    image = skimage.feature.blob.integral_image(image)

    hessian_images = [mask[s] * skimage.feature.blob._hessian_matrix_det(image, s) for s in sigma_list]
    image_cube = np.dstack(hessian_images)

    local_maxima = skimage.feature.blob.peak_local_max(image_cube, threshold_abs=threshold,
                                                       footprint=np.ones((3,) * image_cube.ndim),
                                                       threshold_rel=0.0,
                                                       exclude_border=False)

    if local_maxima.size == 0:
        return np.empty((0, 3))
    lm = local_maxima.astype(np.float64)
    lm[:, -1] = sigma_list[local_maxima[:, -1]]
    return skimage.feature.blob._prune_blobs(lm, overlap)


def _estimate_scale(im, min_radius=20, max_radius=200, num_radii=10, thresholds=[0.01], inlier_tol=np.inf):
    """
    Estimates the scale of the image.
    """
    from superdsm.render import normalize_image

    sigma_list = np.linspace(min_radius, max_radius, num_radii) / math.sqrt(2)
    sigma_list = np.concatenate([[sigma_list.min() / 2], sigma_list])
    
    im_norm  = normalize_image(im)
    im_norm /= im_norm.max()

    blobs_mask  = {sigma: ndi.gaussian_laplace(im_norm, sigma) < 0 for sigma in sigma_list}
    mean_radius = None
    for threshold in sorted(thresholds, reverse=True):
        blobs_doh = _blob_doh(im_norm, sigma_list, threshold=threshold, mask=blobs_mask)
        blobs_doh = blobs_doh[~np.isclose(blobs_doh[:,2], sigma_list.min())]
        if len(blobs_doh) == 0: continue

        radii = blobs_doh[:,2] * math.sqrt(2)
        radii_median  = np.median(radii)
        radii_mad     = np.mean(np.abs(radii - np.median(radii)))
        radii_bound   = np.inf if np.isinf(inlier_tol) else radii_mad * inlier_tol
        radii_inliers = np.logical_and(radii >= radii_median - radii_mad, radii <= radii_median + radii_mad)
        mean_radius   = np.mean(radii[radii_inliers])
        break
    
    if mean_radius is None:
        raise ValueError('scale estimation failed')
    return mean_radius / math.sqrt(2), blobs_doh, radii_inliers
