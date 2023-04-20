# from google.cloud import aiplatform as aip

from kfp import dsl
from kfp import compiler
from kfp.components import load_component_from_url
# from google_cloud_pipeline_components.v1.endpoint import (EndpointCreateOp,
#                                                               ModelDeployOp)
from google_cloud_pipeline_components.v1.model import ModelUploadOp

from pipeline_components import (
    perform_eda,
    train,
)

import os
from dotenv import load_dotenv

load_dotenv()

kserve = load_component_from_url("https://raw.githubusercontent.com/kubeflow/pipelines/56edebb646ca471409a24addc40ab1c040f9fa1a/components/kserve/component.yaml")

PROJECT_ID = os.getenv("PROJECT_ID")
# REGION = os.getenv("REGION")
DEST_BUCKET_URI = os.getenv("DEST_BUCKET_URI")
SOURCE_FILE = os.getenv("SOURCE_FILE")
# PIPELINE_BUCKET_URI = os.getenv("PIPELINE_BUCKET_URI")
# SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT")

# API service endpoint
# API_ENDPOINT = "{}-aiplatform.googleapis.com".format(REGION)
# PIPELINE_ROOT = "{}/pipeline_root/intro".format(PIPELINE_BUCKET_URI)
# print(f"PIPELINE_ROOT DEBUG: {PIPELINE_ROOT}")

@dsl.pipeline(
    name="churn-prediction-pipeline",
    description="Getting churn predictions"
)
def pipeline(dest_bucket_uri: str, source_file: str, ):

    # TODO: get just the run id number from this string
    # run_id = dsl.PIPELINE_JOB_NAME_PLACEHOLDER.split("-")[-1]
    
    # input_data_task = (
    #     ingest_data(source_bucket_uri = source_bucket_uri).
    #     set_cpu_limit('1').
    #     set_memory_limit('3G').
    #     set_display_name("Ingest Data")
    # )

    model_uri=f"gcs://{dest_bucket_uri}/model_file"
    
    perform_eda_task = (
        perform_eda(run_id = "run_id_1", 
                    dest_bucket_uri = dest_bucket_uri,
                    source_file = source_file).\
            set_cpu_limit('1').\
            set_memory_limit('3G').\
            set_display_name("Ingest Data & Perform EDA")#.\
    )
    
    train_task = train(run_id = "run_id_2", 
          dest_bucket_uri = dest_bucket_uri, 
          source_file = source_file).\
        set_display_name("Train Models").\
        after(perform_eda_task)
    
    model_upload_op = ModelUploadOp(
        project=PROJECT_ID,
        display_name='model_upload',
        unmanaged_container_model=dest_bucket_uri,
    )
    model_upload_op.after(train_task)

    model_uri = str(model_uri)
    # pylint: disable=unused-variable
    isvc_yaml = """
    apiVersion: "serving.kserve.io/v1beta1"
    kind: "InferenceService"
    metadata:
      name: "model-deploy"
      namespace: "kubeflow-user-example-com"
    spec:
      predictor:
        serviceAccountName: sa
        pytorch:
          protocolVersion: v2
          storageUri: {}
          resources:
            requests: 
              cpu: 4
              memory: 8Gi
            limits:
              cpu: 4
              memory: 8Gi
    """.format(model_uri)

    deploy_task = kserve(action="apply", inferenceservice_yaml=isvc_yaml
                 ).after(model_upload_op).set_display_name("Deployer")
    
    # endpoint_create_op = EndpointCreateOp(
    #     project=PROJECT_ID,
    #     display_name="pipelines-created-endpoint",
    # ).after(model_upload_op)

    # ModelDeployOp(
    #     endpoint=endpoint_create_op.outputs["endpoint"],
    #     model=model_upload_op.outputs["model"],
    #     deployed_model_display_name='model_deploy',
    #     dedicated_resources_machine_type="n1-standard-16",
    #     dedicated_resources_min_replica_count=1,
    #     dedicated_resources_max_replica_count=1,
    # ).after(endpoint_create_op)


if __name__=="__main__":


    # aip.init(project=PROJECT_ID, staging_bucket=PIPELINE_BUCKET_URI)

    # compiler.Compiler().compile(pipeline_func=pipeline, package_path="churn_pipeline.json")
    compiler.Compiler().compile(pipeline, 'pipeline.tar.gz', type_check=True)

    # clean up
    # training triger input 
    # deploy - scheduled (?) trigger POSTMAN