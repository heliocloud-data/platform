#!/bin/bash

kustomize build monitoring-storage/base | kubectl apply -f -
