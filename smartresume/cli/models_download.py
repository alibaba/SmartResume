import os
import sys

import click
from loguru import logger


project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)


@click.command(
    help="Download SmartResume model files from ModelScope or HuggingFace."
)
@click.option(
    "-s",
    "--source",
    "model_source",
    type=click.Choice(["modelscope", "huggingface"]),
    help="The source of the model repository",
    default=None,
)
@click.option(
    "-m",
    "--model_type",
    "model_type",
    type=click.Choice(["llm", "layout", "all"]),
    help="The type of the model to download",
    default=None,
)
@click.option(
    "--force",
    "force_download",
    is_flag=True,
    help="Force download even if model exists locally",
    default=False,
)
def download_models(model_source, model_type, force_download):
    from smartresume.utils.models_download_utils import download_model
    from smartresume.utils.model_paths import ModelType, ModelSource

    if model_source is None:
        model_source = click.prompt(
            "Please select the model download source: ",
            type=click.Choice(["modelscope", "huggingface"]),
            default="modelscope",
        )

    if model_type is None:
        model_type = click.prompt(
            "Please select the model type to download: ",
            type=click.Choice(["llm", "layout", "all"]),
            default="all",
        )

    model_source_enum = ModelSource(model_source)
    model_type_enum = ModelType(model_type)

    logger.info(f"Downloading {model_type} model from {model_source}...")

    try:
        if model_type_enum == ModelType.ALL:

            llm_path = download_model(ModelType.LLM, model_source_enum)
            layout_path = download_model(ModelType.LAYOUT, model_source_enum)
            logger.info("All models downloaded successfully!")
            logger.info(f"LLM model: {llm_path}")
            logger.info(f"Layout model: {layout_path}")
        else:

            model_path = download_model(model_type_enum, model_source_enum)
            logger.info(
                f"{model_type} model downloaded successfully to: {model_path}"
            )

    except Exception as e:
        logger.exception(
            f"An error occurred while downloading models: {str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    download_models()
