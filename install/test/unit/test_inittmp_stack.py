import aws_cdk as core
import aws_cdk.assertions as assertions

from inittmp.inittmp_stack import InittmpStack

# example test. To run these test, uncomment this file along with the example
# resource in inittmp/inittmp_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = InittmpStack(app, "inittmp")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
