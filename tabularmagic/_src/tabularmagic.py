import pandas as pd
from typing import Iterable, Literal
from sklearn.model_selection import train_test_split

from .ml.discriminative.regression.base_regression import BaseRegression
from .ml.discriminative.classification.\
    base_classification import BaseClassification
from .linear.regression.linear_regression import OrdinaryLeastSquares
from .linear.regression.lm_rlike_util import parse_and_transform_rlike
from .interactive import (MLRegressionReport, 
    ComprehensiveEDA, RegressionVotingSelectionReport, 
    LinearRegressionReport, MLClassificationReport)
from .util.console import print_wrapped
from .feature_selection import BaseFeatureSelectorR
from .data.datahandler import DataHandler



class TabularMagic:
    """TabularMagic: Automatic statistical and machine learning analysis of 
    DataFrames in tabular form. 
    """

    def __init__(self, df: pd.DataFrame, df_test: pd.DataFrame = None, 
            test_size: float = 0.0, split_seed: int = 42, 
            verbose: bool = True, name: str = 'TabularMagic'):
        """Initializes a TabularMagic object.
        
        Note: DataFrame indices are not guaranteed to be correctly preserved. 

        Parameters
        ----------
        - df : pd.DataFrame ~ (sample_size, n_variables).
        - df_test : pd.DataFrame ~ (test_sample_size, n_variables).
            Default: None. If not None, then treats df as the train DataFrame.
        - test_size : float. 
            Default: 0. Proportion of the DataFrame to withhold for 
            testing. If test_size = 0, then the train DataFrame and the 
            test DataFrame will both be the same as the input df. 
            If df_test is provided, then test_size is ignored. 
        - split_seed : int.
            Default: 42. Used only for the train test split. 
            If df_test is provided, then split_seed is ignored. 
        - verbose : bool. 
            Default: False. If True, prints helpful update messages for certain 
                TabularMagic function calls.
        - name : str. 
            Identifier for object. 
        """

        self._verbose = verbose


        if df_test is not None:
            self._datahandler = DataHandler(
                df_train=df,
                df_test=df_test,
                verbose=self._verbose,
                name=name
            )

        else:
            if test_size > 0:
                temp_train, temp_test = train_test_split(df, 
                    test_size=test_size, shuffle=True, 
                    random_state=split_seed)
                temp_train_df = pd.DataFrame(temp_train, columns=df.columns)
                temp_test_df = pd.DataFrame(temp_test, columns=df.columns)
            else:
                if self._verbose:
                    print_wrapped(
                        'No test DataFrame provided. The test DataFrame ' +\
                        'will be treated as a train DataFrame copy.',
                        type='WARNING'
                    )
                temp_train_df = df
                temp_test_df = df
            self._datahandler = DataHandler(
                df_train=temp_train_df,
                df_test=temp_test_df, 
                verbose=self._verbose,
                name=name
            )
        self._name = name

        if self._verbose:
            shapes_dict = self._datahandler._shapes_str_formatted()
            print_wrapped(
                f'Initialization complete. ' +\
                'Shapes of train, test DataFrames: ' + \
                f'{shapes_dict["train"]}, ' + \
                f'{shapes_dict["test"]}.',
                type='UPDATE'
            )


    # --------------------------------------------------------------------------
    # EDA + FEATURE SELECTION + REGRESSION ANALYSIS
    # --------------------------------------------------------------------------
    def eda(self, 
            dataset: Literal['train', 'test', 'all'] = 'train') ->\
                ComprehensiveEDA:
        """Constructs a ComprehensiveEDA object for the working train 
        DataFrame, the working test DataFrame, or both DataFrames combined.

        Parameters
        ----------
        - dataset: Literal['train', 'test', 'all'].
            Default: 'train'.

        Returns
        -------
        - ComprehensiveEDA
        """
        if dataset == 'train':
            return ComprehensiveEDA(self._datahandler.df_train())
        elif dataset == 'test':
            return ComprehensiveEDA(self._datahandler.df_test())
        elif dataset == 'all':
            return ComprehensiveEDA(self._datahandler.df_all())
        else:
            raise ValueError(f'Invalid input: dataset = {dataset}.')


    def feature_selection(self, 
                          selectors: Iterable[BaseFeatureSelectorR], 
                          y_var: str, 
                          X_vars: list[str] = None, 
                          n_target_features: int = 10, 
                          update_working_dfs: bool = False):
        """Supervised feature selection via methods voting based on
        training dataset. 
        Also returns a RegressionVotingSelectionReport object. 
        Can automatically update the working train and working test
        datasets so that only the selected features remain if 
        update_working_dfs is True.
        
        Parameters
        ----------
        - selectors : Iterable[BaseSelector].
            Each BaseSelector decides on the top n_target_features.
        - y_var : str.
            The variable to be predicted. 
        - X_vars : list[str].
            A list of features from which n_target_features are to be selected.
            If None, all continuous variables except y_var will be used. 
        - n_target_features : int. 
            Number of desired features, < len(X_vars). Default 10. 
        - update_working_dfs : bool.
            Default: False.

        Returns
        -------
        - RegressionVotingSelectionReport
        """
        if X_vars is None:
            X_vars = self._datahandler.continuous_vars(True)
        report = RegressionVotingSelectionReport(
            selectors=selectors,
            datahandler=self._datahandler.copy(y_var, X_vars),
            n_target_features=n_target_features, 
            verbose=self._verbose
        )
        if update_working_dfs:
            var_subset = report._top_features + [y_var]
            self._datahandler.select_vars(var_subset)
        return report




    def lm(self, y_var: str = None, X_vars: list[str] = None, 
           formula: str = None) ->\
                LinearRegressionReport:
        """Conducts a simple OLS regression analysis exercise. 
        If formula is provided, performs regression with OLS via formula. 
        Examples with missing data will be dropped. 

        Parameters
        ----------
        - y_var : str. 
        - X_vars : list[str]. 
            If None, all variables except y_var will be used as predictors.
        - formula : str.
            If not None, uses formula to specify the regression 
            (overrides y_var and X_vars).
            
        Returns
        -------
        - report : LinearRegressionReport
        """
        if formula is None and y_var is None:
            raise ValueError('y_var must be specified if formula is None.')

        elif formula is None:
            if X_vars is None:
                X_vars = self._datahandler.vars(ignore_yvar=False)
                X_vars.remove(y_var)
            return LinearRegressionReport(
                OrdinaryLeastSquares(),
                self._datahandler.copy(y_var, X_vars),
            )
        
        else:
            try:
                y_series_train, y_scaler, X_df_train =\
                    parse_and_transform_rlike(formula, 
                                              self._datahandler.df_train())
                y_series_test, _, X_df_test =\
                    parse_and_transform_rlike(formula,
                                              self._datahandler.df_test())
            except:
                raise ValueError(f'Invalid formula: {formula}')

            # ensure missing values are dropped
            y_X_df_combined_train = pd.DataFrame(
                y_series_train).join(X_df_train)
            y_X_df_combined_test = pd.DataFrame(
                y_series_test).join(X_df_test)
            y_X_df_combined_train.dropna(inplace=True)
            y_X_df_combined_test.dropna(inplace=True)
            y_X_df_combined_train, y_X_df_combined_test =\
                self._datahandler._force_train_test_var_agreement(
                    y_X_df_combined_train,
                    y_X_df_combined_test)
            
            X_vars = y_X_df_combined_train.columns.to_list()
            y_var = y_series_train.name
            X_vars.remove(y_var)
            
            datahandler = DataHandler(
                y_X_df_combined_train, 
                y_X_df_combined_test, 
                verbose=False)
            datahandler._continuous_var_to_scaler[y_var] = y_scaler

            return LinearRegressionReport(
                OrdinaryLeastSquares(), 
                datahandler.copy(y_var, X_vars),
            )





    # --------------------------------------------------------------------------
    # MACHINE LEARNING
    # --------------------------------------------------------------------------

    def ml_regression(self, 
                      models: Iterable[BaseRegression], 
                      y_var: str, 
                      X_vars: list[str] = None,
                      outer_cv: int = None,
                      outer_cv_seed: int = 42) -> MLRegressionReport:
        """Conducts a comprehensive regression benchmarking exercise. 
        Examples with missing data will be dropped. 

        Parameters
        ----------
        - models : Iterable[BaseRegression]. 
            Testing performance of all models will be evaluated. 
        - y_var : str. 
        - X_vars : list[str]. 
            If None, uses all variables except y_var as predictors.
        - outer_cv : int.
            If not None, reports training scores via nested k-fold CV.
        - outer_cv_seed : int.
            The random seed for the outer cross validation loop.
        
        Returns
        -------
        - report : MLRegressionReport
        """
        if X_vars is None:
            X_vars = self._datahandler.vars(ignore_yvar=False)
            X_vars.remove(y_var)

        return MLRegressionReport(
            models=models,
            datahandler=self._datahandler.copy(y_var, X_vars),
            outer_cv=outer_cv,
            outer_cv_seed=outer_cv_seed,
            verbose=self._verbose
        )


    def ml_classification(self, 
                          models: Iterable[BaseClassification], 
                          y_var: str, 
                          X_vars: list[str] = None, 
                          outer_cv: int = None,
                          outer_cv_seed: int = 42) -> MLClassificationReport:
        """Conducts a comprehensive classification benchmarking exercise.
        Examples with missing data will be dropped. 
        
        Parameters
        ----------
        - models : Iterable[BaseClassification].
            Testing performance of all models will be evaluated.
        - y_var : str.
        - X_vars : list[str].
            If None, uses all variables except y_var as predictors.
        - outer_cv : int.
            If not None, reports training scores via nested k-fold CV.
        - outer_cv_seed : int.
            The random seed for the outer cross validation loop.

        Returns
        -------
        - report MLClassificationReport
        """

        if X_vars is None:
            X_vars = self._datahandler.vars(ignore_yvar=False)
            X_vars.remove(y_var)
        
        return MLClassificationReport(
            models=models,
            datahandler=self._datahandler.copy(y_var, X_vars),
            outer_cv=outer_cv,
            outer_cv_seed=outer_cv_seed,
            verbose=self._verbose
        )



    # --------------------------------------------------------------------------
    # GETTERS
    # --------------------------------------------------------------------------
    def datahandler(self) -> DataHandler:
        """Returns the DataHandler."""
        return self._datahandler


    def __len__(self):
        """Returns the number of examples in working train DataFrame."""
        return len(self._datahandler)
            

    def __str__(self):
        """Returns metadata in string form."""
        return self._datahandler.__str__()


    def _repr_pretty_(self, p, cycle):
        p.text(str(self))


        