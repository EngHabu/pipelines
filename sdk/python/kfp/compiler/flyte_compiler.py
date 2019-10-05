import datetime
import inspect
import os
import re

import six
from flytekit.common import interface as interface_common
from flytekit.common import promise as promise_common, workflow as workflow_common
from flytekit.common.tasks import task as base_tasks
from flytekit.common.nodes import SdkNode
from flytekit.common.types import helpers as _type_helpers
from flytekit.models import interface as interface_model, task as task_model
from flytekit.models import literals as literals_model
from flytekit.models.workflow_closure import WorkflowClosure
from flytekit.sdk.types import Types
from flytekit.common.core import identifier as _identifier

from kfp import dsl
from kfp.compiler import Compiler

import json
from collections import defaultdict
import inspect
import tarfile
import zipfile
from typing import Callable, Set, List, Text, Dict, Tuple, Any, Union, Optional

from kfp.dsl import _for_loop

from .. import dsl
from ._k8s_helper import K8sHelper
from ._op_to_template import _op_to_template
from ._default_transformers import add_pod_env

from ..components._structures import InputSpec
from ..dsl._metadata import _extract_pipeline_metadata
from ..dsl._ops_group import OpsGroup

class FlyteCompiler(Compiler):
    """DSL Compiler.

    It compiles DSL pipeline functions into Flyte Workflow Template. Example usage:
    ```python
    @dsl.pipeline(
      name='name',
      description='description'
    )
    def my_pipeline(a: dsl.PipelineParam, b: dsl.PipelineParam):
      pass

    FlyteCompiler().compile(my_pipeline, 'path/to/workflow.yaml')
    ```
    """

    def _op_to_task(self, op, node_map):
        """Generate task given an operator inherited from dsl.ContainerOp."""

        interface_inputs = {}
        interface_outputs = {}
        input_mappings = {}
        processed_args = None
        if op.arguments:
            processed_args = list(map(str, op.arguments))
            for i, _ in enumerate(processed_args):
                if op.argument_inputs:
                    for param in op.argument_inputs:
                        full_name = self._param_full_name(param)
                        processed_args[i] = re.sub(str(param), '{{.inputs.%s}}' % full_name,
                                                   processed_args[i])
        for param in op.inputs:
            interface_inputs[param.name] = interface_model.Variable(
                _type_helpers.python_std_to_sdk_type(Types.String).to_flyte_literal_type(),
                ''
            )

            if not param.op_name or param.op_name == '':
                binding = promise_common.Input(sdk_type=Types.String, name=param.name)
            else:
                binding = promise_common.NodeOutput(
                    sdk_node=node_map[param.op_name],
                    sdk_type=Types.String,
                    var=param.name)
            input_mappings[param.name] = binding

        for param in op.outputs.values():
            interface_outputs[param.name] = interface_model.Variable(
                _type_helpers.python_std_to_sdk_type(Types.String).to_flyte_literal_type(),
                ''
            )

        requests = []
        if op.container.resources and op.container.resources.cpu_request:
            requests.append(
                task_model.Resources.ResourceEntry(
                    task_model.Resources.ResourceName.CPU,
                    op.container.resources.cpu_request
                )
            )

        if op.container.resources and op.container.resources.memory_request:
            requests.append(
                task_model.Resources.ResourceEntry(
                    task_model.Resources.ResourceName.MEMORY,
                    op.container.resources.memory_request
                )
            )

        limits = []
        if op.container.resources and op.container.resources.cpu_limit:
            limits.append(
                task_model.Resources.ResourceEntry(
                    task_model.Resources.ResourceName.CPU,
                    op.container.resources.cpu_limit
                )
            )
        if op.container.resources and op.container.resources.memory_limit:
            limits.append(
                task_model.Resources.ResourceEntry(
                    task_model.Resources.ResourceName.MEMORY,
                    op.container.resources.memory_limit
                )
            )

        task = base_tasks.SdkTask(
            "container_op",
            metadata=task_model.TaskMetadata(
                discoverable=False,
                runtime=task_model.RuntimeMetadata(
                    type=task_model.RuntimeMetadata.RuntimeType.OTHER,
                    version='1.0',
                    flavor='kf'
                ),
                timeout=datetime.timedelta(seconds=0),
                retries=literals_model.RetryStrategy(0),
                discovery_version='1',
                deprecated_error_message=None,
            ),
            interface=interface_common.TypedInterface(inputs=interface_inputs, outputs=interface_outputs),
            custom=None,
            container=task_model.Container(
                image=op.image,
                command=op.command,
                args=processed_args,
                resources=task_model.Resources(limits=limits, requests=requests),
                env={},
                config={},
            )
        )

        # HACK to fix the project and domain. Ideally this should be a parameter
        task._id = _identifier.Identifier(
            task.id.resource_type,
            "flyteexamples",
            "development",
            op.name,
            "1",
        )

        return task, task(**input_mappings).assign_id_and_return(op.name)

    def _create_tasks(self, pipeline):
        tasks = set()
        nodes = {}
        for op in pipeline.ops.values():
            task, node = self._op_to_task(op, nodes)
            tasks.add(task)
            nodes[node.id] = node
        return tasks, [v for k, v in six.iteritems(nodes)]

    def _create_pipeline_workflow(self, args, pipeline) -> WorkflowClosure:
        """Create workflow for the pipeline."""

        wf_inputs = []
        for arg in args:
            default_value = ''
            if arg.value is not None:
                default_value = str(arg.value)
            wf_inputs.append(promise_common.Input(name=arg.name, sdk_type=Types.String, default=default_value,
                                                  help='Not required input.'))

        tasks, nodes = self._create_tasks(pipeline)

        # Create map to look up tasks by their fully-qualified name. This map goes from something like
        # app.workflows.MyWorkflow.task_one to the task_one SdkRunnable task object
        tmap = {}
        for t in tasks:
            # TODO Maybe we just call register here?
            # This mocks an Admin registration, setting the reference id to the name of the task itself
            tmap[t.id] = t

        w = workflow_common.SdkWorkflow(inputs=wf_inputs, outputs={}, nodes=nodes)
        task_templates = []
        for n in w.nodes:
            if n.task_node is not None:
                task_templates.append(tmap[n.task_node.reference_id])
            elif n.workflow_node is not None:
                n.workflow_node.launchplan_ref = n.workflow_node.id
                n.workflow_node.sub_workflow_ref = n.workflow_node.id

        # Create the WorkflowClosure object that wraps both the workflow and its tasks
        return WorkflowClosure(workflow=w, tasks=task_templates)

    def _compile(self, pipeline_func: Callable,
      pipeline_name: Text=None,
      pipeline_description: Text=None,
      params_list: List[dsl.PipelineParam]=None,
      pipeline_conf: dsl.PipelineConf = None,
      ) -> WorkflowClosure:
        """ Internal implementation of create_workflow."""
        params_list = params_list or []
        argspec = inspect.getfullargspec(pipeline_func)

        # Create the arg list with no default values and call pipeline function.
        # Assign type information to the PipelineParam
        pipeline_meta = _extract_pipeline_metadata(pipeline_func)
        pipeline_meta.name = pipeline_name or pipeline_meta.name
        pipeline_meta.description = pipeline_description or pipeline_meta.description
        pipeline_name = K8sHelper.sanitize_k8s_name(pipeline_meta.name)

        # Need to first clear the default value of dsl.PipelineParams. Otherwise, it
        # will be resolved immediately in place when being to each component.
        default_param_values = {}
        for param in params_list:
            default_param_values[param.name] = param.value
            param.value = None

        # Currently only allow specifying pipeline params at one place.
        if params_list and pipeline_meta.inputs:
            raise ValueError('Either specify pipeline params in the pipeline function, or in "params_list", but not both.')


        args_list = []
        for arg_name in argspec.args:
            arg_type = None
            for input in pipeline_meta.inputs or []:
                if arg_name == input.name:
                    arg_type = input.type
                break
            args_list.append(dsl.PipelineParam(K8sHelper.sanitize_k8s_name(arg_name), param_type=arg_type))

        with dsl.Pipeline(pipeline_name) as dsl_pipeline:
            pipeline_func(*args_list)

        pipeline_conf = pipeline_conf or dsl_pipeline.conf # Configuration passed to the compiler is overriding. Unfortunately, it's not trivial to detect whether the dsl_pipeline.conf was ever modified.

        self._validate_exit_handler(dsl_pipeline)
        self._sanitize_and_inject_artifact(dsl_pipeline, pipeline_conf)

        # Fill in the default values.
        args_list_with_defaults = []
        if pipeline_meta.inputs:
            args_list_with_defaults = [dsl.PipelineParam(K8sHelper.sanitize_k8s_name(arg_name))
                                        for arg_name in argspec.args]
            if argspec.defaults:
                for arg, default in zip(reversed(args_list_with_defaults), reversed(argspec.defaults)):
                    arg.value = default.value if isinstance(default, dsl.PipelineParam) else default
        elif params_list:
            # Or, if args are provided by params_list, fill in pipeline_meta.
            for param in params_list:
                param.value = default_param_values[param.name]

            args_list_with_defaults = params_list
            pipeline_meta.inputs = [
                InputSpec(
                    name=param.name,
                    type=param.param_type,
                    default=param.value) for param in params_list]

        op_transformers = [add_pod_env]
        op_transformers.extend(pipeline_conf.op_transformers)

        return self._create_pipeline_workflow(args_list_with_defaults, dsl_pipeline)

    def compile(self, pipeline_func, package_path):
        """Compile the given pipeline function into workflow yaml.

        Args:
          pipeline_func: pipeline functions with @dsl.pipeline decorator.
          package_path: the output workflow tar.gz file path. for example, "~/a.tar.gz"
        """
        workflow = self._compile(pipeline_func)
        file_name = os.path.join(package_path, '{}.pb'.format(workflow.workflow.id))
        with open(file_name, 'wb') as fd:
            fd.write(workflow.to_flyte_idl().SerializeToString())
        print(file_name)

    def register(self, pipeline_func, version: str):
        w = self._compile(pipeline_func)
        for t in w.tasks:
            print(t.register("flyteexamples", "development", t._id.name, version))
        print(w.workflow.register("flyteexamples", "development", "test_workflow", "v1"))
