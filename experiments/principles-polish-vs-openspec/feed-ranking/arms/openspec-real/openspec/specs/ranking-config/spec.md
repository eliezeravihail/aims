# ranking-config Specification

## Purpose

Lets an operator set the per-deployment weight of each ranking signal in a configuration file and change it
without a code change, while the service only ever scores with a valid, consistent set of weights.

## Requirements

### Requirement: Weights come from a deployment configuration file
The service SHALL read signal weights from a JSON configuration file whose location the deployment supplies. The
file SHALL contain a `weights` object with exactly one numeric entry for each signal: `recency`, `affinity` and
`popularity`. Weights SHALL NOT be hard-coded, and there SHALL be no built-in default weights.

#### Scenario: Weights loaded from file
- **WHEN** the configuration file contains `{"weights": {"recency": 0.5, "affinity": 0.3, "popularity": 0.2}}`
- **THEN** requests are scored with recency 0.5, affinity 0.3 and popularity 0.2

#### Scenario: No configuration supplied
- **WHEN** the service is started without a configuration file location, or the file does not exist
- **THEN** the service refuses to start and reports that configuration is required

### Requirement: Weight validation
The service SHALL accept a configuration only when every weight is a finite real number ≥ 0, at least one weight
is > 0, all three signals are present, and no unknown signal name appears. Weights SHALL NOT have to sum to 1. The
service SHALL use them as given and SHALL NOT normalize them. Any violation SHALL be reported with an error that
names the offending key.

#### Scenario: Negative weight rejected
- **WHEN** the configuration sets `affinity` to -0.1
- **THEN** the configuration is rejected with an error naming `affinity`

#### Scenario: Unknown signal rejected
- **WHEN** the configuration contains a `freshness` weight
- **THEN** the configuration is rejected with an error naming `freshness`

#### Scenario: Missing signal rejected
- **WHEN** the configuration omits `popularity`
- **THEN** the configuration is rejected with an error naming `popularity`

#### Scenario: All-zero weights rejected
- **WHEN** every weight is 0
- **THEN** the configuration is rejected

#### Scenario: Weights not summing to one accepted
- **WHEN** the weights are recency 5, affinity 3, popularity 2
- **THEN** the configuration is accepted and scores are the weighted sums with those exact values

### Requirement: Operator changes weights without a code change
An operator SHALL be able to change the weights by editing the configuration file and triggering a reload,
without modifying or redeploying code. A reload of a valid file SHALL take effect for every request that starts
after the reload completes.

#### Scenario: Reload applies new weights
- **WHEN** the operator changes `recency` from 0.5 to 0.1 in the file and triggers a reload
- **THEN** requests started after the reload are scored with recency 0.1

### Requirement: Invalid reload keeps last good weights
If a reload finds an invalid or unreadable configuration, the service SHALL keep scoring with the weights that
were last loaded successfully and SHALL report the reload failure to the caller that triggered it.

#### Scenario: Bad edit does not break ranking
- **WHEN** the operator saves a file with a negative weight and triggers a reload
- **THEN** the reload reports an error and subsequent requests keep using the previous valid weights

### Requirement: One weight set per request
Each rank request SHALL be scored entirely with a single weight set. A reload that happens while a request is
being processed SHALL NOT cause that request to mix old and new weights.

#### Scenario: Reload during a request
- **WHEN** a reload completes while a request is being scored
- **THEN** every candidate in that request is scored with the same weights, either all old or all new
