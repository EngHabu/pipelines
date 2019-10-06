#!/usr/bin/env python3

import kfp
from kfp import dsl


def echo_op(text):
    return dsl.ContainerOp(
        name='echo',
        image='library/bash:4.4.23',
        command=['sh', '-c'],
        arguments=['echo "$0"', text]
    )

@dsl.pipeline(
    name='Simple pipeline',
    description='A pipeline with two parallel steps that echo input strings.'
)
def simple_pipeline(input_a="abc", input_b="def"):
    """A pipeline with two parallel steps."""

    echo_task_a = echo_op(input_a)
    echo_task_b = echo_op(input_b)

if __name__ == '__main__':
    kfp.compiler.Compiler().compile(simple_pipeline, __file__ + '.zip')
