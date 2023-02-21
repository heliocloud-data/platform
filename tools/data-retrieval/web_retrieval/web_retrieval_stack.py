from constructs import Construct

from aws_cdk import (
    aws_lambda as lambda_,
    aws_lambda_python_alpha as lambda_alpha,
    aws_s3 as s3_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_s3_notifications,
    Stack,
    Duration,
    Size
)


class WebRetrievalStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ############
        # Makes S3 bucket with given id
        s3_save_data = s3_.Bucket(self, 's3_save_data')

        ############

        # Lambdas data upload step function
        check_file_registry_lambda = lambda_.Function(self, "check_file_registry_lambda",
                                                      runtime=lambda_.Runtime.PYTHON_3_9,
                                                      handler="check_file_registry.lambda_handler",
                                                      code=lambda_.Code.from_asset(
                                                          "./web_retrieval/lambdas"),
                                                      timeout=Duration.minutes(10))

        data_load_parse_small_lambda = lambda_alpha.PythonFunction(self, "data_load_parse_small_lambda",
                                                                   entry='./web_retrieval/lambdas/load_files',
                                                                   index='data_load_parse_small.py',
                                                                   runtime=lambda_.Runtime.PYTHON_3_9,
                                                                   handler="lambda_handler",
                                                                   timeout=Duration.minutes(10),
                                                                   memory_size=256,
                                                                   ephemeral_storage_size=Size.mebibytes(512))

        data_load_parse_medium_lambda = lambda_alpha.PythonFunction(self, "data_load_parse_medium_lambda",
                                                                    entry='./web_retrieval/lambdas/load_files',
                                                                    index='data_load_parse_medium.py',
                                                                    runtime=lambda_.Runtime.PYTHON_3_9,
                                                                    handler="lambda_handler",
                                                                    timeout=Duration.minutes(
                                                                        10),
                                                                    memory_size=512,
                                                                    ephemeral_storage_size=Size.mebibytes(1024))

        data_load_parse_large_lambda = lambda_alpha.PythonFunction(self, "data_load_parse_large_lambda",
                                                                   entry='./web_retrieval/lambdas/load_files',
                                                                   index='data_load_parse_large.py',
                                                                   runtime=lambda_.Runtime.PYTHON_3_9,
                                                                   handler="lambda_handler",
                                                                   timeout=Duration.minutes(
                                                                       10),
                                                                   memory_size=512,
                                                                   ephemeral_storage_size=Size.mebibytes(4096))

        log_failures_lambda = lambda_.Function(self, "log_failures_lambda",
                                               runtime=lambda_.Runtime.PYTHON_3_9,
                                               handler="log_failures.lambda_handler",
                                               code=lambda_.Code.from_asset("./web_retrieval/lambdas"))

        # Task definitions for data upload
        succeed_job = sfn.Succeed(self, "Successful Job")

        failed_job = sfn.Fail(self, "Failed Job",
                              cause="Failed Job", error="did not parse chunk")

        check_registry_job = sfn_tasks.LambdaInvoke(self, "check registry Job",
                                                    lambda_function=check_file_registry_lambda,
                                                    output_path="$.Payload")

        log_failures_job = sfn_tasks.LambdaInvoke(self, "log failures Job",
                                                  lambda_function=log_failures_lambda,
                                                  output_path="$.Payload").next(failed_job)

        data_load_parse_large_job = sfn_tasks.LambdaInvoke(self, "data load parse large Job",
                                                           lambda_function=data_load_parse_large_lambda,
                                                           output_path="$.Payload")
        data_load_parse_large_job.add_catch(
            result_path="$.error", handler=log_failures_job).next(succeed_job)

        data_load_parse_medium_job = sfn_tasks.LambdaInvoke(self, "data load parse medium Job",
                                                            lambda_function=data_load_parse_medium_lambda,
                                                            output_path="$.Payload")
        data_load_parse_medium_job.add_catch(
            result_path="$.error", handler=data_load_parse_large_job).next(succeed_job)

        data_load_parse_small_job = sfn_tasks.LambdaInvoke(self, "data load parse small Job",
                                                           lambda_function=data_load_parse_small_lambda,
                                                           output_path="$.Payload")
        data_load_parse_small_job.add_catch(
            result_path="$.error", handler=data_load_parse_medium_job).next(succeed_job)

        data_upload_definition = check_registry_job.next(
            data_load_parse_small_job)

        data_upload_sm = sfn.StateMachine(self, 'Data Upload SM',
                                          definition=data_upload_definition,
                                          timeout=Duration.seconds(30))

        ############

        # Lambdas for start full pipeline step functions
        chunk_file_lambda = lambda_alpha.PythonFunction(self, "chunk_file_lambda",
                                                        entry='./web_retrieval/lambdas/chunk_files',
                                                        index='chunk_file.py',
                                                        runtime=lambda_.Runtime.PYTHON_3_9,
                                                        handler="lambda_handler",
                                                        timeout=Duration.minutes(10))

        make_upload_lambda = lambda_alpha.PythonFunction(self, "make_upload_lambda",
                                                         entry='./web_retrieval/lambdas/chunk_files',
                                                         index='make_upload_json.py',
                                                         environment={
                                                             'SAVE_S3_BUCKET': s3_save_data.bucket_name},
                                                         runtime=lambda_.Runtime.PYTHON_3_9,
                                                         handler="lambda_handler")

        # Step Function tasks

        # Include the state machine in a Task state with callback pattern
        data_upload_sm_job = sfn_tasks.StepFunctionsStartExecution(self, "data upload sm job",
                                                                   state_machine=data_upload_sm,
                                                                   input=sfn.TaskInput.from_object({
                                                                       "AWS_STEP_FUNCTIONS_STARTED_BY_EXECUTION_ID.$": "$$.Execution.Id",
                                                                       "Payload.$": "$"
                                                                   }),
                                                                   name="MyExecutionName"
                                                                   )

        next_step_function_job = sfn.Map(self, "Test step function",
                                         max_concurrency=5,
                                         items_path=sfn.JsonPath.string_at("$.upload_reqs"))
        next_step_function_job.iterator(data_upload_sm_job)

        chunk_file_job = sfn_tasks.LambdaInvoke(self, "chunk file Job",
                                                lambda_function=chunk_file_lambda,
                                                output_path="$.Payload")

        make_upload_job = sfn_tasks.LambdaInvoke(self, "make upload Job",
                                                 lambda_function=make_upload_lambda,
                                                 output_path="$.Payload")

        chunk_manifest_job = sfn.Map(self, "Chunk Manifest",
                                     max_concurrency=1,
                                     items_path=sfn.JsonPath.string_at("$.chunked_files"))
        chunk_manifest_job.iterator(
            make_upload_job.next(next_step_function_job))

        full_pipeline_definition = chunk_file_job.next(chunk_manifest_job)

        # Step function to kick off full pipeline
        full_pipeline_sm = sfn.StateMachine(self, "Full processing pipeline",
                                            definition=full_pipeline_definition
                                            )

        # TODO add back in SNS publish state at the end

        ############

        # Create S3 bucket with notifications that invoke a lambda (which starts step function)
        start_full_pipeline_function = lambda_.Function(self, "start_full_pipeline_function",
                                                        runtime=lambda_.Runtime.PYTHON_3_9,
                                                        handler="start_full_pipeline.lambda_handler",
                                                        code=lambda_.Code.from_asset(
                                                            "./web_retrieval/lambdas"),
                                                        environment={
                                                            'STEPFUNCTION_ARN': full_pipeline_sm.state_machine_arn},
                                                        timeout=Duration.seconds(3))

        #############

        # Makes S3 bucket with given id
        s3_manifest = s3_.Bucket(self, 'upload_manifest')

        # Give lambda IAM permissions to start execution on state machine
        full_pipeline_sm.grant_start_execution(start_full_pipeline_function)

        # Create an S3 notification that when event occurs will start Lambda
        reprocessing_notification = aws_s3_notifications.LambdaDestination(
            start_full_pipeline_function)

        # Makes a notification on the S3 bucket when there is an object added that calls lambda
        # Structure of event notification here: https://docs.aws.amazon.com/AmazonS3/latest/userguide/notification-content-structure.html
        s3_manifest.add_event_notification(
            s3_.EventType.OBJECT_CREATED, reprocessing_notification)

        s3_manifest.grant_read(start_full_pipeline_function)
        s3_manifest.grant_read_write(chunk_file_lambda)

        s3_manifest.grant_read(make_upload_lambda)

        ############
        s3_save_data.grant_read_write(check_file_registry_lambda)
        s3_save_data.grant_read_write(data_load_parse_small_lambda)
        s3_save_data.grant_read_write(data_load_parse_medium_lambda)
        s3_save_data.grant_read_write(data_load_parse_large_lambda)
