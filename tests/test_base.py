import collections
import typing

import numpy as np
import pandas as pd
import pytest
from numpy import testing

from hamilton import base


def test_numpymatrixresult_int():
    """Tests the happy path of build_result of numpymatrixresult"""
    outputs = collections.OrderedDict(
        a=np.array([1, 7, 3, 7, 3, 6, 4, 9, 5, 0]), b=np.zeros(10), c=1
    )
    expected = np.array([[1, 7, 3, 7, 3, 6, 4, 9, 5, 0], np.zeros(10), np.ones(10)]).T
    actual = base.NumpyMatrixResult().build_result(**outputs)
    testing.assert_array_equal(actual, expected)


def test_numpymatrixresult_raise_length_mismatch():
    """Test raising an error build_result of numpymatrixresult"""
    outputs = collections.OrderedDict(
        a=np.array([1, 7, 3, 7, 3, 6, 4, 9, 5, 0]), b=np.array([1, 2, 3, 4, 5]), c=1
    )
    with pytest.raises(ValueError):
        base.NumpyMatrixResult().build_result(**outputs)


def test_SimplePythonGraphAdapter():
    """Tests that it delegates as intended"""

    class Foo(base.ResultMixin):
        @staticmethod
        def build_result(**outputs: typing.Dict[str, typing.Any]) -> typing.Any:
            outputs.update({"esoteric": "function"})
            return outputs

    spga = base.SimplePythonGraphAdapter(Foo())
    cols = {"a": "b"}
    expected = {"a": "b", "esoteric": "function"}
    actual = spga.build_result(**cols)
    assert actual == expected


T = typing.TypeVar("T")


@pytest.mark.parametrize(
    "node_type,input_value",
    [
        (typing.Any, None),
        (pd.Series, pd.Series([1, 2, 3])),
        (T, None),
        (typing.List, []),
        (typing.Dict, {}),
        (dict, {}),
        (list, []),
        (int, 1),
        (float, 1.0),
        (str, "abc"),
        (typing.Union[int, pd.Series], pd.Series([1, 2, 3])),
        (typing.Union[int, pd.Series], 1),
    ],
    ids=[
        "test-any",
        "test-subclass",
        "test-typevar",
        "test-generic-list",
        "test-generic-dict",
        "test-type-match-dict",
        "test-type-match-list",
        "test-type-match-int",
        "test-type-match-float",
        "test-type-match-str",
        "test-union-match-series",
        "test-union-match-int",
    ],
)
def test_SimplePythonDataFrameGraphAdapter_check_input_type_match(node_type, input_value):
    """Tests check_input_type of SimplePythonDataFrameGraphAdapter"""
    adapter = base.SimplePythonDataFrameGraphAdapter()
    actual = adapter.check_input_type(node_type, input_value)
    assert actual is True


@pytest.mark.parametrize(
    "node_type,input_value",
    [
        (pd.DataFrame, pd.Series([1, 2, 3])),
        (typing.List, {}),
        (typing.Dict, []),
        (dict, []),
        (list, {}),
        (int, 1.0),
        (float, 1),
        (str, 0),
        (typing.Union[int, pd.Series], pd.DataFrame({"a": [1, 2, 3]})),
        (typing.Union[int, pd.Series], 1.0),
    ],
    ids=[
        "test-subclass",
        "test-generic-list",
        "test-generic-dict",
        "test-type-match-dict",
        "test-type-match-list",
        "test-type-match-int",
        "test-type-match-float",
        "test-type-match-str",
        "test-union-mismatch-dataframe",
        "test-union-mismatch-float",
    ],
)
def test_SimplePythonDataFrameGraphAdapter_check_input_type_mismatch(node_type, input_value):
    """Tests check_input_type of SimplePythonDataFrameGraphAdapter"""
    adapter = base.SimplePythonDataFrameGraphAdapter()
    actual = adapter.check_input_type(node_type, input_value)
    assert actual is False


@pytest.mark.parametrize(
    "outputs,expected_result",
    [
        ({"a": 1}, pd.DataFrame([{"a": 1}])),
        ({"a": pd.Series([1, 2, 3])}, pd.DataFrame({"a": pd.Series([1, 2, 3])})),
        (
            {"a": pd.DataFrame({"a": [1, 2, 3], "b": [11, 12, 13]})},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13])}),
        ),
        ({"a": 1, "bar": 2}, pd.DataFrame([{"a": 1, "bar": 2}])),
        (
            {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13])},
            pd.DataFrame({"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13])}),
        ),
        (
            {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13]), "c": 1},
            pd.DataFrame(
                {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13]), "c": pd.Series([1, 1, 1])}
            ),
        ),
        (
            {
                "a": pd.Series([1, 2, 3]),
                "b": pd.Series([11, 12, 13]),
                "c": pd.Series([11, 12, 13]).index,
            },
            pd.DataFrame(
                {"a": pd.Series([1, 2, 3]), "b": pd.Series([11, 12, 13]), "c": pd.Series([0, 1, 2])}
            ),
        ),
    ],
    ids=[
        "test-single-scalar",
        "test-single-series",
        "test-single-dataframe",
        "test-multiple-scalars",
        "test-multiple-series",
        "test-multiple-series-with-scalar",
        "test-multiple-series-with-index",
    ],
)
def test_PandasDataFrameResult_build_result(outputs, expected_result):
    """Tests the happy case of PandasDataFrameResult.build_result()"""
    pdfr = base.PandasDataFrameResult()
    actual = pdfr.build_result(**outputs)
    pd.testing.assert_frame_equal(actual, expected_result)


@pytest.mark.parametrize(
    "outputs",
    [
        (
            {
                "a": pd.DataFrame({"a": [1, 2, 3], "b": [11, 12, 13]}),
                "b": pd.DataFrame({"c": [1, 3, 5], "d": [14, 15, 16]}),
            }
        ),
        (
            {
                "a": pd.Series([1, 2, 3]),
                "b": pd.Series([11, 12, 13]),
                "c": pd.DataFrame({"d": [0, 0, 0]}),
            }
        ),
    ],
    ids=[
        "test-multiple-dataframes",
        "test-multiple-series-with-dataframe",
    ],
)
def test_PandasDataFrameResult_build_result_errors(outputs):
    """Tests the error case of PandasDataFrameResult.build_result()"""
    pdfr = base.PandasDataFrameResult()
    with pytest.raises(ValueError):
        pdfr.build_result(**outputs)


@pytest.mark.parametrize(
    "outputs,expected_result",
    [
        ({"a": pd.Series([1, 2, 3])}, ({"RangeIndex:::int64": ["a"]}, {}, {})),
        (
            {"a": pd.Series([1, 2, 3]), "b": pd.Series([3, 4, 5])},
            ({"RangeIndex:::int64": ["a", "b"]}, {}, {}),
        ),
        (
            {
                "b": pd.Series(
                    [3, 4, 5], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                )
            },
            (
                {"DatetimeIndex:::datetime64[ns]": ["b"]},
                {"DatetimeIndex:::datetime64[ns]": ["b"]},
                {},
            ),
        ),
        ({"c": 1}, ({"no-index": ["c"]}, {}, {"no-index": ["c"]})),
        (
            {
                "a": pd.Series([1, 2, 3]),
                "b": 1,
                "c": pd.Series(
                    [3, 4, 5], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
            },
            (
                {
                    "DatetimeIndex:::datetime64[ns]": ["c"],
                    "RangeIndex:::int64": ["a"],
                    "no-index": ["b"],
                },
                {"DatetimeIndex:::datetime64[ns]": ["c"]},
                {"no-index": ["b"]},
            ),
        ),
        ({"a": pd.DataFrame({"a": [1, 2, 3]})}, ({"RangeIndex:::int64": ["a"]}, {}, {})),
        ({"a": pd.Series([1, 2, 3]).index}, ({"Int64Index:::int64": ["a"]}, {}, {})),
    ],
    ids=[
        "int-index",
        "int-index-double",
        "ts-index",
        "no-index",
        "multiple-different-indexes",
        "df-index",
        "index-object",
    ],
)
def test_PandasDataFrameResult_pandas_index_types(outputs, expected_result):
    """Tests exercising the function to return pandas index types from outputs"""
    pdfr = base.PandasDataFrameResult()
    actual = pdfr.pandas_index_types(outputs)
    assert dict(actual[0]) == expected_result[0]
    assert dict(actual[1]) == expected_result[1]
    assert dict(actual[2]) == expected_result[2]


@pytest.mark.parametrize(
    "all_index_types,time_indexes,no_indexes,expected_result",
    [
        ({"foo": ["a", "b", "c"]}, {}, {}, True),
        ({"int-index": ["a"], "no-index": ["b"]}, {}, {"no-index": ["b"]}, True),
        ({"ts-1": ["a"], "ts-2": ["b"]}, {"ts-1": ["a"], "ts-2": ["b"]}, {}, False),
        ({"float-index": ["a"], "int-index": ["b"]}, {}, {}, False),
        ({"no-index": ["a", "b"]}, {}, {"no-index": ["a", "b"]}, False),
    ],
    ids=[
        "all-the-same",  # True
        "single-index-with-no-index",  # True
        "multiple-ts",  # False
        "multiple-indexes-not-ts",  # False
        "no-indexes-at-all",  # False4
    ],
)
def test_PandasDataFrameResult_check_pandas_index_types_match(
    all_index_types, time_indexes, no_indexes, expected_result
):
    """Tests exercising the function to determine whether pandas index types match"""
    # setup to test conditional if statement on logger level
    import logging

    logger = logging.getLogger("hamilton.base")  # get logger of base module.
    logger.setLevel(logging.DEBUG)
    pdfr = base.PandasDataFrameResult()
    actual = pdfr.check_pandas_index_types_match(all_index_types, time_indexes, no_indexes)
    assert actual == expected_result


@pytest.mark.parametrize(
    "outputs,expected_result",
    [
        ({"a": pd.Series([1, 2, 3])}, pd.DataFrame({"a": pd.Series([1, 2, 3])})),
        (
            {
                "a": pd.Series(
                    [1, 2, 3], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
                "b": pd.Series(
                    [3, 4, 5], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
            },
            pd.DataFrame(
                {
                    "a": pd.Series(
                        [1, 2, 3],
                        index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS"),
                    ),
                    "b": pd.Series(
                        [3, 4, 5],
                        index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS"),
                    ),
                }
            ),
        ),
        (
            {
                "a": pd.Series(
                    [1, 2, 3], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
                "b": 4,
            },
            pd.DataFrame(
                {
                    "a": pd.Series(
                        [1, 2, 3],
                        index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS"),
                    ),
                    "b": 4,
                }
            ),
        ),
    ],
    ids=[
        "test-same-index-simple",
        "test-same-index-ts",
        "test-index-with-scalar",
    ],
)
def test_StrictIndexTypePandasDataFrameResult_build_result(outputs, expected_result):
    """Tests the happy case of StrictIndexTypePandasDataFrameResult.build_result()"""
    sitpdfr = base.StrictIndexTypePandasDataFrameResult()
    actual = sitpdfr.build_result(**outputs)
    pd.testing.assert_frame_equal(actual, expected_result)


@pytest.mark.parametrize(
    "outputs",
    [
        (
            {
                "a": pd.Series([1, 2, 3], index=[0, 1, 2]),
                "b": pd.Series([1, 2, 3], index=[0.0, 1.0, 2.0]),
            }
        ),
        (
            {
                "series1": pd.Series(
                    [1, 2, 3], index=pd.DatetimeIndex(["2022-01", "2022-02", "2022-03"], freq="MS")
                ),
                "series2": pd.Series(
                    [4, 5, 6],
                    index=pd.PeriodIndex(year=[2022, 2022, 2022], month=[1, 2, 3], freq="M"),
                ),
                "series3": pd.Series(
                    [4, 5, 6],
                    index=pd.PeriodIndex(
                        year=[2022, 2022, 2022], month=[1, 1, 1], day=[3, 4, 5], freq="B"
                    ),
                ),
                "series4": pd.Series(
                    [4, 5, 6],
                    index=pd.PeriodIndex(
                        year=[2022, 2022, 2022], month=[1, 1, 1], day=[4, 11, 18], freq="W"
                    ),
                ),
            }
        ),
    ],
    ids=[
        "test-int-float",
        "test-different-ts-indexes",
    ],
)
def test_StrictIndexTypePandasDataFrameResult_build_result_errors(outputs):
    """Tests the error case of StrictIndexTypePandasDataFrameResult.build_result()"""
    sitpdfr = base.StrictIndexTypePandasDataFrameResult()
    with pytest.raises(ValueError):
        sitpdfr.build_result(**outputs)
