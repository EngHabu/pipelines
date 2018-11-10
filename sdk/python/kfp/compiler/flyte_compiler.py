import datetime
import inspect
import os
import re

import six
from flyteidl.core.tasks_pb2 import SingleStepTask
from flytekit.common import interface as interface_common
from flytekit.common import promise as promise_common, workflow as workflow_common
from flytekit.common.tasks import task as base_tasks
from flytekit.common.types import helpers as _type_helpers
from flytekit.models import interface as interface_model, task as task_model
from flytekit.models import literals as literals_model
from flytekit.models.workflow_closure import WorkflowClosure
from flytekit.sdk.types import Types

from kfp import dsl
from kfp.compiler import Compiler


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

      if param.op_name == '':
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
    if op.cpu_request:
      requests.append(
        task_model.Resources.ResourceEntry(
          task_model.Resources.ResourceName.Cpu,
          op.cpu_request
        )
      )

    if op.memory_request:
      requests.append(
        task_model.Resources.ResourceEntry(
          task_model.Resources.ResourceName.Memory,
          op.memory_request
        )
      )

    limits = []
    if op.cpu_limit:
      limits.append(
        task_model.Resources.ResourceEntry(
          task_model.Resources.ResourceName.Cpu,
          op.cpu_limit
        )
      )
    if op.memory_limit:
      limits.append(
        task_model.Resources.ResourceEntry(
          task_model.Resources.ResourceName.Memory,
          op.memory_limit
        )
      )

    task = base_tasks.SdkTask(
      op.name,
      SingleStepTask,
      "container_op",
      task_model.TaskMetadata(
        False,
        task_model.RuntimeMetadata(
          type=task_model.RuntimeMetadata.RuntimeType.Other,
          version='1.0',
          flavor='kf'
        ),
        datetime.timedelta(seconds=0),
        literals_model.RetryStrategy(0),
        '1',
        None,
      ),
      interface_common.TypedInterface(inputs=interface_inputs, outputs=interface_outputs),
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

    return task, task(**input_mappings).assign_id_and_return(op.name)

  def _create_tasks(self, pipeline):
    tasks = set()
    nodes = {}
    for op in pipeline.ops.values():
      task, node = self._op_to_task(op, nodes)
      tasks.add(task)
      nodes[node.id] = node
    return tasks, [v for k, v in six.iteritems(nodes)]

  def _create_pipeline_workflow(self, args, pipeline):
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
      # This mocks an Admin registration, setting the reference id to the name of the task itself
      t.target._reference_id = t.id
      tmap[t.id] = t

    w = workflow_common.SdkWorkflow(workflow_id=pipeline.name, inputs=wf_inputs, outputs={}, nodes=nodes)
    task_templates = []
    for n in w.nodes:
      if n.task_node is not None:
        task_templates.append(tmap[n.task_node.reference_id])
      elif n.workflow_node is not None:
        n.workflow_node.launchplan_ref = n.workflow_node.id
        n.workflow_node.sub_workflow_ref = n.workflow_node.id

    # Create the WorkflowClosure object that wraps both the workflow and its tasks
    return WorkflowClosure(workflow=w, tasks=task_templates)

  def _compile(self, pipeline_func):
    """

    :param pipeline_func:
    :rtype: flytekit.models.workflow_closure
    """
    argspec = inspect.getfullargspec(pipeline_func)
    self._validate_args(argspec)

    registered_pipeline_functions = dsl.Pipeline.get_pipeline_functions()
    if pipeline_func not in registered_pipeline_functions:
      raise ValueError('Please use a function with @dsl.pipeline decorator.')

    pipeline_name, _ = dsl.Pipeline.get_pipeline_functions()[pipeline_func]
    pipeline_name = self._sanitize_name(pipeline_name)

    # Create the arg list with no default values and call pipeline function.
    args_list = [dsl.PipelineParam(self._sanitize_name(arg_name))
                 for arg_name in argspec.args]
    with dsl.Pipeline(pipeline_name) as p:
      pipeline_func(*args_list)

    # Remove when argo supports local exit handler.
    # self._validate_exit_handler(p)

    # Fill in the default values.
    args_list_with_defaults = [dsl.PipelineParam(self._sanitize_name(arg_name))
                               for arg_name in argspec.args]
    if argspec.defaults:
      for arg, default in zip(reversed(args_list_with_defaults), reversed(argspec.defaults)):
        arg.value = default.value

    return self._create_pipeline_workflow(args_list_with_defaults, p)

  def compile(self, pipeline_func, package_path):
    """Compile the given pipeline function into workflow yaml.

    Args:
      pipeline_func: pipeline functions with @dsl.pipeline decorator.
      package_path: the output workflow tar.gz file path. for example, "~/a.tar.gz"
    """
    workflow = self._compile(pipeline_func)
    file_name = os.path.join(package_path, 'output.pb')
    with open(file_name, 'wb') as fd:
      fd.write(workflow.to_flyte_idl().SerializeToString())
    print(file_name)
