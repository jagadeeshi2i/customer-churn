from kfp.dsl import component
from kfp import components
from kfp.components import create_component_from_func
########################################################################################
# Lightweight Componenents
########################################################################################
# @component(
#     base_image='python:3.8-slim', # Optional
#     packages_to_install=['pandas==1.2.4', "gcsfs", "fsspec"], # Optional
#     # output_component_file='add.component.yaml', # Optional
#     # pip_index_urls = [] 
# )
# def ingest_data(source_bucket_uri: str) -> None:
#     import logging
#     import sys

#     import pandas as pd 

#     logging.basicConfig(stream = sys.stdout)
#     logger = logging.getLogger("churn")
#     logger.setLevel("INFO")

#     logging.info("Test to see if logging works")

#     df = pd.read_csv(f"gs://{source_bucket_uri}/bank_data.csv",)
#     logging.info(f"{df.shape}")

#     return

# ingest_data_op = components.func_to_container_op(
#     func=ingest_data,
#     base_image='python:3.8-slim', # Optional
#     packages_to_install=['pandas==1.2.4'], # Optional
#     # output_component_file='add.component.yaml', # Optional
#     pip_index_urls = [] # Optional, default is PyPI
# )

def perform_eda(run_id: str, dest_bucket_uri: str, source_file: str) -> None:
    '''
    perform eda on df and save figures to images folder
    input:
            df: pandas dataframe
    output:
            None
    '''
    import io
    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns

    from google.cloud import storage

    import logging
    import sys
    # set up logging
    logging.basicConfig(stream = sys.stdout)
    logger = logging.getLogger("churn")
    logger.setLevel("INFO")

    def save_plot_to_gcs(plot, dest_bucket_uri, plot_name):
        buf = io.BytesIO()
        plot.savefig(buf, format='png')

        # init GCS client and upload buffer contents
        client = storage.Client()
        bucket = client.get_bucket(dest_bucket_uri[5:])
        blob = bucket.blob(f'{run_id}/plots/{plot_name}.png')
        blob.upload_from_file(buf, content_type='image/png', rewind=True)
        return 
    
    df = pd.read_csv(source_file)
    logging.info(f"Pipeline Run ID: {run_id}")
    logging.info(f"Read in input data; Shape: {df.shape}")

    fig = plt.figure(figsize=(20,10)) 
    df['Churn'] = df['Attrition_Flag'].apply(lambda val: 0 if val == "Existing Customer" else 1)
    df['Churn'].hist()
    fig_to_upload = plt.gcf()
    save_plot_to_gcs(plot = fig_to_upload, dest_bucket_uri=dest_bucket_uri, plot_name = "first_plot")
    # plt.savefig('./images/eda/churn_histogram')

    return

    # plt.figure(figsize=(20,10)) 
    # df['Customer_Age'].hist()
    # plt.savefig('./images/eda/age_histogram')

    
    # plt.figure(figsize=(20,10)) 
    # df.Marital_Status.value_counts('normalize').plot(kind='bar')
    # plt.savefig('./images/eda/marital_status_bins')

    # plt.figure(figsize=(20,10)) 
    #     # distplot is deprecated. Use histplot instead
    #     # sns.distplot(df['Total_Trans_Ct']);
    #     # Show distributions of 'Total_Trans_Ct' and add a smooth curve obtained using a kernel density estimate
    # sns.histplot(df['Total_Trans_Ct'], stat='density', kde=True)
    # plt.savefig('./images/eda/total_trans_ct_histogram_density_plot')
    
    # plt.figure(figsize=(20,10)) 
    # sns.heatmap(df.corr(), annot=False, cmap='Dark2_r', linewidths = 2)
    # plt.savefig('./images/eda/variable_heatmap')

# perform_eda_op = components.func_to_container_op(
#     func=perform_eda,
#     base_image='python:3.8-slim', # Optional
#     packages_to_install=['pandas==1.2.4', "matplotlib==3.3.4", "seaborn==0.11.2"], # Optional
#     # output_component_file='add.component.yaml', # Optional
#     # pip_index_urls = [] # Optional, default is PyPI
# )

train = components.load_component_from_file("training/component.yaml")
perform_eda = create_component_from_func(
    perform_eda,
    base_image='python:3.8',
    packages_to_install=['pandas==1.2.4', "gcsfs", "fsspec", "matplotlib==3.3.4", "seaborn==0.11.2"], # Optional
    output_component_file='eda_component.yaml')

########################################################################################

########################################################################################

# kfp.components.load_component_from_file('comp_typed.yaml')
if __name__=="__main__":
    pass