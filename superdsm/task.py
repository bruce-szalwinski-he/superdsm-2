import csv
import os

import ray
import repype.config
import repype.stage
import repype.status
import repype.task
from repype.typing import (
    InputID,
    Pipeline,
    PipelineData,
)

import superdsm.globalenergymin
import superdsm.io
import superdsm.pipeline
import superdsm.render


def _write_performance_report(task_path, performance_path, data, overall_performance):
    file_ids = data.keys()
    properties = [
        'direct_solution_success',
        'iterative_pruning_success',
        'overall_pruning_success',
        'nontrivial_pruning_success',
    ]
    fields = superdsm.globalenergymin.PerformanceReport.attributes + properties
    rows = [[str(task_path)], ['ID'] + fields]

    def get_row(prefix, performance):
        return [prefix] + [getattr(performance, field) for field in fields]

    for file_id in file_ids:
        row = get_row(str(file_id), data[file_id]['performance'])
        rows.append(row)
    footer_row = get_row('', overall_performance)
    rows.append(footer_row)
    with open(str(performance_path), 'w', newline='') as fout:
        csv_writer = csv.writer(fout, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            csv_writer.writerow(row)


class Task(repype.task.Task):

    def create_pipeline(self, *args, **kwargs) -> Pipeline:
        scopes = self.full_spec.get('scopes', dict())
        scopes = {key: self.resolve_path(value) for key, value in scopes.items()}
        return superdsm.pipeline.Pipeline(*args, scopes=scopes, **kwargs)

    def run(self, *args, **kwargs) -> repype.task.TaskData:
        ray.init(num_cpus=int(os.environ.get('SUPERDSM_NUM_CPUS', 2)), log_to_driver=False, logging_level='error')
        data = super().run(*args, **kwargs)

        # Aggregate performance report
        performance = superdsm.globalenergymin.PerformanceReport()
        for file_id in data.keys():
            if 'performance' in data[file_id]:
                performance += data[file_id]['performance']

        # Write performance report
        _write_performance_report(self.path, self.path.resolve() / 'performance.csv', data, performance)

        return data

    def on_c2f_region_analysis_end(self, pipeline: Pipeline, input_id: InputID, data: PipelineData, **kwargs):
        # Write adjacencies image
        adj_filepath = pipeline.resolve('adjacencies', input_id)
        if adj_filepath is not None:
            ymap = superdsm.render.render_ymap(data)
            ymap = superdsm.render.render_atoms(data, override_img=ymap, border_color=(0, 0, 0), border_radius=1)
            img  = superdsm.render.render_adjacencies(
                data,
                override_img=ymap,
                edge_color=(0, 1, 0),
                endpoint_color=(0, 1, 0),
            )
            adj_filepath.parent.mkdir(parents=True, exist_ok=True)
            superdsm.io.imsave(adj_filepath, img)

    def on_postprocess_end(self, pipeline: Pipeline, input_id: InputID, data: PipelineData, **kwargs):
        # Write segmentation masks
        seg_filepath = pipeline.resolve('masks', input_id)
        if seg_filepath is not None:
            seg_result = superdsm.render.rasterize_labels(data)
            seg_filepath.parent.mkdir(parents=True, exist_ok=True)
            superdsm.io.imsave(seg_filepath, seg_result)

        # Write overlay image
        overlay_filepath = pipeline.resolve('overlays', input_id)
        if overlay_filepath is not None:
            img_overlay = superdsm.render.render_result_over_image(
                data,
                border_width=self.full_spec.get('overlay_border', 8),
            )
            overlay_filepath.parent.mkdir(parents=True, exist_ok=True)
            superdsm.io.imsave(overlay_filepath, img_overlay)
