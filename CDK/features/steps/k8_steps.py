"""
Cucumber step definition file for kubernetes.
"""

# pylint: disable=missing-function-docstring
# pylint: disable=undefined-variable
# pylint: disable=unused-argument
# pylint: disable=unused-variable


@given('no existing {resource_type} named "{resource_name}" exists in namespace "{namespace}"')
def step_impl(context, namespace, resource_type, resource_name):
    cmd = f" kubectl --namespace {namespace} delete {resource_type}/{resource_name}"
    print("Run the k8 cmd: {cmd}")
