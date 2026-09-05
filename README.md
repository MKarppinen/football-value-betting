# Football Value Betting Model


# About the project
This project was made as a learning experience to enchance my mathematical skills and also coding. The conceptual development of the model, statistical reasoning, modelling decisions, and overall project direction were my own. AI tools were used as a development assistant, primarily for generating parts of the code, debugging, refactoring, and helping translate the modelling ideas into working Python implementations. 


I reviewed, tested, modified, and integrated the generated code myself, and the underlying modelling methodology and assumptions were independently understood and validated. I wil keep adding features and improving this constantly. For example I will be adding Kelly-criterion-based stake sizing, weighting for recent games and scanner for bookmaker odds. 

# Overview
This project is a Python-based football match prediction system designed to estimate the probabilities of home wins, draws, and away wins from historical match data.

The model combines team attack and defence strengths with home/away performance and opponent-strength adjustments to estimate expected goals. These expected goals are then used in a Poisson model, with a Dixon-Coles correction applied to improve the modelling of low-scoring outcomes that are particularly common in football.

A key focus of the project is reliable model evaluation. Predictions are evaluated using walk-forward backtesting, where each match is predicted using only information that would have been available before that match was played. This prevents future information from leaking into the training data and provides a more realistic estimate of how the model would perform in practice.

The model is evaluated using metrics such as Brier Score, Log Loss, and probability calibration. Model parameters, including home advantage, opponent adjustment, and Dixon-Coles correlation, are tested empirically using historical data.

# Features
Team strength modelling — Estimates team attacking and defensive strength from historical match results.

Opponent-strength adjustment — Adjusts team strength estimates based on the quality of the opponents faced.

Home/Away weighting — Uses separate home and away performance information, with a 60/40 weighting between venue-specific and overall performance.

Home advantage modelling — Applies an empirically tested home-advantage factor to account for the systematic advantage of playing at home.

Expected goals estimation — Estimates expected goals for both teams using their attacking and defensive strengths.

Poisson goal model — Converts expected goals into probabilities for individual scorelines.
   
Dixon-Coles correction — Adjusts the probabilities of common low-scoring results such as 0–0, 1–0, 0–1, and 1–1.

1X2 probability prediction — Aggregates scoreline probabilities into home win, draw, and away win probabilities.


## Model

The prediction model combines historical team performance with a Poisson goal model and a Dixon-Coles correction.

### 1. Team Strength

For each team, the model estimates attacking and defensive strength from previously played matches.

Home and away performance are treated separately. The current model uses a 60/40 weighting between venue-specific performance and overall performance.

Opponent strength is also taken into account, so performance against stronger teams has a different impact than performance against weaker teams.

### 2. Expected Goals

The estimated team strengths are combined to produce expected goals (xG) for both teams:


Home xG = (Home attack + Away defence) / 2
Away xG = (Away attack + Home defence) / 2


A home-advantage factor is applied to account for the systematic advantage of playing at home.

The current backtested home-advantage parameter is 1.14.

### 3. Poisson Model

Expected goals are converted into probabilities for individual scorelines using the Poisson distribution:


P(X = k) = e^(-λ) λ^k / k!


where `λ` represents the expected number of goals.

The model calculates probabilities for a range of possible scorelines and aggregates them into:

Home win probability
Draw probability
Away win probability

### 4. Dixon-Coles Correction

The independent Poisson model is adjusted using the Dixon-Coles method.

The correction specifically modifies the probability of common low-scoring outcomes:


0-0
1-0
0-1
1-1


The current Dixon-Coles parameter was selected through historical backtesting.

### 5. Probability Normalization

Because the scoreline matrix is truncated at a maximum number of goals, the resulting probabilities are normalized so that:


P(Home) + P(Draw) + P(Away) = 1


### Current Model Parameters

The current baseline uses:

| Parameter           | Value |
| ------------------- | ----: |
| Home/Away weighting | 60/40 |
| TeamStrength rho    |  0.50 |
| Home advantage      |  1.14 |
| Dixon-Coles rho     | -0.25 |
| Maximum goals       |    10 |

## Backtesting

The model is evaluated using walk-forward backtesting on historical Premier League matches.

For each match in chronological order, the model is trained using only matches that occurred before the target match. The target match is then predicted, after which its result becomes available for subsequent predictions.

This approach prevents future information from being used when making historical predictions and provides a more realistic estimate of out-of-sample model performance.

A minimum history of 5 previous matches is required before a prediction is generated.

## Backtest Results

The current baseline model was evaluated on 380 historical Premier League matches.

| Metric             | Result |
| ------------------ | -----: |
| Historical matches |    380 |
| Matches tested     |    360 |
| Matches skipped    |     20 |
| Brier Score        | 0.6191 |
| Log Loss           | 1.0316 |

### Outcome Calibration

| Outcome | Model Average | Actual Rate |
| ------- | ------------: | ----------: |
| Home    |         41.7% |       42.2% |
| Draw    |         27.7% |       27.5% |
| Away    |         30.6% |       30.3% |

The predicted outcome frequencies are close to the observed historical frequencies, indicating reasonable overall calibration.

Model parameters were also tested using historical walk-forward backtesting. The current baseline uses a home-advantage factor of 1.14, TeamStrength rho of 0.50, and Dixon-Coles rho of -0.25.

## Tech Stack

 Python - Core programming language
 SQLite — Local relational database for match and statistical data
Poisson distribution — Goal probability modelling
Dixon-Coles model — Low-scoring football outcome correction
Git — Version control
GitHub — Source code management and project hosting

## Usage

### 1. Install the project

Create a virtual environment and install the project:


py -m venv .venv
.venv\Scripts\activate
pip install -e .


### 2. Update match data

The project can retrieve and store football match data in the local SQLite database.

The database contains historical matches, results, team information, and match statistics used by the prediction model.

### 3. Run the backtest

To evaluate the model on historical data:

py -m vbet.main backtest


This runs a walk-forward backtest and reports the model's Brier Score, Log Loss, and calibration.

### 4. Predict upcoming matches

The model can use the stored historical data to estimate the probabilities of upcoming matches.

For each match, the model produces:


Home win probability
Draw probability
Away win probability
Home expected goals
Away expected goals


The three outcome probabilities always sum to approximately 100%.

For example:


Home team: Arsenal
Away team: Chelsea

Home win: 48.2%
Draw:     27.1%
Away win: 24.7%

Home xG: 1.62
Away xG: 1.08


The prediction is based on the information available in the database at the time of prediction, including team attacking and defensive strength, home/away performance, opponent adjustment, home advantage, and the Poisson/Dixon-Coles model.

# Arguments
use py -m vbet.main --help  
 for the commands 


