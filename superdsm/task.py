import repype.config
import repype.stage
import repype.status
import repype.task
from repype.typing import (
    Pipeline,
    PipelineData,
)

import superdsm.pipeline


class Task(repype.task.Task):

    def create_pipeline(self, *args, **kwargs) -> Pipeline:
        return superdsm.pipeline.Pipeline(*args, **kwargs)
    
    def on_c2f_region_analysis_end(self, pipeline: Pipeline, data: PipelineData, **kwargs):
        # TODO: Write adjacencies image
        ...
    
    def on_global_energy_minimization_end(self, pipeline: Pipeline, data: PipelineData, **kwargs):
        # TODO: Write performance report
        ...
    
    def on_postprocess_end(self, pipeline: Pipeline, data: PipelineData, **kwargs):
        # TODO: Write segmentation masks
        # TODO: Write overlay image
        ...
