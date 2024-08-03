from sklearn.base import BaseEstimator
from ....metrics import RegressionScorer
from ..base_model import BasePredictModel, HyperparameterSearcher
from ....data import DataEmitter
from ....feature_selection import VotingSelectionReport
from ....display.print_utils import print_wrapped


class BaseR(BasePredictModel):
    """BaseR is a class that provides a training and evaluation framework that all
    TabularMagic regression classes inherit (i.e., all ___R classes are children 
    of BaseR). The primary purpose of BaseR is to automate the scoring and
    model selection processes.
    """

    def __init__(self):
        """Initializes a BaseR object."""
        self._hyperparam_searcher: HyperparameterSearcher = None
        self._estimator: BaseEstimator = None
        self._dataemitter = None
        self._dataemitters = None
        self._feature_selectors = None
        self._max_n_features = None
        self._name = "BaseR"
        self._train_scorer = None
        self._cv_scorer = None
        self._test_scorer = None
        self._feature_selection_report = None
        self._predictors = None

        # By default, the first column is NOT dropped. For LinearR,
        # the first column is dropped to avoid multicollinearity.
        self._dropfirst = False

    def specify_data(
        self,
        dataemitter: DataEmitter | None = None,
        dataemitters: list[DataEmitter] | None = None,
    ):
        """Specifies the DataEmitters for the model fitting process.

        Parameters
        ----------
        dataemitter : DataEmitter | None
            Default: None.
            DataEmitter that contains the data. If not None, re-specifies the
            DataEmitter for the model.

        dataemitters : list[DataEmitter] | None
            Default: None.
            If not None, re-specifies the DataEmitters for nested cross validation.
        """
        if dataemitter is not None:
            self._dataemitter = dataemitter
        if dataemitters is not None:
            self._dataemitters = dataemitters

    def fit(self, verbose: bool = False):
        """Fits and evaluates the model.

        The model fitting process is as follows:

        1. The train data is emitted. This means that the data is preprocessed based on 
        user specifications AND necessary automatic preprocessing steps. That is,
        the DataEmitter will automatically drop observations with missing
        entries and encode categorical variables IF NOT SPECIFIED BY USER.
        2. The hyperparameter search is performed. The best estimator is saved and
        evaluated on the train data.
        3. The test data is emitted. Preprocessing steps were previously
        fitted on the train data. The test data is transformed accordingly.
        4. The best estimator determined from the training step
        is evaluated on the test data.

        If cross validation is specified, fold-specific DataEmitters are generated.
        Steps 1-4 are repeated for each fold.

        The fitting process yields three sets of metrics:
        
        1. The training set metrics.
        2. The cross validation set metrics. *only if cross validation was specified*
            Note that the cross validation metrics are computed on the test set of
            each fold and are therefore a more robust estimate of model performance
            than the test set metrics.
        3. The test set metrics.

        Parameters
        ----------
        verbose : bool
            Default: False. If True, prints progress.
        """
        if self._dataemitter is None:
            raise RuntimeError("DataEmitter not specified.")

        y_scaler = self._dataemitter.y_scaler()

        if self._dataemitters is None and self._dataemitter is not None:
            X_train_df, y_train_series = self._dataemitter.emit_train_Xy()

            if self._feature_selectors is not None:
                self._feature_selection_report = VotingSelectionReport(
                    selectors=self._feature_selectors,
                    dataemitter=self._dataemitter,
                    max_n_features=self._max_n_features,
                    verbose=verbose,
                )
                self._predictors = self._feature_selection_report.top_features()
                X_train = self._feature_selection_report._emit_train_X().to_numpy()
            else:
                self._predictors = X_train_df.columns.tolist()
                X_train = X_train_df.to_numpy()

            y_train = y_train_series.to_numpy()

            self._hyperparam_searcher.fit(X_train, y_train, verbose=verbose)
            self._estimator = self._hyperparam_searcher._best_estimator
            y_pred = self._estimator.predict(X_train)
            if y_scaler is not None:
                y_pred = y_scaler.inverse_transform(y_pred)
                y_train = y_scaler.inverse_transform(y_train)
            self._train_scorer = RegressionScorer(
                y_pred=y_pred,
                y_true=y_train,
                n_predictors=X_train.shape[1],
                name=str(self),
            )

        elif self._dataemitters is not None and self._dataemitter is not None:
            y_preds = []
            y_trues = []
            for emitter in self._dataemitters:
                (
                    X_train_df,
                    y_train_series,
                    X_test_df,
                    y_test_series,
                ) = emitter.emit_train_test_Xy()
                y_train = y_train_series.to_numpy()
                y_test = y_test_series.to_numpy()

                if self._feature_selectors is not None:
                    fold_selector = VotingSelectionReport(
                        selectors=self._feature_selectors,
                        dataemitter=emitter,
                        max_n_features=self._max_n_features,
                        verbose=verbose,
                    )
                    X_train = fold_selector._emit_train_X().to_numpy()
                    X_test = fold_selector._emit_test_X().to_numpy()
                else:
                    X_train = X_train_df.to_numpy()
                    X_test = X_test_df.to_numpy()

                self._hyperparam_searcher.fit(X_train, y_train, verbose=verbose)
                fold_estimator = self._hyperparam_searcher._best_estimator

                y_pred = fold_estimator.predict(X_test)
                if y_scaler is not None:
                    y_pred = y_scaler.inverse_transform(y_pred)
                    y_test = y_scaler.inverse_transform(y_test)

                y_preds.append(y_pred)
                y_trues.append(y_test)

            self._cv_scorer = RegressionScorer(
                y_pred=y_preds,
                y_true=y_trues,
                n_predictors=X_train.shape[1],
                name=str(self),
            )

            # refit on all data
            X_train_df, y_train_series = self._dataemitter.emit_train_Xy()

            self._predictors = X_train_df.columns.tolist()

            y_train = y_train_series.to_numpy()

            if self._feature_selectors is not None:
                self._feature_selection_report = VotingSelectionReport(
                    selectors=self._feature_selectors,
                    dataemitter=self._dataemitter,
                    max_n_features=self._max_n_features,
                    verbose=verbose,
                )
                X_train = self._feature_selection_report._emit_train_X().to_numpy()
                self._predictors = self._feature_selection_report.top_features()
            else:
                self._predictors = X_train_df.columns.to_list()
                X_train = X_train_df.to_numpy()

            self._hyperparam_searcher.fit(X_train, y_train, verbose=verbose)
            self._estimator = self._hyperparam_searcher._best_estimator
            y_pred = self._estimator.predict(X_train)
            if y_scaler is not None:
                y_pred = y_scaler.inverse_transform(y_pred)
                y_train = y_scaler.inverse_transform(y_train)

            self._train_scorer = RegressionScorer(
                y_pred=y_pred,
                y_true=y_train,
                n_predictors=X_train.shape[1],
                name=str(self),
            )

        else:
            raise ValueError("DataEmitter or DataEmitters not specified.")

        X_test_df, y_test_series = self._dataemitter.emit_test_Xy()

        if self._feature_selectors is None:
            X_test = X_test_df.to_numpy()
        else:
            X_test = self._feature_selection_report._emit_test_X().to_numpy()

        y_test = y_test_series.to_numpy()

        y_pred = self._estimator.predict(X_test)
        if y_scaler is not None:
            y_pred = y_scaler.inverse_transform(y_pred)
            y_test = y_scaler.inverse_transform(y_test)

        self._test_scorer = RegressionScorer(
            y_pred=y_pred, y_true=y_test, n_predictors=X_test.shape[1], name=str(self)
        )

    def sklearn_estimator(self) -> BaseEstimator:
        """Returns the sklearn estimator object.

        Note that the sklearn estimator can be saved and used for future predictions.
        However, the input data must be preprocessed in the same way. If you intend
        to use the estimator for future predictions, it is recommended that you
        manually specify every preprocessing step, which will ensure that you
        have full control over how the data is being transformed for future
        reproducibility and predictions.

        It is not recommended to use TabularMagic for ML production.
        We recommend using TabularMagic to quickly identify promising models
        and then manually implementing and training
        the best model in a production environment.

        Returns
        -------
        BaseEstimator
        """
        return self._estimator

    def hyperparam_searcher(self) -> HyperparameterSearcher:
        """Returns the HyperparameterSearcher object.

        Returns
        -------
        HyperparameterSearcher
        """
        return self._hyperparam_searcher

    def _set_voting_selection_report(
        self, voting_selection_report: VotingSelectionReport
    ):
        """Adds a VotingSelectionReport object to the model. The VotingSelectionReport
        must have already been fitted to the data.

        Parameters
        ----------
        voting_selection_report : VotingSelectionReport
            The VotingSelectionReport object that has already been fitted to the data.
        """
        self._feature_selection_report = voting_selection_report

    def feature_selection_report(self) -> VotingSelectionReport | None:
        """Returns the VotingSelectionReport object.

        Returns
        -------
        VotingSelectionReport | None
            None if the VotingSelectionReport object has not been set (e.g. no
            feature selection was conducted).
        """
        if self._feature_selection_report is None:
            print_wrapped(
                f"No feature selection report available for {self._name}.",
                type="WARNING",
            )
        return self._feature_selection_report

    def is_cross_validated(self) -> bool:
        """Returns True if the cross validation metrics are available.

        Returns
        -------
        bool
            True if cross validation metrics are available.
        """
        return self._dataemitters is not None

    def predictors(self) -> list[str] | None:
        """Returns a list predictor variable names. A warning is printed if the model
        has not been fitted, and None is returned.

        Returns
        -------
        list[str] | None
            A list of predictor variable names used in the final model,
            after feature selection and data transformation.
        """
        if self._predictors is None:
            print_wrapped(
                "No predictors available. The model has not been fitted.",
                type="WARNING",
            )
        return self._predictors

    def __str__(self):
        return self._name