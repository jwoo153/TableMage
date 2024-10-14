from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
from llama_index.core.indices.struct_store import JSONQueryEngine

from json import dumps

from ..tabularmagic_utils import GLOBAL_DATA_CONTAINER
from ..io.io import GLOBAL_IO


# Means test tool
class _TestEqualMeansInput(BaseModel):
    categorical_var: str = Field(
        description="The categorical variable that defines the groups/levels."
    )
    numeric_var: str = Field(
        description="The numeric variable to test between the groups/levels."
    )


def _test_equal_means_function(categorical_var: str, numeric_var: str) -> str:
    """Tests whether the means of a numeric variable are equal across the different
    levels of a categorical variable."""
    dict_output = str(
        GLOBAL_DATA_CONTAINER.analyzer.eda("all")
        .test_equal_means(numeric_var=numeric_var, stratify_by=categorical_var)
        ._to_dict()
    )
    return dumps(dict_output)


test_equal_means_tool = FunctionTool.from_defaults(
    fn=_test_equal_means_function,
    name="test_equal_means_tool",
    description="Tests whether the means of a numeric variable are equal across "
    "the different levels of a categorical variable. "
    "The null hypothesis is that the means are equal. "
    "Automatically determines the correct statistical test to conduct. "
    "Returns a JSON string containing the results.",
    fn_schema=_TestEqualMeansInput,
)


class _PlotDistributionInput(BaseModel):
    var: str = Field(description="The variable to plot the distribution of.")


def _plot_distribution_function(var: str) -> str:
    """Plots the distribution of a variable."""
    fig = GLOBAL_DATA_CONTAINER.analyzer.eda("all").plot_distribution(var)
    GLOBAL_IO.add_figure(fig, f"Distribution plot of variable: {var}.")
    return "A plot of the distribution has been saved to STORAGE."
