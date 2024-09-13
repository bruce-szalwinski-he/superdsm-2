import repype.config
import repype.stage
import repype.status
import repype.task
from repype.typing import (
    Pipeline,
    PipelineData,
)

import superdsm.pipeline
import superdsm.render
import superdsm.io


class Task(repype.task.Task):

    def create_pipeline(self, *args, **kwargs) -> Pipeline:
        return superdsm.pipeline.Pipeline(*args, **kwargs)
    
    def on_c2f_region_analysis_end(self, pipeline: Pipeline, data: PipelineData, **kwargs):
        # TODO: Write adjacencies image
        ...
        adj_filepath = pipeline.resolve('adjacencies', input_id)
        if adj_filepath is not None:
            ymap = superdsm.render.render_ymap(data)
            ymap = superdsm.render.render_atoms(data, override_img=ymap, border_color=(0,0,0), border_radius=1)
            img  = superdsm.render.render_adjacencies(data, override_img=ymap, edge_color=(0,1,0), endpoint_color=(0,1,0))
            superdsm.io.imsave(adj_filepath, img)
    
    def on_global_energy_minimization_end(self, pipeline: Pipeline, data: PipelineData, **kwargs):
        # TODO: Write performance report
        ...
    
    def on_postprocess_end(self, pipeline: Pipeline, data: PipelineData, **kwargs):
        # TODO: Write segmentation masks
        # TODO: Write overlay image
        ...
