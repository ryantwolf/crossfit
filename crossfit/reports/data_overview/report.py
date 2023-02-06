import functools as ft

import numpy as np

from crossfit.reports.base import Report
from crossfit.calculate.aggregate import Aggregator
from crossfit.metrics.common import CommonStats
from crossfit.metrics.continuous.range import Range
from crossfit.metrics.continuous.moments import Moments
from crossfit.metrics.categorical.str_len import MeanStrLength
from crossfit.metrics.categorical.value_counts import ValueCounts
from crossfit.reports.data_overview.visualization.facets import (
    visualize,
    FacetsOverview,
)

from crossfit.backends.dask.aggregate import aggregate


class ContinuousMetrics(Aggregator):
    def prepare(self, array):
        return {
            "range": Range(axis=self.axis)(array),
            "moments": Moments(axis=self.axis)(array),
            "common_stats": CommonStats()(array),
        }


def is_continuous(col) -> bool:
    return np.issubdtype(col.dtype, np.number)


class CategoricalMetrics(Aggregator):
    def prepare(self, array):
        return {
            "value_counts": ValueCounts()(array),
            "mean_str_len": MeanStrLength()(array),
            "common_stats": CommonStats()(array),
        }


def is_categorical(col) -> bool:
    return col.dtype == object


class DataOverviewReport(Report):
    def __init__(self, con_df=None, cat_df=None):
        self.con_df = con_df
        self.cat_df = cat_df

    def visualize(self, name="data") -> FacetsOverview:
        return visualize(self.con_df, self.cat_df, name=name)


def column_select(df, col_fn):
    return [col for col in df.columns if col_fn(df[col])]


def data_overview_report(data, groupby=None) -> DataOverviewReport:
    continuous_agg = Aggregator(
        ContinuousMetrics(),
        per_column=ft.partial(column_select, col_fn=is_continuous),
        groupby=groupby,
    )
    categorical_agg = Aggregator(
        CategoricalMetrics(),
        per_column=ft.partial(column_select, col_fn=is_categorical),
        groupby=groupby,
    )

    con_df = aggregate(data, continuous_agg, to_frame=True)
    cat_df = aggregate(data, categorical_agg, to_frame=True)

    return DataOverviewReport(con_df, cat_df)
