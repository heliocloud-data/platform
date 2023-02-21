#!/usr/bin/env python3

import aws_cdk as cdk
from web_retrieval.web_retrieval_stack import WebRetrievalStack

app = cdk.App()
WebRetrievalStack(app, "WebRetrievalStack")

app.synth()
