# Test_edisson_KMN

## On-line game Stone Scissors, Paper, Lizard, Spock

### Winner list:

|        | Stone |Scissors| Paper| Lizard| Spock |
|--------|-------|-------|-------|-------|-------|
|Stone   |0      |Stone  |  Paper| Stone |Spock  |
|Scissors|Stone  |0      |Scissors|Scissors|Spock|
|Paper   |Paper  |Scissors|0     |Lizard |Paper  |
|Lizard  |Stone  |Scissors|Lizard|0      |Lizard |
|Spock   |Spock  |Spock  |Paper  |Lizard |0      |

____
# Very important! To working with django channels You must to run Redis
## docker run -p 6379:6379 -d redis:5
