#!/bin/bash

kustomize build portal/overlays/production | kubectl apply -f -
